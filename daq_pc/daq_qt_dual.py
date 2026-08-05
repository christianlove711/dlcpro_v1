from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from .daq_protocol_v2 import DATA_PORT
from .daq_udp_dual import DualSampleRingBuffer, UdpReceiverCore


class UdpDualReceiver(QThread):
    metrics = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        ring: DualSampleRingBuffer,
        port: int = DATA_PORT,
        *,
        board_ip: str | None = None,
        packet_callback=None,
    ) -> None:
        super().__init__()
        self._core = UdpReceiverCore(
            ring,
            port,
            board_ip=board_ip,
            metrics_callback=self.metrics.emit,
            error_callback=self.failed.emit,
            packet_callback=packet_callback,
        )

    def run(self) -> None:
        self._core.run()

    def stop(self) -> None:
        self._core.stop()

    def wait_until_ready(self, timeout: float = 1.0) -> bool:
        return self._core.wait_until_ready(timeout)

    def wait_for_stream(self, stream_id: int, timeout: float = 2.0) -> bool:
        return self._core.wait_for_stream(stream_id, timeout)

    def prepare_stream(self, stream_id: int) -> None:
        self._core.prepare_stream(stream_id)

    @property
    def startup_error(self):
        return self._core.startup_error
