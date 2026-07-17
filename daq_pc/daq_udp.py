from __future__ import annotations

import collections
import socket
import threading
import time

import numpy as np
from PySide6.QtCore import QThread, Signal

from daq_protocol import (
    BLOCK_BYTES,
    CONTROL_PORT,
    DATA_PORT,
    Command,
    Status,
    pack_control_request,
    parse_control_response,
    parse_data_packet,
)


class ControlClient:
    def __init__(self, board_ip: str, timeout: float = 1.0):
        self.board_ip = board_ip
        self.timeout = timeout
        self._request_id = 0
        self._lock = threading.Lock()

    def request(self, command: Command, **kwargs):
        with self._lock:
            self._request_id = (self._request_id + 1) & 0xFFFFFFFF
            request_id = self._request_id
            payload = pack_control_request(command, request_id, **kwargs)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(self.timeout)
                sock.sendto(payload, (self.board_ip, CONTROL_PORT))
                while True:
                    data, address = sock.recvfrom(512)
                    if address[0] != self.board_ip:
                        continue
                    response = parse_control_response(data)
                    if response.request_id != request_id:
                        continue
                    if response.command != (int(command) | int(Command.RESPONSE)):
                        continue
                    if response.status != Status.OK:
                        raise RuntimeError(
                            f"board rejected {command.name}: status={response.status}"
                        )
                    return response


class SampleRingBuffer:
    def __init__(self, capacity: int = 48_000_000):
        self.capacity = int(capacity)
        self._data = np.zeros(self.capacity, dtype=np.uint8)
        self._end = 0
        self._count = 0
        self._started = False
        self._gaps = collections.deque(maxlen=4096)
        self._lock = threading.Lock()

    @property
    def end_sample(self) -> int:
        with self._lock:
            return self._end

    def clear(self, first_sample: int = 0):
        with self._lock:
            self._end = int(first_sample)
            self._count = 0
            self._started = False
            self._gaps.clear()

    def _write(self, first_sample: int, values: np.ndarray):
        count = int(values.size)
        if count == 0:
            return
        if count >= self.capacity:
            values = values[-self.capacity :]
            first_sample += count - self.capacity
            count = self.capacity
        offset = first_sample % self.capacity
        first = min(count, self.capacity - offset)
        self._data[offset : offset + first] = values[:first]
        if first < count:
            self._data[: count - first] = values[first:]

    def append(self, first_sample: int, payload: bytes | memoryview):
        values = np.frombuffer(payload, dtype=np.uint8)
        with self._lock:
            first_sample = int(first_sample)
            if not self._started:
                self._end = first_sample
                self._started = True
            if first_sample < self._end:
                trim = self._end - first_sample
                if trim >= values.size:
                    return
                values = values[trim:]
                first_sample = self._end
            elif first_sample > self._end:
                gap = first_sample - self._end
                self._gaps.append((self._end, first_sample))
                zeros = np.zeros(min(gap, self.capacity), dtype=np.uint8)
                self._write(first_sample - zeros.size, zeros)
                self._end = first_sample
                self._count = min(self.capacity, self._count + gap)
            self._write(first_sample, values)
            self._end = first_sample + int(values.size)
            self._count = min(self.capacity, self._count + int(values.size))
            oldest = self._end - self.capacity
            while self._gaps and self._gaps[0][1] <= oldest:
                self._gaps.popleft()

    def envelope(self, samples: int, pixels: int):
        pixels = max(1, int(pixels))
        with self._lock:
            available = self._count if self._started else 0
            count = min(max(0, int(samples)), available)
            if count == 0:
                return None
            end = self._end
            start = end - count
            offset = start % self.capacity
            first = min(count, self.capacity - offset)
            if first == count:
                raw = self._data[offset : offset + count].copy()
            else:
                raw = np.concatenate((self._data[offset:], self._data[: count - first]))
            gaps = list(self._gaps)

        bins = min(pixels, count)
        boundaries = np.linspace(0, count, bins + 1, dtype=np.int64)
        minimum = np.minimum.reduceat(raw, boundaries[:-1])
        maximum = np.maximum.reduceat(raw, boundaries[:-1])
        valid = np.ones(bins, dtype=np.bool_)
        visible_start = start
        for gap_start, gap_end in gaps:
            left = max(gap_start, visible_start)
            right = min(gap_end, end)
            if left >= right:
                continue
            left_offset = left - visible_start
            right_offset = right - visible_start
            first_bin = max(
                0, int(np.searchsorted(boundaries, left_offset, side="right")) - 1
            )
            last_bin = min(
                bins, int(np.searchsorted(boundaries, right_offset, side="left"))
            )
            valid[first_bin:last_bin] = False
        return minimum, maximum, valid, visible_start, end

    def snapshot(self, samples: int):
        with self._lock:
            available = self._count if self._started else 0
            count = min(max(0, int(samples)), available)
            end = self._end
            start = end - count
            if count == 0:
                return np.empty(0, dtype=np.uint8), np.empty(0, dtype=np.bool_), start
            offset = start % self.capacity
            first = min(count, self.capacity - offset)
            if first == count:
                raw = self._data[offset : offset + count].copy()
            else:
                raw = np.concatenate((self._data[offset:], self._data[: count - first]))
            gaps = list(self._gaps)
        valid = np.ones(count, dtype=np.bool_)
        for gap_start, gap_end in gaps:
            left = max(gap_start, start)
            right = min(gap_end, end)
            if left < right:
                valid[left - start : right - start] = False
        return raw, valid, start


class UdpReceiver(QThread):
    metrics = Signal(dict)
    failed = Signal(str)

    def __init__(self, ring: SampleRingBuffer, port: int = DATA_PORT):
        super().__init__()
        self.ring = ring
        self.port = port
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._socket = None
        self._startup_error = None
        self._pending = {}
        self._expected_sample = None
        self._stream_id = None
        self._packets = 0
        self._packet_loss = 0
        self._block_loss = 0
        self._invalid_packets = 0
        self._bytes = 0
        self._last_block = None
        self._flags = 0
        self._sample_rate = 0

    def wait_until_ready(self, timeout=1.0):
        return self._ready_event.wait(timeout) and self._startup_error is None

    @property
    def startup_error(self):
        return self._startup_error

    def stop(self):
        self._stop_event.set()
        sock = self._socket
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    def _drain_pending(self, now: float):
        while self._expected_sample in self._pending:
            _, packet = self._pending.pop(self._expected_sample)
            self.ring.append(packet.first_sample, packet.payload)
            self._expected_sample += packet.sample_count
            if packet.packet_index == 0:
                if self._last_block is not None and packet.block_sequence > self._last_block + 1:
                    self._block_loss += packet.block_sequence - self._last_block - 1
                self._last_block = packet.block_sequence

        if not self._pending:
            return
        first_sample = min(self._pending)
        oldest = min(item[0] for item in self._pending.values())
        if first_sample > self._expected_sample and (
            len(self._pending) >= 32 or now - oldest >= 0.010
        ):
            missing = first_sample - self._expected_sample
            self._packet_loss += max(1, (missing + 1439) // 1440)
            self._expected_sample = first_sample
            self._drain_pending(now)

    def run(self):
        started = time.monotonic()
        last_metrics = started
        last_bytes = 0
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket = sock
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 * 1024 * 1024)
            sock.bind(("0.0.0.0", self.port))
            sock.settimeout(0.05)
            self._ready_event.set()
            while not self._stop_event.is_set():
                try:
                    datagram, _ = sock.recvfrom(2048)
                except socket.timeout:
                    self._drain_pending(time.monotonic())
                    datagram = None
                except OSError:
                    if self._stop_event.is_set():
                        break
                    raise
                if datagram:
                    try:
                        packet = parse_data_packet(datagram)
                    except ValueError:
                        self._invalid_packets += 1
                    else:
                        if self._stream_id != packet.stream_id:
                            self._stream_id = packet.stream_id
                            self._pending.clear()
                            self._expected_sample = packet.first_sample
                            self._last_block = None
                            self.ring.clear(packet.first_sample)
                        if packet.first_sample >= self._expected_sample:
                            self._pending[packet.first_sample] = (time.monotonic(), packet)
                            self._drain_pending(time.monotonic())
                        self._packets += 1
                        self._bytes += packet.sample_count
                        self._flags = packet.flags
                        self._sample_rate = packet.sample_rate_hz

                now = time.monotonic()
                if now - last_metrics >= 0.25:
                    interval = now - last_metrics
                    throughput = (self._bytes - last_bytes) * 8.0 / interval / 1_000_000.0
                    self.metrics.emit(
                        {
                            "stream_id": self._stream_id or 0,
                            "sample_rate_hz": self._sample_rate,
                            "throughput_mbps": throughput,
                            "packets": self._packets,
                            "packet_loss": self._packet_loss,
                            "block_loss": self._block_loss,
                            "invalid_packets": self._invalid_packets,
                            "flags": self._flags,
                            "seconds": now - started,
                        }
                    )
                    last_metrics = now
                    last_bytes = self._bytes
        except Exception as exc:
            if not self._ready_event.is_set():
                self._startup_error = str(exc)
            self._ready_event.set()
            self.failed.emit(str(exc))
        finally:
            sock = self._socket
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
            self._socket = None
            self._ready_event.set()
