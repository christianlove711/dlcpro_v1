from __future__ import annotations

import ipaddress
import socket
import threading
import time
from collections.abc import Callable

import numpy as np
from dataclasses import dataclass

from .daq_protocol_v2 import (
    CONFIG_CHANNEL_SWAP, CONFIG_TEST_SHIFT, CONTROL_PORT, Command,
    DATA_PORT, PlCommand, RATE_TO_SELECTOR, ControlResponse,
    DaqdContinuityTracker, pack_pldq, parse_data_packet, parse_status_packet,
)


class ControlClient:
    """Synchronous PLDQ controller. The FPGA always replies to UDP/5000.

    The pure-PL IPv4 core does not implement ARP.  Send control requests to
    the fixed /24 subnet broadcast address so Windows does not have to resolve
    the board's unicast MAC address first.  Status replies still carry the
    configured board IP and are filtered below.
    """
    def __init__(self, board_ip: str, timeout: float = 1.0, *, adc_model: int = 1):
        self.board_ip = board_ip
        self.control_ip = str(
            ipaddress.ip_network(f"{board_ip}/24", strict=False).broadcast_address
        )
        self.timeout = timeout
        self.adc_model = int(adc_model)
        self._transaction = 0
        self._lock = threading.Lock()

    def _send_only(
        self, command: PlCommand, arg0: int = 0, arg1: int = 0,
    ) -> int:
        """Submit a mutating PLDQ command without depending on its immediate ACK.

        The PL command parser and acquisition manager are in different clock
        domains.  The command value is stable, but an individual status-toggle
        acknowledgement can be lost.  Mutations are therefore spaced and
        verified by a final GET_STATUS transaction.
        """
        self._transaction = (self._transaction + 1) & 0xFFFFFFFF
        transaction = self._transaction
        packet = pack_pldq(command, transaction, arg0, arg1)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", CONTROL_PORT))
            sock.sendto(packet, (self.control_ip, CONTROL_PORT))
        return transaction

    def _mutate_then_status(
        self, commands: tuple[tuple[PlCommand, int, int], ...],
    ) -> ControlResponse:
        for command, arg0, arg1 in commands:
            self._send_only(command, arg0, arg1)
            # Far longer than either 125 MHz -> 100 MHz CDC latency, while
            # still imperceptible to the operator.
            time.sleep(0.02)
        return self._exchange(PlCommand.GET_STATUS)

    def _exchange(
        self, command: PlCommand, arg0: int = 0, arg1: int = 0,
        *, attempts: int = 2,
    ) -> ControlResponse:
        self._transaction = (self._transaction + 1) & 0xFFFFFFFF
        transaction = self._transaction
        packet = pack_pldq(command, transaction, arg0, arg1)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", CONTROL_PORT))
            for _ in range(max(1, int(attempts))):
                sock.sendto(packet, (self.control_ip, CONTROL_PORT))
                deadline = time.monotonic() + self.timeout
                while time.monotonic() < deadline:
                    sock.settimeout(max(0.001, deadline - time.monotonic()))
                    try:
                        data, address = sock.recvfrom(512)
                    except socket.timeout:
                        break
                    if address[0] != self.board_ip or address[1] != CONTROL_PORT:
                        continue
                    # UDP/5000 can contain a delayed, malformed or unrelated
                    # datagram when acquisition/monitoring is changing state.
                    # Only a valid DAQS packet with this transaction completes
                    # the request; everything else must be ignored.
                    try:
                        response = parse_status_packet(data)
                    except ValueError:
                        continue
                    if response.request_id == transaction:
                        return response
        raise TimeoutError(f"PLDQ {command.name} timed out")

    def request(self, command: Command, **kwargs) -> ControlResponse:
        with self._lock:
            if command in (Command.DISCOVER, Command.GET_INFO):
                return self._exchange(PlCommand.DISCOVER)
            if command == Command.STATUS:
                return self._exchange(PlCommand.GET_STATUS)
            if command == Command.STOP:
                return self._mutate_then_status(
                    ((PlCommand.ACQ_STOP, 0, 0),)
                )
            if command == Command.CONFIG:
                rate = int(kwargs.get("sample_rate_hz", 5_000_000))
                if rate not in RATE_TO_SELECTOR:
                    raise ValueError(f"unsupported PL sample rate {rate}")
                flags = int(kwargs.get("flags", 0))
                test_mode = (flags >> CONFIG_TEST_SHIFT) & 0x7
                channel_swap = 1 if flags & CONFIG_CHANNEL_SWAP else 0
                jumbo = 1 if kwargs.get("jumbo_enable", False) else 0
                return self._mutate_then_status((
                    (PlCommand.SELECT_ADC, self.adc_model, channel_swap),
                    (PlCommand.CONFIG_RATE, RATE_TO_SELECTOR[rate], jumbo),
                    (PlCommand.SET_ADC_TEST, test_mode, 0),
                ))
            if command == Command.START:
                monitor_enable = bool(kwargs.get("monitor_enable", True))
                monitor_command = (
                    PlCommand.MONITOR_START if monitor_enable
                    else PlCommand.MONITOR_STOP
                )
                return self._mutate_then_status((
                    (PlCommand.ACQ_START, 0, 0),
                    (monitor_command, 0, 0),
                ))
        raise ValueError(f"unsupported GUI command {command}")


@dataclass(frozen=True)
class RawHistoryFrame:
    """Absolute 1 ms min/max bins used by control algorithms, in ADC codes."""

    bin_indices: np.ndarray
    minimum_a: np.ndarray
    maximum_a: np.ndarray
    minimum_b: np.ndarray
    maximum_b: np.ndarray
    valid: np.ndarray
    sample_rate_hz: int
    bin_seconds: float


class DualSampleRingBuffer:
    """Thread-safe two-channel preview ring indexed in received sample pairs."""
    HISTORY_BIN_SECONDS = 0.001
    # Long scope timebases use compact 1 ms min/max bins, so extending the
    # visible history to 100 s costs little memory and supports 10 s/div.
    HISTORY_SECONDS = 100.0

    def __init__(self, capacity: int = 10_000_000):
        self.capacity = int(capacity)
        self._a = np.zeros(self.capacity, dtype=np.int16)
        self._b = np.zeros(self.capacity, dtype=np.int16)
        self._valid = np.zeros(self.capacity, dtype=np.bool_)
        self._write = 0
        self._count = 0
        self._total_written = 0
        self._expected_raw_pair: int | None = None
        self._sample_rate_hz = 0
        self._stride = 1
        # Long timebases use one min/max bin per millisecond instead of
        # repeatedly copying millions of raw samples on every paint tick.
        self._history_capacity = int(
            self.HISTORY_SECONDS / self.HISTORY_BIN_SECONDS
        )
        self._history_min_a = np.zeros(self._history_capacity, np.int16)
        self._history_max_a = np.zeros(self._history_capacity, np.int16)
        self._history_min_b = np.zeros(self._history_capacity, np.int16)
        self._history_max_b = np.zeros(self._history_capacity, np.int16)
        self._history_valid = np.zeros(self._history_capacity, bool)
        self._history_write = 0
        self._history_count = 0
        self._history_bin_pairs = 0
        self._history_current_index: int | None = None
        self._history_current = None
        self._lock = threading.Lock()

    @property
    def effective_rate_hz(self) -> float:
        with self._lock:
            return self._sample_rate_hz / max(1, self._stride)

    def clear(self) -> None:
        with self._lock:
            self._write = self._count = 0
            self._total_written = 0
            self._expected_raw_pair = None
            self._valid.fill(False)
            self._reset_history()

    def _reset_history(self) -> None:
        self._history_write = 0
        self._history_count = 0
        self._history_current_index = None
        self._history_current = None
        self._history_valid.fill(False)

    def _commit_history_bin(self, valid: bool = True) -> None:
        if self._history_current is None:
            return
        min_a, max_a, min_b, max_b = self._history_current
        index = self._history_write
        self._history_min_a[index] = min_a
        self._history_max_a[index] = max_a
        self._history_min_b[index] = min_b
        self._history_max_b[index] = max_b
        self._history_valid[index] = bool(valid)
        self._history_write = (index + 1) % self._history_capacity
        self._history_count = min(
            self._history_capacity, self._history_count + 1
        )

    def _append_invalid_history_bins(self, count: int) -> None:
        count = min(max(0, int(count)), self._history_capacity)
        for _ in range(count):
            index = self._history_write
            self._history_min_a[index] = 0
            self._history_max_a[index] = 0
            self._history_min_b[index] = 0
            self._history_max_b[index] = 0
            self._history_valid[index] = False
            self._history_write = (index + 1) % self._history_capacity
            self._history_count = min(
                self._history_capacity, self._history_count + 1
            )

    def _update_history(self, first_raw_pair: int,
                        pairs: np.ndarray) -> None:
        if not pairs.size or self._history_bin_pairs <= 0:
            return
        raw_position = int(first_raw_pair)
        offset = 0
        stride = max(1, self._stride)
        while offset < len(pairs):
            bin_index = raw_position // self._history_bin_pairs
            bin_end = (bin_index + 1) * self._history_bin_pairs
            remaining_raw = max(1, bin_end - raw_position)
            take = min(
                len(pairs) - offset,
                max(1, (remaining_raw + stride - 1) // stride),
            )
            segment = pairs[offset:offset + take]
            segment_extrema = (
                int(np.min(segment[:, 0])),
                int(np.max(segment[:, 0])),
                int(np.min(segment[:, 1])),
                int(np.max(segment[:, 1])),
            )
            if self._history_current_index is None:
                self._history_current_index = bin_index
                self._history_current = segment_extrema
            elif bin_index > self._history_current_index:
                previous = self._history_current_index
                self._commit_history_bin(True)
                self._append_invalid_history_bins(bin_index - previous - 1)
                self._history_current_index = bin_index
                self._history_current = segment_extrema
            elif bin_index == self._history_current_index:
                current = self._history_current
                self._history_current = (
                    min(current[0], segment_extrema[0]),
                    max(current[1], segment_extrema[1]),
                    min(current[2], segment_extrema[2]),
                    max(current[3], segment_extrema[3]),
                )
            raw_position += take * stride
            offset += take

    def _write_values(self, a: np.ndarray, b: np.ndarray, valid: np.ndarray) -> None:
        count = min(int(a.size), self.capacity)
        if not count:
            return
        a, b, valid = a[-count:], b[-count:], valid[-count:]
        first = min(count, self.capacity - self._write)
        end = self._write + first
        self._a[self._write:end], self._b[self._write:end], self._valid[self._write:end] = a[:first], b[:first], valid[:first]
        if first < count:
            rest = count - first
            self._a[:rest], self._b[:rest], self._valid[:rest] = a[first:], b[first:], valid[first:]
        self._write = (self._write + count) % self.capacity
        self._count = min(self.capacity, self._count + count)
        self._total_written += count

    def append_packet(self, first_raw_pair: int, stride: int, sample_rate_hz: int,
                      payload: bytes | memoryview, *, mono_u8: bool = False) -> None:
        if mono_u8:
            a = np.frombuffer(payload, dtype=np.uint8).astype(np.int16)
            pairs = np.column_stack((a, np.zeros(a.size, dtype=np.int16)))
        else:
            pairs = np.frombuffer(payload, dtype="<i2")
            if pairs.size % 2:
                raise ValueError("AD9269 payload has an odd number of int16 values")
            pairs = pairs.reshape(-1, 2)
        with self._lock:
            new_rate = int(sample_rate_hz)
            new_stride = max(1, int(stride))
            if (new_rate != self._sample_rate_hz or
                    new_stride != self._stride):
                self._sample_rate_hz, self._stride = new_rate, new_stride
                self._history_bin_pairs = max(
                    1, round(new_rate * self.HISTORY_BIN_SECONDS)
                )
                self._reset_history()
            else:
                self._sample_rate_hz, self._stride = new_rate, new_stride
            if self._expected_raw_pair is None:
                self._expected_raw_pair = int(first_raw_pair)
            if first_raw_pair > self._expected_raw_pair:
                missing = min(self.capacity, first_raw_pair - self._expected_raw_pair)
                self._write_values(np.zeros(missing, np.int16), np.zeros(missing, np.int16), np.zeros(missing, bool))
            elif first_raw_pair < self._expected_raw_pair:
                skip = (self._expected_raw_pair - first_raw_pair + self._stride - 1) // self._stride
                # Entirely old/reordered datagrams must not move the expected
                # position backwards (otherwise a late UDP packet can replay
                # an already drawn segment).
                if skip >= len(pairs):
                    return
                pairs = pairs[skip:]
                first_raw_pair += skip * self._stride
            self._update_history(first_raw_pair, pairs)
            self._write_values(pairs[:, 0], pairs[:, 1], np.ones(len(pairs), bool))
            self._expected_raw_pair = first_raw_pair + len(pairs) * self._stride

    def _copy_latest(self, count: int):
        count = min(max(0, int(count)), self._count)
        if not count:
            return np.empty(0, np.int16), np.empty(0, np.int16), np.empty(0, bool)
        start, first = (self._write - count) % self.capacity, min(count, self.capacity - ((self._write - count) % self.capacity))
        if first == count:
            return self._a[start:start + count].copy(), self._b[start:start + count].copy(), self._valid[start:start + count].copy()
        return np.concatenate((self._a[start:], self._a[:count-first])), np.concatenate((self._b[start:], self._b[:count-first])), np.concatenate((self._valid[start:], self._valid[:count-first]))

    def envelope(self, samples: int, pixels: int):
        with self._lock:
            a, b, valid = self._copy_latest(samples)
        return self._envelope_arrays(a, b, valid, pixels)

    @staticmethod
    def _copy_ring_values(values: np.ndarray, write: int,
                          count: int) -> np.ndarray:
        if count <= 0:
            return np.empty(0, dtype=values.dtype)
        start = (write - count) % len(values)
        first = min(count, len(values) - start)
        if first == count:
            return values[start:start + count].copy()
        return np.concatenate((values[start:], values[:count - first]))

    def history_envelope(self, seconds: float, pixels: int):
        """Return a long-timebase envelope from the 1 ms history cache."""
        requested = max(1, int(np.ceil(
            float(seconds) / self.HISTORY_BIN_SECONDS
        )))
        with self._lock:
            include_current = self._history_current is not None
            count = min(
                max(0, requested - (1 if include_current else 0)),
                self._history_count,
            )
            min_a = self._copy_ring_values(
                self._history_min_a, self._history_write, count
            )
            max_a = self._copy_ring_values(
                self._history_max_a, self._history_write, count
            )
            min_b = self._copy_ring_values(
                self._history_min_b, self._history_write, count
            )
            max_b = self._copy_ring_values(
                self._history_max_b, self._history_write, count
            )
            valid = self._copy_ring_values(
                self._history_valid, self._history_write, count
            )
            if include_current:
                current = self._history_current
                min_a = np.append(min_a, current[0])
                max_a = np.append(max_a, current[1])
                min_b = np.append(min_b, current[2])
                max_b = np.append(max_b, current[3])
                valid = np.append(valid, True)
        if not min_a.size:
            return None
        bins = min(max(1, int(pixels)), min_a.size)
        bounds = np.linspace(0, min_a.size, bins + 1, dtype=np.int64)
        starts, widths = bounds[:-1], np.diff(bounds)
        return (
            np.minimum.reduceat(min_a, starts),
            np.maximum.reduceat(max_a, starts),
            np.minimum.reduceat(min_b, starts),
            np.maximum.reduceat(max_b, starts),
            np.add.reduceat(valid.astype(np.uint8), starts) == widths,
        )

    def raw_history(self, seconds: float | None = None) -> RawHistoryFrame:
        """Return unscaled long-history bins with their absolute bin numbers.

        Unlike ``history_envelope`` this method does not reduce to display
        pixels.  Invalid bins created by PL/network sample gaps are preserved so
        an automatic controller can reject a damaged analysis window.
        """
        requested = self._history_capacity if seconds is None else max(
            1, int(np.ceil(float(seconds) / self.HISTORY_BIN_SECONDS))
        )
        with self._lock:
            include_current = self._history_current is not None
            count = min(
                max(0, requested - (1 if include_current else 0)),
                self._history_count,
            )
            min_a = self._copy_ring_values(
                self._history_min_a, self._history_write, count
            )
            max_a = self._copy_ring_values(
                self._history_max_a, self._history_write, count
            )
            min_b = self._copy_ring_values(
                self._history_min_b, self._history_write, count
            )
            max_b = self._copy_ring_values(
                self._history_max_b, self._history_write, count
            )
            valid = self._copy_ring_values(
                self._history_valid, self._history_write, count
            )
            current_index = self._history_current_index
            if include_current:
                current = self._history_current
                min_a = np.append(min_a, current[0])
                max_a = np.append(max_a, current[1])
                min_b = np.append(min_b, current[2])
                max_b = np.append(max_b, current[3])
                valid = np.append(valid, True)
            total = int(valid.size)
            if current_index is None or total == 0:
                indices = np.empty(0, dtype=np.int64)
            else:
                last_index = int(current_index)
                indices = np.arange(
                    last_index - total + 1, last_index + 1,
                    dtype=np.int64,
                )
            sample_rate = int(self._sample_rate_hz)
        return RawHistoryFrame(
            bin_indices=indices,
            minimum_a=min_a,
            maximum_a=max_a,
            minimum_b=min_b,
            maximum_b=max_b,
            valid=valid,
            sample_rate_hz=sample_rate,
            bin_seconds=self.HISTORY_BIN_SECONDS,
        )

    @staticmethod
    def _envelope_arrays(a: np.ndarray, b: np.ndarray,
                         valid: np.ndarray, pixels: int):
        if not a.size:
            return None
        bounds = np.linspace(0, a.size, min(max(1, int(pixels)), a.size) + 1, dtype=np.int64)
        starts, widths = bounds[:-1], np.diff(bounds)
        return (np.minimum.reduceat(a, starts), np.maximum.reduceat(a, starts),
                np.minimum.reduceat(b, starts), np.maximum.reduceat(b, starts),
                np.add.reduceat(valid.astype(np.uint8), starts) == widths)

    def triggered_envelope(self, samples: int, pixels: int, *,
                           channel: int, level: float, rising: bool):
        """Return a synchronized A/B display window aligned to a crossing.

        Trigger search is bounded to two display windows and at most two
        million samples, so enabling a long timebase cannot monopolize the GUI
        thread. The returned boolean reports whether a real crossing was used.
        """
        samples = min(self.capacity, max(16, int(samples)))
        search_count = min(self.capacity, 1_000_000,
                           max(samples + 256, samples * 2))
        with self._lock:
            a, b, valid = self._copy_latest(search_count)
        if not a.size:
            return None
        values = a if int(channel) == 0 else b
        pre = min(samples // 4, max(0, samples - 1))
        post = samples - pre
        usable_end = len(values) - post
        locked = False
        start = max(0, len(values) - samples)
        if usable_end > pre:
            pair_valid = valid[:-1] & valid[1:]
            if rising:
                crossing = pair_valid & (values[:-1] < level) & (values[1:] >= level)
            else:
                crossing = pair_valid & (values[:-1] > level) & (values[1:] <= level)
            candidates = np.flatnonzero(crossing)
            candidates = candidates[(candidates >= pre) &
                                    (candidates <= usable_end)]
            if candidates.size:
                start = int(candidates[-1]) - pre + 1
                locked = True
        stop = min(len(values), start + samples)
        start = max(0, stop - samples)
        envelope = self._envelope_arrays(
            a[start:stop], b[start:stop], valid[start:stop], pixels
        )
        if envelope is None:
            return None
        return (*envelope, locked)

    def snapshot(self, samples: int):
        with self._lock:
            a, b, valid = self._copy_latest(samples)
            return a, b, valid, self._sample_rate_hz, self._stride

    @property
    def total_written(self) -> int:
        with self._lock:
            return self._total_written

    def read_since(self, cursor: int, limit: int):
        """Return only samples not previously consumed by an absolute cursor.

        If the consumer falls behind the retained ring window or ``limit``,
        the oldest unavailable samples are counted in ``dropped``.
        """
        with self._lock:
            latest = self._total_written
            earliest = latest - self._count
            start = max(int(cursor), earliest)
            dropped = max(0, earliest - int(cursor))
            if latest - start > int(limit):
                dropped += latest - start - int(limit)
                start = latest - int(limit)
            count = max(0, latest - start)
            if not count:
                empty_i16 = np.empty(0, np.int16)
                return (empty_i16, empty_i16.copy(), np.empty(0, bool),
                        self._sample_rate_hz, self._stride, latest, dropped)
            index = start % self.capacity
            first = min(count, self.capacity - index)
            if first == count:
                a = self._a[index:index + count].copy()
                b = self._b[index:index + count].copy()
                valid = self._valid[index:index + count].copy()
            else:
                rest = count - first
                a = np.concatenate((self._a[index:], self._a[:rest]))
                b = np.concatenate((self._b[index:], self._b[:rest]))
                valid = np.concatenate((self._valid[index:], self._valid[:rest]))
            return (a, b, valid, self._sample_rate_hz, self._stride,
                    latest, dropped)


class UdpReceiverCore:
    def __init__(self, ring: DualSampleRingBuffer, port: int = DATA_PORT, *, board_ip: str | None = None, metrics_callback: Callable[[dict], None] | None = None, error_callback: Callable[[str], None] | None = None, packet_callback: Callable[[object], None] | None = None):
        self.ring, self.port, self.board_ip = ring, port, board_ip
        self.metrics_callback, self.error_callback = metrics_callback, error_callback
        self.packet_callback = packet_callback
        self._stop_event, self._ready_event, self._stream_event = threading.Event(), threading.Event(), threading.Event()
        self._socket = None; self._startup_error = None; self._stream_id = None
        self._packets = self._packet_loss = self._invalid_packets = self._bytes = 0
        self._expected_pair = None; self._sample_rate = 0; self._stride = 1; self._flags = 0
        self._continuity = DaqdContinuityTracker()

    def prepare_stream(self, stream_id: int) -> None:
        self._stream_id, self._expected_pair = int(stream_id), None
        self._packets = self._packet_loss = self._invalid_packets = self._bytes = 0
        self._continuity.reset()
        self.ring.clear()

    def wait_until_ready(self, timeout: float = 1.0) -> bool: return self._ready_event.wait(timeout) and self._startup_error is None
    @property
    def startup_error(self): return self._startup_error
    def stop(self):
        self._stop_event.set()
        if self._socket:
            self._socket.close()
    def wait_for_stream(self, stream_id: int, timeout: float = 2.0) -> bool:
        return self._stream_event.wait(timeout) and self._stream_id == int(stream_id) and self._packets > 0

    def run(self) -> None:
        last_metrics, last_bytes = time.monotonic(), 0
        try:
            sock = self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 * 1024 * 1024)
            sock.bind(("", self.port)); sock.settimeout(.05); self._ready_event.set()
            while not self._stop_event.is_set():
                now = time.monotonic()
                try:
                    data, address = sock.recvfrom(65535)
                    if self.board_ip and address[0] != self.board_ip: continue
                    packet = parse_data_packet(data)
                    if packet.channel_mask not in (1, 3) or self._stream_id is None or packet.stream_id != self._stream_id: continue
                    continuity = self._continuity.observe(packet)
                    self._packet_loss = self._continuity.network_packets_lost
                    if not continuity.reordered_or_duplicate:
                        self.ring.append_packet(packet.first_sample_pair, 1, packet.sample_rate_hz,
                                                packet.payload, mono_u8=packet.channel_mask == 1)
                        self._expected_pair = packet.first_sample_pair + packet.sample_pair_count
                        if self.packet_callback:
                            self.packet_callback(packet)
                    self._packets += 1; self._bytes += len(data); self._flags = packet.flags; self._sample_rate = packet.sample_rate_hz; self._stream_event.set()
                except socket.timeout: pass
                except ValueError: self._invalid_packets += 1
                if now - last_metrics >= .25:
                    if self.metrics_callback: self.metrics_callback({'throughput_mbps': (self._bytes-last_bytes)*8/(now-last_metrics)/1e6, 'packets': self._packets, 'packet_loss': self._packet_loss, 'network_packet_loss': self._continuity.network_packets_lost, 'pl_sample_gap': self._continuity.pl_samples_lost, 'sample_gap': self._continuity.pl_samples_lost, 'index_gap_events': self._continuity.index_gap_events, 'last_gap_expected': self._continuity.last_gap_expected, 'last_gap_actual': self._continuity.last_gap_actual, 'block_loss': 0, 'invalid_packets': self._invalid_packets, 'flags': self._flags, 'sample_rate_hz': self._sample_rate, 'stride': 1, 'stream_id': self._stream_id or 0})
                    last_metrics, last_bytes = now, self._bytes
        except OSError as exc:
            self._startup_error = str(exc); self._ready_event.set()
            if not self._stop_event.is_set() and self.error_callback: self.error_callback(str(exc))
