from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class AcquisitionFrame:
    time: tuple[float, ...]
    transmission: tuple[float, ...]
    error: tuple[float, ...]
    sample_rate: float
    source_type: str
    timestamp: float


@dataclass(slots=True)
class AcquisitionConfig:
    source_type: str
    resource: str
    transmission_channel: int
    error_channel: int
    points: int
    timeout_ms: int
    daq_device: str = ""
    daq_transmission_channel: str = "ai0"
    daq_error_channel: str = "ai1"
    daq_sample_rate: float = 10_000.0
    daq_window_seconds: float = 2.0


class AcquisitionBackend(Protocol):
    def connect(self) -> str:
        ...

    def disconnect(self) -> None:
        ...

    def read_frame(self) -> AcquisitionFrame:
        ...

    def start_stream(self, callback) -> None:
        ...

    def stop_stream(self) -> None:
        ...


@dataclass(slots=True)
class _Waveform:
    time: tuple[float, ...]
    values: tuple[float, ...]
    sample_rate: float


class _RawSocketTektronixTransport:
    def __init__(self, resource: str, timeout_ms: int) -> None:
        parts = resource.split("::")
        if len(parts) < 3 or parts[0].upper() != "SOCKET":
            raise ValueError("Socket resource must look like SOCKET::<ip>::<port>.")
        self.host = parts[1]
        self.port = int(parts[2])
        self.timeout_s = max(0.2, timeout_ms / 1000.0)
        self.sock: socket.socket | None = None

    def connect(self) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout_s)
        self.sock.settimeout(self.timeout_s)

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def write(self, command: str) -> None:
        if self.sock is None:
            raise RuntimeError("Socket is not connected.")
        self.sock.sendall((command + "\n").encode("ascii"))

    def query(self, command: str) -> str:
        self.write(command)
        chunks: list[bytes] = []
        while True:
            chunk = self._recv(4096)
            chunks.append(chunk)
            if chunk.endswith(b"\n"):
                break
        return b"".join(chunks).decode("ascii", errors="replace").strip()

    def query_binary_int8(self, command: str) -> list[int]:
        self.write(command)
        first = self._recv_exact(1)
        if first != b"#":
            remainder = self._read_until_newline(first)
            raise RuntimeError(f"Unexpected binary block header: {remainder!r}")
        digits = int(self._recv_exact(1).decode("ascii"))
        length = int(self._recv_exact(digits).decode("ascii"))
        payload = self._recv_exact(length)
        self._read_optional_terminator()
        return [int.from_bytes(payload[i : i + 1], "big", signed=True) for i in range(len(payload))]

    def _recv(self, size: int) -> bytes:
        if self.sock is None:
            raise RuntimeError("Socket is not connected.")
        data = self.sock.recv(size)
        if not data:
            raise RuntimeError("Socket connection closed by oscilloscope.")
        return data

    def _recv_exact(self, size: int) -> bytes:
        chunks: list[bytes] = []
        remaining = size
        while remaining > 0:
            chunk = self._recv(remaining)
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _read_until_newline(self, prefix: bytes) -> bytes:
        chunks = [prefix]
        while not chunks[-1].endswith(b"\n"):
            chunks.append(self._recv(4096))
        return b"".join(chunks)

    def _read_optional_terminator(self) -> None:
        if self.sock is None:
            return
        previous_timeout = self.sock.gettimeout()
        self.sock.settimeout(0.03)
        try:
            try:
                self.sock.recv(1)
            except (TimeoutError, socket.timeout):
                pass
        finally:
            self.sock.settimeout(previous_timeout)


class TektronixScopeBackend:
    def __init__(self, config: AcquisitionConfig) -> None:
        self.config = config
        self._scope = None
        self._resource_manager = None
        self._raw_socket: _RawSocketTektronixTransport | None = None

    def connect(self) -> str:
        resource = self.config.resource.strip()
        if not resource:
            raise RuntimeError("Tektronix resource is empty.")
        if resource.upper().startswith("SOCKET::"):
            self._raw_socket = _RawSocketTektronixTransport(resource, self.config.timeout_ms)
            self._raw_socket.connect()
            return self._raw_socket.query("*IDN?")

        try:
            import pyvisa  # type: ignore
        except ImportError as exc:  # noqa: BLE001
            raise RuntimeError("pyvisa is not installed, so Tektronix VISA capture is unavailable.") from exc

        self._resource_manager = pyvisa.ResourceManager()
        self._scope = self._resource_manager.open_resource(resource)
        self._scope.timeout = int(self.config.timeout_ms)
        self._scope.write_termination = "\n"
        self._scope.read_termination = "\n"
        return str(self._scope.query("*IDN?")).strip()

    def disconnect(self) -> None:
        if self._raw_socket is not None:
            self._raw_socket.close()
            self._raw_socket = None
        if self._scope is not None:
            try:
                self._scope.close()
            finally:
                self._scope = None
        if self._resource_manager is not None:
            try:
                self._resource_manager.close()
            finally:
                self._resource_manager = None

    def read_frame(self) -> AcquisitionFrame:
        transmission = self._read_waveform(self.config.transmission_channel)
        error = self._read_waveform(self.config.error_channel)
        n = min(len(transmission.time), len(transmission.values), len(error.values))
        if n <= 1:
            raise RuntimeError("Oscilloscope returned too few samples.")
        return AcquisitionFrame(
            time=transmission.time[:n],
            transmission=transmission.values[:n],
            error=error.values[:n],
            sample_rate=transmission.sample_rate,
            source_type="tektronix",
            timestamp=time.time(),
        )

    def start_stream(self, callback) -> None:
        raise RuntimeError("Tektronix scope capture is frame-based in this build.")

    def stop_stream(self) -> None:
        return

    def _read_waveform(self, channel: int) -> _Waveform:
        points = max(2, int(self.config.points))
        self._write(f"DATA:SOURCE CH{int(channel)}")
        self._write("DATA:START 1")
        self._write(f"DATA:STOP {points}")
        self._write("DATA:WIDTH 1")
        self._write("DATA:ENC RIBINARY")

        ymult = self._query_float("WFMPRE:YMULT?", "WFMOUTPRE:YMULT?")
        yzero = self._query_float("WFMPRE:YZERO?", "WFMOUTPRE:YZERO?")
        yoff = self._query_float("WFMPRE:YOFF?", "WFMOUTPRE:YOFF?")
        xincr = self._query_float("WFMPRE:XINCR?", "WFMOUTPRE:XINCR?")
        xzero = self._query_float("WFMPRE:XZERO?", "WFMOUTPRE:XZERO?")

        raw = self._query_binary_int8("CURVE?")
        values = tuple((sample - yoff) * ymult + yzero for sample in raw)
        times = tuple(xzero + index * xincr for index in range(len(values)))
        sample_rate = 1.0 / xincr if abs(xincr) > 1e-15 else 0.0
        return _Waveform(time=times, values=values, sample_rate=sample_rate)

    def _write(self, command: str) -> None:
        if self._raw_socket is not None:
            self._raw_socket.write(command)
            return
        if self._scope is None:
            raise RuntimeError("Tektronix scope is not connected.")
        self._scope.write(command)

    def _query(self, command: str) -> str:
        if self._raw_socket is not None:
            return self._raw_socket.query(command)
        if self._scope is None:
            raise RuntimeError("Tektronix scope is not connected.")
        return str(self._scope.query(command)).strip()

    def _query_float(self, *commands: str) -> float:
        last_error: Exception | None = None
        for command in commands:
            try:
                return float(self._query(command))
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise RuntimeError(f"Failed to read waveform preamble value: {last_error}")

    def _query_binary_int8(self, command: str) -> list[int]:
        if self._raw_socket is not None:
            return self._raw_socket.query_binary_int8(command)
        if self._scope is None:
            raise RuntimeError("Tektronix scope is not connected.")
        return list(self._scope.query_binary_values(command, datatype="b", container=list))


class DaqPlaceholderBackend:
    def __init__(self, config: AcquisitionConfig) -> None:
        self.config = config

    def connect(self) -> str:
        try:
            import nidaqmx  # noqa: F401  # type: ignore
        except ImportError as exc:  # noqa: BLE001
            raise RuntimeError("nidaqmx is not installed. DAQ capture is reserved for the next hardware step.") from exc
        raise RuntimeError("DAQ capture backend is reserved until the concrete DAQ model and channel map are confirmed.")

    def disconnect(self) -> None:
        return

    def read_frame(self) -> AcquisitionFrame:
        raise RuntimeError("DAQ capture backend is not active in this build.")

    def start_stream(self, callback) -> None:
        raise RuntimeError("DAQ streaming is reserved until the concrete DAQ model is confirmed.")

    def stop_stream(self) -> None:
        return


def create_acquisition_backend(config: AcquisitionConfig) -> AcquisitionBackend:
    if config.source_type == "daq":
        return DaqPlaceholderBackend(config)
    return TektronixScopeBackend(config)
