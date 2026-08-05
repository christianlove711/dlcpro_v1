from __future__ import annotations

import socket
import threading
import time
from collections.abc import Callable

import numpy as np

from .daq_protocol_v2 import DATA_PORT, parse_data_packet
from .daq_udp_dual import ControlClient as _DualControlClient


class ControlClient(_DualControlClient):
    def __init__(self, board_ip: str, timeout: float = 1.0):
        super().__init__(board_ip, timeout, adc_model=0)


class SampleRingBuffer:
    def __init__(self, capacity: int = 10_000_000):
        self.capacity = int(capacity)
        self._codes = np.zeros(self.capacity, dtype=np.uint8)
        self._valid = np.zeros(self.capacity, dtype=np.bool_)
        self._write = self._count = 0
        self._first = 0
        self._lock = threading.Lock()

    def clear(self):
        with self._lock:
            self._write = self._count = self._first = 0
            self._valid.fill(False)

    def append_packet(self, first_sample: int, payload: bytes | memoryview):
        values = np.frombuffer(payload, dtype=np.uint8)
        with self._lock:
            count = min(values.size, self.capacity)
            if not count: return
            values = values[-count:]
            first = min(count, self.capacity - self._write)
            self._codes[self._write:self._write+first] = values[:first]
            self._valid[self._write:self._write+first] = True
            if first < count:
                self._codes[:count-first] = values[first:]
                self._valid[:count-first] = True
            self._write = (self._write + count) % self.capacity
            self._count = min(self.capacity, self._count + count)
            self._first = int(first_sample) + count - self._count

    def _copy_latest(self, count: int):
        count = min(max(0, int(count)), self._count)
        if not count: return np.empty(0, np.uint8), np.empty(0, bool), self._first
        start = (self._write - count) % self.capacity
        first = min(count, self.capacity - start)
        if first == count: return self._codes[start:start+count].copy(), self._valid[start:start+count].copy(), self._first + self._count - count
        return np.concatenate((self._codes[start:], self._codes[:count-first])), np.concatenate((self._valid[start:], self._valid[:count-first])), self._first + self._count - count

    def snapshot(self, count: int):
        with self._lock: return self._copy_latest(count)

    def envelope(self, samples: int, pixels: int):
        with self._lock: codes, valid, _ = self._copy_latest(samples)
        if not codes.size: return None
        bounds = np.linspace(0, codes.size, min(max(1, int(pixels)), codes.size)+1, dtype=np.int64)
        starts, widths = bounds[:-1], np.diff(bounds)
        return np.minimum.reduceat(codes, starts), np.maximum.reduceat(codes, starts), np.add.reduceat(valid.astype(np.uint8), starts) == widths


class UdpReceiverCore:
    def __init__(self, ring: SampleRingBuffer, port: int = DATA_PORT, *, board_ip: str | None = None, metrics_callback: Callable[[dict], None] | None = None, error_callback: Callable[[str], None] | None = None):
        self.ring, self.port, self.board_ip = ring, port, board_ip
        self.metrics_callback, self.error_callback = metrics_callback, error_callback
        self._stop_event, self._ready_event = threading.Event(), threading.Event(); self._socket = None; self._startup_error = None
        self._packets = self._invalid = self._bytes = 0; self._rate = 0; self._last_sample = None
    def wait_until_ready(self, timeout=1.0): return self._ready_event.wait(timeout) and self._startup_error is None
    @property
    def startup_error(self): return self._startup_error
    def stop(self):
        self._stop_event.set()
        if self._socket: self._socket.close()
    def run(self):
        last_time, last_bytes = time.monotonic(), 0
        try:
            sock = self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64*1024*1024); sock.bind(("", self.port)); sock.settimeout(.05); self._ready_event.set()
            while not self._stop_event.is_set():
                now = time.monotonic()
                try:
                    data, address = sock.recvfrom(65535)
                    if self.board_ip and address[0] != self.board_ip: continue
                    packet = parse_data_packet(data)
                    if packet.channel_mask != 1: continue
                    self.ring.append_packet(packet.first_sample_pair, packet.payload); self._packets += 1; self._bytes += len(data); self._rate = packet.sample_rate_hz
                except socket.timeout: pass
                except ValueError: self._invalid += 1
                if now-last_time >= .25:
                    if self.metrics_callback: self.metrics_callback({'throughput_mbps': (self._bytes-last_bytes)*8/(now-last_time)/1e6, 'packets':self._packets, 'packet_loss':0, 'invalid_packets':self._invalid, 'sample_rate_hz':self._rate})
                    last_time, last_bytes = now, self._bytes
        except OSError as exc:
            self._startup_error = str(exc); self._ready_event.set()
            if not self._stop_event.is_set() and self.error_callback: self.error_callback(str(exc))
