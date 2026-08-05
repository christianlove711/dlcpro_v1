from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from .daq_protocol import DATA_PORT
from .daq_udp import SampleRingBuffer, UdpReceiverCore


class UdpReceiver(QThread):
    metrics = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        ring: SampleRingBuffer,
        port: int = DATA_PORT,
        *,
        board_ip: str | None = None,
    ) -> None:
        super().__init__()
        self._core = UdpReceiverCore(
            ring,
            port,
            board_ip=board_ip,
            metrics_callback=self.metrics.emit,
            error_callback=self.failed.emit,
        )

    def run(self) -> None:
        self._core.run()

    def stop(self) -> None:
        self._core.stop()

    def wait_until_ready(self, timeout: float = 1.0) -> bool:
        return self._core.wait_until_ready(timeout)

    @property
    def startup_error(self):
        return self._core.startup_error
