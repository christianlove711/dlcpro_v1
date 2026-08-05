from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


@dataclass(frozen=True, slots=True)
class AcquisitionFrame:
    """A synchronized transmission/error frame consumed by Auto Lock algorithms."""

    time: tuple[float, ...]
    transmission: tuple[float, ...]
    error: tuple[float, ...]
    sample_rate: float
    source_type: str = "fpga_dual"
    timestamp: float = 0.0


@dataclass(frozen=True, slots=True)
class FpgaAcquisitionConfig:
    """Connection metadata only; the wire format is intentionally not specified yet."""

    host: str = "192.168.1.10"
    control_port: int = 5001
    data_port: int = 5002
    transmission_channel: int = 1
    error_channel: int = 2
    timeout_ms: int = 1000

    def validate(self) -> None:
        if not self.host.strip():
            raise ValueError("FPGA host is required.")
        for name, value in (
            ("control_port", self.control_port),
            ("data_port", self.data_port),
        ):
            if not 1 <= int(value) <= 65535:
                raise ValueError(f"{name} must be in the range 1..65535.")
        if int(self.transmission_channel) == int(self.error_channel):
            raise ValueError("Transmission and error channels must be different.")
        if int(self.timeout_ms) <= 0:
            raise ValueError("timeout_ms must be positive.")


class AcquisitionBackend(Protocol):
    """Future dual-channel FPGA backend contract.

    Implementations must return synchronized channels sharing one time axis. Packet
    layout, triggering, loss markers, and voltage calibration remain deliberately
    undefined until the dual-channel hardware protocol is confirmed.
    """

    config: FpgaAcquisitionConfig

    def connect(self) -> str: ...

    def disconnect(self) -> None: ...

    def read_frame(self) -> AcquisitionFrame: ...

    def start_stream(self, callback: Callable[[AcquisitionFrame], None]) -> None: ...

    def stop_stream(self) -> None: ...


class FpgaIntegrationPendingError(RuntimeError):
    pass


class FpgaAcquisitionBackend:
    """Non-networking placeholder kept behind the future backend contract."""

    def __init__(self, config: FpgaAcquisitionConfig) -> None:
        self.config = config

    def connect(self) -> str:
        self.config.validate()
        raise FpgaIntegrationPendingError("Dual-channel FPGA protocol is not available yet.")

    def disconnect(self) -> None:
        return

    def read_frame(self) -> AcquisitionFrame:
        raise FpgaIntegrationPendingError("Dual-channel FPGA protocol is not available yet.")

    def start_stream(self, callback: Callable[[AcquisitionFrame], None]) -> None:
        raise FpgaIntegrationPendingError("Dual-channel FPGA protocol is not available yet.")

    def stop_stream(self) -> None:
        return


def create_acquisition_backend(config: FpgaAcquisitionConfig) -> AcquisitionBackend:
    """Create the placeholder without opening sockets or touching hardware."""

    return FpgaAcquisitionBackend(config)
