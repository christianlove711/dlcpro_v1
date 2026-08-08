"""AD9269-only PL-UDP oscilloscope and recorder."""
from __future__ import annotations

import csv
import queue
import struct
import subprocess
import sys
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
from PySide6.QtCore import QPointF, QRectF, QSettings, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDoubleSpinBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget,
)

from widgets.common_controls import VisibleCheckBox
from ui_scaling import schedule_window_fit

from .daq_protocol_v2 import CONFIG_CHANNEL_SWAP, CONFIG_TEST_SHIFT, Command
from .daq_qt_dual import UdpDualReceiver
from .daq_udp_dual import ControlClient, DualSampleRingBuffer
from .dlcpro_settings_dialog import (
    DlcProSettingsDialog,
    DlcScanSession,
    RecordingOptionsDialog,
)
from .adc_peak_balance_controller import AdcPeakBalanceController
from .adc_peak_balance_window import AdcPeakBalanceWindow
from .fpga_programmer import FpgaProgrammer, find_vivado_batch
from .scan_control_window import DlcScanControlWindow


PL_BOARD_IP = "192.168.20.2"
PC_PL_IP = "192.168.20.1"
DISPLAY_FPS = 30
# The deployed AD9269 input frontend assigns the physical INA/INB samples to
# the opposite DDR edges.  Keep the wire protocol unchanged and compensate at
# configuration time so an unchecked UI means the natural mapping INA->A and
# INB->B.  Checking "manual swap" then intentionally reverses that mapping.
AD9269_PHYSICAL_EDGE_SWAP = True


def ad9269_config_channel_swap(manual_swap: bool) -> int:
    return CONFIG_CHANNEL_SWAP if bool(manual_swap) ^ AD9269_PHYSICAL_EDGE_SWAP else 0
# At 5 MSPS the built-in 32.55 kHz DAC sine has about 154 samples/period.
# A 200k-sample min/max window compresses roughly 1,300 periods into 900
# pixels and therefore looks like a solid vertical band.  Use a scope-like
# default that shows about 13 periods; users can still expand the window for
# long-term monitoring.
DISPLAY_SAMPLES = 2_000
DEFAULT_FPGA_BIT = (
    Path.home() / "Desktop" / "采集卡项目_最终版" / "02_最终硬件" / "top.bit"
)
FPGA_PROGRAM_TCL = (
    Path(__file__).resolve().parent.parent / "tools" / "program_fpga_bit.tcl"
)


def show_window_front(window: QWidget) -> None:
    """Restore and foreground an existing tool window after a button click."""
    if window.windowState() & Qt.WindowMinimized:
        window.setWindowState(window.windowState() & ~Qt.WindowMinimized)
    window.show()
    schedule_window_fit(window)
    window.raise_()
    window.activateWindow()

    def promote_after_native_show():
        if not window.isVisible():
            return
        schedule_window_fit(window)
        window.raise_()
        window.activateWindow()
        if sys.platform != "win32":
            return
        try:
            import ctypes

            hwnd = int(window.winId())
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        except (AttributeError, OSError, TypeError, ValueError):
            # Qt activation above remains the portable fallback.
            pass

    # Windows may finish creating/restoring the native HWND after show().
    QTimer.singleShot(0, promote_after_native_show)

APP_STYLE = """
QMainWindow, QWidget#appRoot {
    background: #f3f6fa;
    color: #172033;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}
QLabel, QCheckBox {
    background: transparent;
    color: #172033;
}
QLabel:disabled, QCheckBox:disabled {
    color: #a3adbb;
}
QFrame#card {
    background: #ffffff;
    border: 1px solid #dce3ed;
    border-radius: 10px;
}
QFrame#hero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #10233f, stop:1 #1d4f82);
    border: 0;
    border-radius: 12px;
}
QLabel#heroEyebrow {
    color: #9dc8f4;
    font-size: 11px;
    font-weight: 700;
}
QLabel#heroTitle {
    color: #ffffff;
    font-size: 23px;
    font-weight: 700;
}
QLabel#heroSubtitle {
    color: #d5e6f6;
}
QLabel#eyebrow {
    color: #3563a9;
    font-size: 11px;
    font-weight: 700;
}
QLabel#pageTitle {
    color: #111827;
    font-size: 22px;
    font-weight: 700;
}
QLabel#pageSubtitle, QLabel#muted {
    color: #69758a;
}
QLabel#sectionTitle {
    color: #25324a;
    font-size: 14px;
    font-weight: 700;
}
QLabel#statePill {
    background: #eef2f7;
    border: 1px solid #d7dee9;
    border-radius: 13px;
    color: #536076;
    font-weight: 700;
    padding: 4px 11px;
}
QLabel#statePill[state="connected"] {
    background: #e8f7ef;
    border-color: #bce6ce;
    color: #137044;
}
QLabel#statePill[state="running"] {
    background: #e9f2ff;
    border-color: #bdd5fa;
    color: #195ca8;
}
QLabel#statePill[state="error"] {
    background: #fff0f0;
    border-color: #f2c4c4;
    color: #b52d35;
}
QLineEdit, QComboBox, QSpinBox {
    min-height: 32px;
    padding: 0 10px;
    background: #ffffff;
    border: 1px solid #cfd8e6;
    border-radius: 6px;
    color: #172033;
    selection-background-color: #2f6fcb;
}
QFrame#metricTile {
    background: #ffffff;
    border: 1px solid #dce3ed;
    border-radius: 9px;
}
QLabel#metricTitle {
    color: #738096;
    font-size: 11px;
    font-weight: 600;
}
QLabel#metricValue {
    color: #172033;
    font-size: 16px;
    font-weight: 700;
}
QLabel#metricHint {
    color: #8490a3;
    font-size: 10px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #4b82cf;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    background: #f2f4f7;
    color: #8993a4;
}
QComboBox::drop-down {
    border: 0;
    width: 28px;
}
QCheckBox {
    min-height: 28px;
    spacing: 7px;
    background: transparent;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QPushButton {
    min-height: 34px;
    padding: 0 16px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    color: #25324a;
    font-weight: 600;
}
QPushButton:hover {
    background: #f6f8fb;
    border-color: #9eacbf;
}
QPushButton:pressed {
    background: #edf1f6;
}
QPushButton:disabled {
    background: #f0f2f5;
    border-color: #e0e5ec;
    color: #a3adbb;
}
QPushButton#primaryButton {
    background: #286bc1;
    border-color: #286bc1;
    color: #ffffff;
}
QPushButton#primaryButton:hover {
    background: #225ca6;
}
QPushButton#startButton {
    background: #178455;
    border-color: #178455;
    color: #ffffff;
}
QPushButton#startButton:hover {
    background: #126e47;
}
QPushButton#stopButton {
    background: #ffffff;
    border-color: #e3a7ab;
    color: #ad2b34;
}
QPushButton#recordButton:checked {
    background: #fff1f1;
    border-color: #e4a3a8;
    color: #aa2932;
}
QProgressBar {
    min-height: 28px; border: 1px solid #cbd5e1; border-radius: 6px;
    background: #edf1f6; color: #25324a; text-align: center;
}
QProgressBar::chunk { background: #286bc1; border-radius: 5px; }
QMessageBox {
    background: #ffffff;
    color: #172033;
}
QMessageBox QLabel {
    background: transparent;
    color: #172033;
}
QMessageBox QPushButton {
    min-width: 76px;
    background: #ffffff;
    color: #25324a;
    border: 1px solid #cbd5e1;
}
QLabel#statusHeadline {
    color: #172033;
    font-size: 16px;
    font-weight: 700;
}
QLabel#metrics {
    color: #536076;
}
"""

SCOPE_STYLE = """
QWidget {
    background: #f3f6fa;
    color: #172033;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 12px;
}
QFrame#scopeToolbar, QFrame#scopeReadout {
    background: #ffffff;
    border: 1px solid #dce3ed;
    border-radius: 9px;
}
QLabel#triggerLocked {
    color: #13875a;
    font-weight: 700;
}
QLabel#triggerWaiting {
    color: #b7791f;
    font-weight: 700;
}
QLabel#scopeChannel {
    font-size: 15px;
    font-weight: 700;
}
QLabel#scopeWindowTitle {
    color: #102f57;
    font-size: 22px;
    font-weight: 700;
}
QPushButton#scopeChannelButton {
    min-height: 28px;
    padding: 0 10px;
    background: transparent;
    border: 1px solid transparent;
    color: #25324a;
    font-size: 15px;
    font-weight: 700;
}
QPushButton#scopeChannelButton:hover {
    background: #e9f2ff;
    border-color: #bdd5fa;
    color: #195ca8;
}
QLabel#scopeCaption {
    color: #475569;
    font-weight: 600;
}
QComboBox {
    min-height: 30px;
    padding: 0 8px;
    background: #ffffff;
    border: 1px solid #cfd8e6;
    border-radius: 6px;
}
QDoubleSpinBox {
    min-height: 30px;
    padding: 0 8px;
    background: #ffffff;
    border: 1px solid #cfd8e6;
    border-radius: 6px;
}
QComboBox:focus {
    border-color: #4b82cf;
}
QPushButton {
    min-height: 30px;
    padding: 0 15px;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-weight: 600;
}
QPushButton:checked {
    background: #e9f2ff;
    border-color: #7ea9e3;
    color: #195ca8;
}
"""

TIMEBASES_PER_DIV = (
    ("0.1 µs/div", 0.1e-6),
    ("0.2 µs/div", 0.2e-6),
    ("0.5 µs/div", 0.5e-6),
    ("1 µs/div", 1e-6),
    ("2 µs/div", 2e-6),
    ("5 µs/div", 5e-6),
    ("10 µs/div", 10e-6),
    ("20 µs/div", 20e-6),
    ("50 µs/div", 50e-6),
    ("100 µs/div", 100e-6),
    ("200 µs/div", 200e-6),
    ("500 µs/div", 500e-6),
    ("1 ms/div", 1e-3),
    ("2 ms/div", 2e-3),
    ("5 ms/div", 5e-3),
    ("10 ms/div", 10e-3),
    ("20 ms/div", 20e-3),
    ("50 ms/div", 50e-3),
    ("100 ms/div", 100e-3),
    ("200 ms/div", 200e-3),
    ("500 ms/div", 500e-3),
    ("1 s/div", 1.0),
    ("2 s/div", 2.0),
    ("5 s/div", 5.0),
    ("10 s/div", 10.0),
)
DISPLAY_FPS_OPTIONS = (10, 20, 30)
RAW_ENVELOPE_SAMPLE_LIMIT = 250_000
SCROLL_DIVISORS = (
    ("实时", 1),
    ("1/2 速", 2),
    ("1/4 速", 4),
    ("1/8 速", 8),
)


def windows_jumbo_status() -> tuple[bool | None, str]:
    """Return whether the NIC owning 192.168.20.1 accepts a 9 KB frame."""
    if sys.platform != "win32":
        return None, "仅能在 Windows 上自动检查网卡巨帧"
    script = (
        "$a=Get-NetIPAddress -IPAddress '192.168.20.1' -AddressFamily IPv4 "
        "-ErrorAction Stop | Get-NetAdapter; "
        "$p=Get-NetAdapterAdvancedProperty -Name $a.Name "
        "-RegistryKeyword '*JumboPacket' -ErrorAction Stop; "
        "Write-Output ($a.Name+'|'+($p.RegistryValue -join ','))"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode:
            return None, "无法自动读取网卡巨帧属性"
        line = result.stdout.strip().splitlines()[-1]
        name, value = line.rsplit("|", 1)
        enabled = any(int(item) >= 9000 for item in value.split(",") if item.isdigit())
        return enabled, f"{name}：JumboPacket={value}"
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None, "无法自动读取网卡巨帧属性"


class StatusPoller(QThread):
    received = Signal(object)
    failed = Signal(str)

    def __init__(self, client: ControlClient):
        super().__init__()
        self.client = client
        self._stop = threading.Event()

    def run(self):
        while not self._stop.wait(0.5):
            try:
                self.received.emit(self.client.request(Command.STATUS))
            except Exception as exc:  # status failures must not kill the GUI
                self.failed.emit(str(exc))

    def stop(self):
        self._stop.set()


class AcquisitionStarter(QThread):
    """Run the PL START/STATUS handshake without blocking the GUI thread."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, control: ControlClient, *, sample_rate_hz: int,
                 flags: int, jumbo_enabled: bool,
                 previous_stream: int, parent=None):
        super().__init__(parent)
        self.control = control
        self.sample_rate_hz = int(sample_rate_hz)
        self.flags = int(flags)
        self.jumbo_enabled = bool(jumbo_enabled)
        self.previous_stream = int(previous_stream)

    def run(self):
        try:
            self.control.request(Command.STOP)
            self.control.adc_model = 1
            self.control.request(
                Command.CONFIG,
                sample_rate_hz=self.sample_rate_hz,
                flags=self.flags,
                jumbo_enable=self.jumbo_enabled,
            )
            self.control.request(Command.START, monitor_enable=True)
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                if self.isInterruptionRequested():
                    raise RuntimeError("启动已取消")
                candidate = self.control.request(Command.STATUS)
                if (candidate.daq_state == 3 and
                        int(candidate.stream_id) != self.previous_stream):
                    self.succeeded.emit(candidate)
                    return
                self.msleep(20)
            raise TimeoutError("板卡未在 2 秒内进入 RUNNING 或更新 stream_id")
        except Exception as exc:
            try:
                self.control.request(Command.STOP)
            except Exception:
                pass
            self.failed.emit(str(exc))


class CsvRecorder:
    """Loss-aware high-speed spool followed by streaming CSV export.

    Writing 20 million CSV rows per second is not realistic.  During capture
    the receive thread therefore queues complete UDP payloads and a background
    thread writes a compact binary spool.  CSV formatting happens only after
    capture stops, so plot refresh cadence cannot discard recording samples.
    """

    LEGACY_FILE_MAGIC = b"PLRAW1\0\0"
    FILE_MAGIC = b"PLRAW2\0\0"
    RECORD_HEADER = struct.Struct("<dIIQII")

    def __init__(self, path: str, channel_mask: int = 3):
        if channel_mask not in (1, 2, 3):
            raise ValueError("channel_mask must select A, B, or A+B")
        self.channel_mask = int(channel_mask)
        requested = Path(path)
        self.output_path = requested if requested.suffix.lower() == ".csv" else None
        self.path = str(requested.with_suffix(requested.suffix + ".plraw")
                        if self.output_path else requested)
        self.items: queue.Queue[tuple | None] = queue.Queue(maxsize=4096)
        self._state_lock = threading.Lock()
        self._accepting = True
        self._legacy_offset = 0
        self.dropped_samples = 0
        self.written_samples = 0
        self.error: Exception | None = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            with open(self.path, "wb", buffering=8 * 1024 * 1024) as handle:
                handle.write(self.FILE_MAGIC)
                handle.write(bytes((self.channel_mask,)))
                while True:
                    item = self.items.get()
                    if item is None:
                        return
                    host_time, stream_id, rate, first_sample, count, payload, valid = item
                    valid_bytes = b"" if valid is None else valid
                    handle.write(self.RECORD_HEADER.pack(
                        host_time, stream_id, rate, first_sample, count,
                        len(valid_bytes)
                    ))
                    handle.write(payload)
                    if valid_bytes:
                        handle.write(valid_bytes)
                    self.written_samples += count
        except Exception as exc:
            self.error = exc

    def _enqueue(self, item: tuple, count: int) -> bool:
        with self._state_lock:
            if not self._accepting or self.error is not None:
                return False
            try:
                self.items.put_nowait(item)
                return True
            except queue.Full:
                self.dropped_samples += int(count)
                return False

    def append_packet(self, host_time: float, packet) -> bool:
        """Queue one accepted AD9269 UDP packet, retaining selected channels."""
        count = int(packet.sample_pair_count)
        if packet.channel_mask != 3 or len(packet.payload) != count * 4:
            self.dropped_samples += count
            return False
        if self.channel_mask == 3:
            payload = packet.payload
        else:
            pairs = np.frombuffer(packet.payload, dtype="<i2").reshape(-1, 2)
            column = 0 if self.channel_mask == 1 else 1
            payload = np.ascontiguousarray(pairs[:, column]).tobytes()
        return self._enqueue((
            float(host_time), int(packet.stream_id), int(packet.sample_rate_hz),
            int(packet.first_sample_pair), count, payload, None,
        ), count)

    def append(self, item: tuple) -> bool:
        """Compatibility API used by tests and non-network producers."""
        host_time, stream_id, rate, a, b, valid = item
        a = np.asarray(a, dtype="<i2")
        b = np.asarray(b, dtype="<i2")
        valid = np.asarray(valid, dtype=np.uint8)
        count = min(a.size, b.size, valid.size)
        if not count:
            return True
        if self.channel_mask == 3:
            samples = np.empty((count, 2), dtype="<i2")
            samples[:, 0] = a[:count]
            samples[:, 1] = b[:count]
        elif self.channel_mask == 1:
            samples = np.ascontiguousarray(a[:count])
        else:
            samples = np.ascontiguousarray(b[:count])
        first_sample = self._legacy_offset
        self._legacy_offset += count
        valid_bytes = None if bool(np.all(valid[:count])) else valid[:count].tobytes()
        return self._enqueue((
            float(host_time), int(stream_id), int(rate), first_sample, count,
            samples.tobytes(), valid_bytes,
        ), count)

    def close(self, finalize: bool = True):
        with self._state_lock:
            if not self._accepting:
                return
            self._accepting = False
        self.items.put(None)
        self.thread.join()
        if self.error is not None:
            raise self.error
        if finalize and self.output_path is not None:
            self.export_csv(self.output_path)
            Path(self.path).unlink(missing_ok=True)

    def export_csv(self, destination: str | Path,
                   export_mask: int | None = None):
        """Convert the compact spool to CSV without loading it into memory."""
        destination = Path(destination)
        with open(self.path, "rb") as source:
            magic = source.read(len(self.FILE_MAGIC))
            if magic == self.FILE_MAGIC:
                stored_mask_raw = source.read(1)
                if len(stored_mask_raw) != 1:
                    raise ValueError("truncated high-speed recording header")
                stored_mask = stored_mask_raw[0]
            elif magic == self.LEGACY_FILE_MAGIC:
                stored_mask = 3
            else:
                raise ValueError("invalid high-speed recording spool")
            if stored_mask not in (1, 2, 3):
                raise ValueError("invalid recorded channel mask")
            selected_mask = stored_mask if export_mask is None else int(export_mask)
            if selected_mask not in (1, 2, 3) or selected_mask & stored_mask != selected_mask:
                raise ValueError("requested channel was not recorded")
            stored_columns = int(bool(stored_mask & 1)) + int(bool(stored_mask & 2))
            with open(destination, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                columns = [
                    "host_time_s", "stream_id", "sample_rate_hz",
                    "sample_offset",
                ]
                if selected_mask & 1:
                    columns.append("channel_a")
                if selected_mask & 2:
                    columns.append("channel_b")
                columns.append("valid")
                writer.writerow(columns)
                while True:
                    raw_header = source.read(self.RECORD_HEADER.size)
                    if not raw_header:
                        break
                    if len(raw_header) != self.RECORD_HEADER.size:
                        raise ValueError("truncated recording header")
                    host_time, stream_id, rate, first_sample, count, valid_bytes = \
                        self.RECORD_HEADER.unpack(raw_header)
                    payload_size = count * 2 * stored_columns
                    raw_samples = source.read(payload_size)
                    if len(raw_samples) != payload_size:
                        raise ValueError("truncated recording payload")
                    samples = np.frombuffer(raw_samples, dtype="<i2")
                    if stored_columns == 2:
                        samples = samples.reshape(-1, 2)
                    if valid_bytes:
                        raw_valid = source.read(valid_bytes)
                        if len(raw_valid) != valid_bytes:
                            raise ValueError("truncated recording validity map")
                        valid = np.frombuffer(raw_valid, dtype=np.uint8)
                    else:
                        valid = None
                    def csv_row(index):
                        row = [
                            host_time, stream_id, rate, first_sample + index
                        ]
                        if stored_columns == 2:
                            if selected_mask & 1:
                                row.append(int(samples[index, 0]))
                            if selected_mask & 2:
                                row.append(int(samples[index, 1]))
                        else:
                            row.append(int(samples[index]))
                        row.append(1 if valid is None else int(valid[index]))
                        return row

                    writer.writerows(csv_row(index) for index in range(count))


class Hdf5Recorder:
    """Single-channel, loss-aware HDF5 recorder with DLC pro metadata.

    UDP payloads are queued as whole packets.  Decimation, voltage conversion,
    feature extraction and HDF5 writes happen only in the writer thread so the
    receiver thread remains lightweight.
    """

    FORMAT_NAME = "DLCDAQ-HDF5"
    FORMAT_VERSION = 1
    ADC_VOLTS_PER_CODE = 5.0 / 32768.0
    ADC_VOLTAGE_OFFSET = 0.0
    QUEUE_CAPACITY = 32_768
    WRITE_BATCH_PACKETS = 4_096
    WRITE_COALESCE_SECONDS = 0.075

    def __init__(
        self,
        path: str | Path,
        channel: str,
        record_rate_hz: int = 0,
        snapshot_provider=None,
        include_dlcpro: bool = False,
    ):
        normalized_channel = str(channel).strip().upper()
        if normalized_channel not in ("A", "B"):
            raise ValueError("channel must be A or B")
        requested = Path(path)
        self.path = str(
            requested if requested.suffix.lower() == ".h5"
            else requested.with_suffix(".h5")
        )
        self.channel = normalized_channel
        self.channel_index = 0 if normalized_channel == "A" else 1
        self.record_rate_hz = max(0, int(record_rate_hz))
        self.snapshot_provider = snapshot_provider
        self.include_dlcpro = bool(include_dlcpro)
        # Standard-MTU 10 MSPS produces about 28.4k datagrams/s. Keep over a
        # second of elasticity so short HDF5/filesystem stalls cannot push
        # work back into the UDP receive loop.
        self.items: queue.Queue[tuple | None] = queue.Queue(
            maxsize=self.QUEUE_CAPACITY
        )
        self._state_lock = threading.Lock()
        self._snapshot_lock = threading.Lock()
        self._accepting = True
        self._last_snapshot_poll = 0.0
        self._last_snapshot_values = None
        self._dlc_incomplete_reported = False
        self.dropped_samples = 0
        self.written_samples = 0
        self.recorded_index_gap_events = 0
        self.recorded_index_missing_samples = 0
        self.peak_queue_items = 0
        self.writer_batches = 0
        self._last_recorded_source_end: int | None = None
        self.error: Exception | None = None
        self._ready = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self._ready.wait(5.0):
            raise RuntimeError("HDF5 writer did not start within 5 seconds")
        if self.error is not None:
            raise self.error

    @staticmethod
    def _create_series(group, name, dtype, chunk=65_536, **kwargs):
        return group.create_dataset(
            name, shape=(0,), maxshape=(None,), dtype=dtype,
            chunks=(chunk,), **kwargs,
        )

    @staticmethod
    def _append_series(dataset, values):
        values = np.asarray(values, dtype=dataset.dtype)
        start = dataset.shape[0]
        dataset.resize((start + values.size,))
        dataset[start:] = values

    def _create_file(self):
        handle = h5py.File(self.path, "w", libver="latest")
        handle.attrs.update({
            "format": self.FORMAT_NAME,
            "format_version": self.FORMAT_VERSION,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "record_channel": self.channel,
            "requested_record_rate_hz": self.record_rate_hz,
            "adc_voltage_scale_v_per_code": self.ADC_VOLTS_PER_CODE,
            "adc_voltage_offset_v": self.ADC_VOLTAGE_OFFSET,
            "adc_voltage_calibration": (
                "Project conversion: voltage = raw_code * 5/32768. "
                "Keep raw_code as the calibration-independent source of truth."
            ),
            "recording_mode": (
                "waveform_with_dlcpro"
                if self.include_dlcpro else "waveform_only"
            ),
            "dlcpro_metadata_enabled": self.include_dlcpro,
            "dlcpro_metadata_available": False,
            "dlcpro_metadata_complete": False,
        })

        samples = handle.create_group("samples")
        self._datasets = {
            "raw": self._create_series(
                samples, "raw_code", "<i2", compression="lzf", shuffle=True
            ),
            "voltage": self._create_series(
                samples, "voltage_v", "<f4", compression="lzf", shuffle=True
            ),
            "index": self._create_series(
                samples, "sample_index", "<u8", compression="lzf", shuffle=True
            ),
            "valid": self._create_series(
                samples, "valid", "u1", compression="lzf"
            ),
        }
        samples["raw_code"].attrs["unit"] = "ADC code"
        samples["voltage_v"].attrs["unit"] = "V"
        samples["sample_index"].attrs["meaning"] = (
            "Original 64-bit PL sample index; gaps are intentionally preserved."
        )

        packets = handle.create_group("packets")
        for name, dtype in (
            ("host_time_s", "<f8"),
            ("stream_id", "<u4"),
            ("source_sample_rate_hz", "<u4"),
            ("first_sample_index", "<u8"),
            ("source_sample_count", "<u4"),
            ("recorded_sample_count", "<u4"),
            ("decimation_stride", "<u4"),
        ):
            self._datasets[f"packet_{name}"] = self._create_series(
                packets, name, dtype, chunk=4096
            )

        features = handle.create_group("features")
        for name, dtype in (
            ("host_time_s", "<f8"),
            ("first_sample_index", "<u8"),
            ("sample_count", "<u4"),
            ("minimum_v", "<f4"),
            ("maximum_v", "<f4"),
            ("peak_to_peak_v", "<f4"),
            ("mean_v", "<f4"),
            ("rms_v", "<f4"),
        ):
            self._datasets[f"feature_{name}"] = self._create_series(
                features, name, dtype, chunk=4096
            )

        if self.include_dlcpro:
            dlc = handle.create_group("dlcpro")
            string_dtype = h5py.string_dtype(encoding="utf-8")
            for name, dtype in (
                ("host_time_s", "<f8"),
                ("sample_index_anchor", "<u8"),
                ("scan_enabled", "u1"),
                ("scan_offset", "<f8"),
                ("scan_amplitude", "<f8"),
                ("scan_frequency_hz", "<f8"),
                ("scan_output_channel", "<i4"),
                ("scan_signal_type", "<i4"),
                ("scan_unit", string_dtype),
            ):
                self._datasets[f"dlc_{name}"] = self._create_series(
                    dlc, name, dtype, chunk=1024
                )
            dlc.attrs["source"] = (
                "TOPTICA SDK-backed DeviceSnapshot fields from laser1.scan"
            )

        quality = handle.create_group("quality")
        quality.attrs.update({
            "recorder_queue_dropped_samples": 0,
            "recorder_queue_peak_items": 0,
            "recorder_writer_batches": 0,
            "recorded_index_gap_events": 0,
            "recorded_index_missing_samples": 0,
            "network_packets_lost": 0,
            "pl_samples_lost": 0,
            "index_gap_events": 0,
        })
        return handle

    @staticmethod
    def _record_stride(source_rate_hz: int, target_rate_hz: int) -> int:
        if target_rate_hz <= 0 or target_rate_hz >= source_rate_hz:
            return 1
        return max(1, int(round(source_rate_hz / target_rate_hz)))

    def _write_packet_batch(self, items):
        """Convert many UDP packets, then resize each HDF5 dataset only once."""
        sample_batches = {"raw": [], "voltage": [], "index": [], "valid": []}
        packet_batches = {
            name: [] for name in (
                "host_time_s", "stream_id", "source_sample_rate_hz",
                "first_sample_index", "source_sample_count",
                "recorded_sample_count", "decimation_stride",
            )
        }
        feature_batches = {
            name: [] for name in (
                "host_time_s", "first_sample_index", "sample_count",
                "minimum_v", "maximum_v", "peak_to_peak_v", "mean_v",
                "rms_v",
            )
        }

        for item in items:
            host_time, stream_id, source_rate, first_sample, count, payload, valid = item
            pairs = np.frombuffer(payload, dtype="<i2")
            if pairs.size != count * 2:
                raise ValueError("invalid AD9269 packet payload length")
            pairs = pairs.reshape(-1, 2)
            stride = self._record_stride(source_rate, self.record_rate_hz)
            # Select the first index divisible by stride arithmetically. This
            # avoids allocating and testing a full 352-element index/mask for
            # every UDP packet (about 28k times/s with standard MTU at 10 MSPS).
            first_offset = (-first_sample) % stride
            raw = np.ascontiguousarray(
                pairs[first_offset::stride, self.channel_index]
            )
            indices = np.arange(
                first_sample + first_offset,
                first_sample + count,
                stride,
                dtype=np.uint64,
            )
            if valid is None:
                valid_values = np.ones(raw.size, dtype=np.uint8)
            else:
                valid_values = np.asarray(
                    valid, dtype=np.uint8
                )[first_offset::stride]
            voltage = (
                raw.astype(np.float32) * self.ADC_VOLTS_PER_CODE
                + self.ADC_VOLTAGE_OFFSET
            )
            sample_batches["raw"].append(raw)
            sample_batches["voltage"].append(voltage)
            sample_batches["index"].append(indices)
            sample_batches["valid"].append(valid_values)
            self.written_samples += int(raw.size)

            if (self._last_recorded_source_end is not None
                    and first_sample > self._last_recorded_source_end):
                self.recorded_index_gap_events += 1
                self.recorded_index_missing_samples += (
                    first_sample - self._last_recorded_source_end
                )
            self._last_recorded_source_end = max(
                self._last_recorded_source_end or 0,
                first_sample + count,
            )

            packet_values = {
                "host_time_s": host_time,
                "stream_id": stream_id,
                "source_sample_rate_hz": source_rate,
                "first_sample_index": first_sample,
                "source_sample_count": count,
                "recorded_sample_count": raw.size,
                "decimation_stride": stride,
            }
            for name, value in packet_values.items():
                packet_batches[name].append(value)

        combined_samples = {}
        for name, batches in sample_batches.items():
            if batches:
                combined_samples[name] = np.concatenate(batches)
                self._append_series(self._datasets[name], combined_samples[name])
        for name, values in packet_batches.items():
            self._append_series(self._datasets[f"packet_{name}"], values)

        # Peak/mean/RMS are recording summaries, not transport metadata. One
        # feature row per writer batch avoids thousands of NumPy reductions per
        # second while retaining the full raw waveform and packet timeline.
        voltage = combined_samples.get("voltage")
        if voltage is not None and voltage.size:
            valid_values = combined_samples["valid"].astype(bool)
            valid_voltage = voltage[valid_values]
            values = valid_voltage if valid_voltage.size else voltage
            indices = combined_samples["index"]
            feature_values = {
                "host_time_s": items[-1][0],
                "first_sample_index": int(indices[0]),
                "sample_count": voltage.size,
                "minimum_v": float(np.min(values)),
                "maximum_v": float(np.max(values)),
                "peak_to_peak_v": float(np.ptp(values)),
                "mean_v": float(np.mean(values, dtype=np.float64)),
                "rms_v": float(np.sqrt(np.mean(
                    np.square(values.astype(np.float64))
                ))),
            }
            for name, value in feature_values.items():
                feature_batches[name].append(value)
        for name, values in feature_batches.items():
            if values:
                self._append_series(self._datasets[f"feature_{name}"], values)

    def _write_snapshot(self, handle, item):
        host_time, sample_index_anchor, values = item
        names = (
            "scan_enabled", "scan_offset", "scan_amplitude",
            "scan_frequency_hz", "scan_output_channel",
            "scan_signal_type", "scan_unit",
        )
        self._append_series(self._datasets["dlc_host_time_s"], [host_time])
        self._append_series(
            self._datasets["dlc_sample_index_anchor"], [sample_index_anchor]
        )
        for name, value in zip(names, values):
            self._append_series(self._datasets[f"dlc_{name}"], [value])
        handle.attrs["dlcpro_metadata_available"] = True

    def _run(self):
        handle = None
        try:
            handle = self._create_file()
            self._ready.set()
            last_flush = time.monotonic()
            while True:
                queued = self.items.get()
                if queued is None:
                    break
                kind, item = queued
                if kind == "packet":
                    packet_items = [item]
                    deferred = []
                    # Do not immediately write a tiny batch. Coalesce for a
                    # bounded 75 ms so normal 10 MSPS traffic becomes roughly
                    # 10-14 large HDF5 transactions/s rather than thousands of
                    # small resize/compression operations that starve recvfrom.
                    deadline = time.monotonic() + self.WRITE_COALESCE_SECONDS
                    while len(packet_items) < self.WRITE_BATCH_PACKETS:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            break
                        try:
                            following = self.items.get(timeout=remaining)
                        except queue.Empty:
                            break
                        if following is None:
                            deferred.append(None)
                            break
                        following_kind, following_item = following
                        if following_kind == "packet":
                            packet_items.append(following_item)
                        else:
                            deferred.append(following)
                    self.writer_batches += 1
                    self._write_packet_batch(packet_items)
                    for event in deferred:
                        if event is None:
                            queued = None
                            break
                        event_kind, event_item = event
                        if event_kind == "snapshot":
                            self._write_snapshot(handle, event_item)
                        elif event_kind == "quality":
                            handle["quality"].attrs.update(event_item)
                        elif event_kind == "dlc_incomplete":
                            handle.attrs["dlcpro_metadata_complete"] = False
                            handle.attrs["dlcpro_metadata_interruption"] = str(event_item)
                    if queued is None:
                        break
                elif kind == "snapshot":
                    self._write_snapshot(handle, item)
                elif kind == "quality":
                    handle["quality"].attrs.update(item)
                elif kind == "dlc_incomplete":
                    handle.attrs["dlcpro_metadata_complete"] = False
                    handle.attrs["dlcpro_metadata_interruption"] = str(item)
                if time.monotonic() - last_flush >= 1.0:
                    handle.flush()
                    last_flush = time.monotonic()
            handle["quality"].attrs[
                "recorder_queue_dropped_samples"
            ] = self.dropped_samples
            handle["quality"].attrs[
                "recorder_queue_peak_items"
            ] = self.peak_queue_items
            handle["quality"].attrs[
                "recorder_writer_batches"
            ] = self.writer_batches
            handle["quality"].attrs[
                "recorded_index_gap_events"
            ] = self.recorded_index_gap_events
            handle["quality"].attrs[
                "recorded_index_missing_samples"
            ] = self.recorded_index_missing_samples
            handle.attrs["completed_utc"] = datetime.now(timezone.utc).isoformat()
            handle.attrs["written_samples"] = self.written_samples
            if self.include_dlcpro:
                available = bool(handle.attrs["dlcpro_metadata_available"])
                interrupted = "dlcpro_metadata_interruption" in handle.attrs
                handle.attrs["dlcpro_metadata_complete"] = (
                    available and not interrupted
                )
            handle.flush()
        except Exception as exc:
            self.error = exc
        finally:
            self._ready.set()
            if handle is not None:
                handle.close()

    def _enqueue(self, kind: str, item, dropped_count: int = 0) -> bool:
        with self._state_lock:
            if not self._accepting or self.error is not None:
                return False
            try:
                self.items.put_nowait((kind, item))
                self.peak_queue_items = max(
                    self.peak_queue_items, self.items.qsize()
                )
                return True
            except queue.Full:
                self.dropped_samples += int(dropped_count)
                return False

    @staticmethod
    def _snapshot_values(snapshot):
        return (
            bool(snapshot.sc_enabled),
            float(snapshot.sc_offset),
            float(snapshot.sc_amplitude),
            float(snapshot.sc_frequency),
            int(snapshot.sc_output_channel),
            int(snapshot.sc_signal_type),
            str(snapshot.sc_unit),
        )

    def _maybe_append_snapshot(self, host_time: float, sample_index: int):
        if not self.include_dlcpro:
            return
        provider = self.snapshot_provider
        if provider is None:
            return
        now = time.monotonic()
        with self._snapshot_lock:
            if now - self._last_snapshot_poll < 0.1:
                return
            self._last_snapshot_poll = now
        try:
            snapshot = provider()
            if snapshot is None:
                return
            values = self._snapshot_values(snapshot)
        except (AttributeError, TypeError, ValueError):
            return
        with self._snapshot_lock:
            if values == self._last_snapshot_values:
                return
            self._last_snapshot_values = values
        self._enqueue(
            "snapshot", (float(host_time), int(sample_index), values)
        )

    def append_packet(self, host_time: float, packet) -> bool:
        count = int(packet.sample_pair_count)
        if packet.channel_mask != 3 or len(packet.payload) != count * 4:
            self.dropped_samples += count
            return False
        item = (
            float(host_time), int(packet.stream_id),
            int(packet.sample_rate_hz), int(packet.first_sample_pair),
            count, packet.payload, None,
        )
        accepted = self._enqueue("packet", item, count)
        if accepted:
            self._maybe_append_snapshot(host_time, packet.first_sample_pair)
        return accepted

    def update_quality(self, metrics: dict):
        values = {
            "network_packets_lost": int(
                metrics.get("network_packet_loss", 0)
            ),
            "pl_samples_lost": int(metrics.get("pl_sample_gap", 0)),
            "index_gap_events": int(metrics.get("index_gap_events", 0)),
        }
        self._enqueue("quality", values)

    def mark_dlcpro_incomplete(self, reason: str):
        if not self.include_dlcpro:
            return
        with self._snapshot_lock:
            if self._dlc_incomplete_reported:
                return
            self._dlc_incomplete_reported = True
        self._enqueue("dlc_incomplete", str(reason))

    def close(self):
        with self._state_lock:
            if not self._accepting:
                return
            self._accepting = False
        self.items.put(None)
        self.thread.join()
        if self.error is not None:
            raise self.error


class EnvelopePlot(QWidget):
    def __init__(self, color: str):
        super().__init__()
        self.setObjectName("scopePlot")
        self.minimum = np.empty(0)
        self.maximum = np.empty(0)
        self.valid = np.empty(0, dtype=bool)
        self.color = QColor(color)
        self.fixed_bounds: tuple[float, float] | None = None
        self.value_scale = 1.0
        self.value_offset = 0.0
        self.auto_minimum_half_span = 16.0
        self.vertical_scale_multiplier = 1.0
        self.trigger_enabled = False
        self.trigger_locked = False
        self.smoothing = False
        self.plot_mode = "trace"
        self._display_signature = None
        self._auto_bounds_state: tuple[float, float] | None = None
        self._auto_bounds_time: float | None = None
        self.seconds_per_div = 50e-6
        self.axis_unit = "V"
        self.setMinimumSize(720, 340)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_display(self, scale: float, offset: float,
                    fixed_bounds: tuple[float, float] | None,
                    auto_minimum_half_span: float = 16.0,
                    vertical_scale_multiplier: float = 1.0):
        signature = (
            float(scale), float(offset), fixed_bounds,
            max(float(auto_minimum_half_span), 1e-12),
            min(8.0, max(0.001, float(vertical_scale_multiplier))),
        )
        changed = signature != self._display_signature
        if changed:
            self._auto_bounds_state = None
            self._auto_bounds_time = None
            self._display_signature = signature
        self.value_scale = float(scale)
        self.value_offset = float(offset)
        self.fixed_bounds = fixed_bounds
        self.auto_minimum_half_span = signature[3]
        self.vertical_scale_multiplier = signature[4]
        if changed:
            # Range changes must update the grid labels immediately, including
            # while acquisition is stopped and no new frame is arriving.
            self.update()

    def set_axes(self, seconds_per_div: float, unit: str):
        seconds_per_div = max(1e-12, float(seconds_per_div))
        unit = str(unit)
        if (seconds_per_div, unit) != (self.seconds_per_div, self.axis_unit):
            self.seconds_per_div = seconds_per_div
            self.axis_unit = unit
            self.update()

    @staticmethod
    def _time_axis_scale(seconds_per_div: float) -> tuple[float, str]:
        seconds_per_div = abs(float(seconds_per_div))
        if seconds_per_div < 1e-3:
            return 1e6, "µs"
        if seconds_per_div < 1.0:
            return 1e3, "ms"
        return 1.0, "s"

    @staticmethod
    def _axis_number(value: float) -> str:
        magnitude = abs(float(value))
        if magnitude >= 1000:
            return f"{value:.4g}"
        if magnitude >= 10:
            return f"{value:.3g}"
        if magnitude >= 1:
            return f"{value:.3f}".rstrip("0").rstrip(".")
        if magnitude >= 1e-3:
            return f"{value:.4f}".rstrip("0").rstrip(".")
        return f"{value:.3g}"

    def _plot_rect(self) -> QRectF:
        return QRectF(
            72.0,
            12.0,
            max(1.0, self.width() - 88.0),
            max(1.0, self.height() - 48.0),
        )

    def set_envelope(self, minimum, maximum, valid):
        first = np.asarray(minimum, dtype=np.float32) * self.value_scale + self.value_offset
        second = np.asarray(maximum, dtype=np.float32) * self.value_scale + self.value_offset
        self.minimum = np.minimum(first, second)
        self.maximum = np.maximum(first, second)
        self.valid = valid
        self.update()

    def set_trigger_state(self, enabled: bool, locked: bool):
        self.trigger_enabled = bool(enabled)
        self.trigger_locked = bool(locked)

    def set_smoothing(self, enabled: bool):
        self.smoothing = bool(enabled)
        self.update()

    def set_plot_mode(self, mode: str):
        mode = str(mode)
        self.plot_mode = mode if mode in ("trace", "points", "envelope") else "trace"
        self.update()

    @staticmethod
    def _smooth_path(points):
        """Create a Catmull-Rom style cubic path through real sample points."""
        path = QPainterPath()
        if not points:
            return path
        path.moveTo(*points[0])
        if len(points) == 1:
            return path
        if len(points) == 2:
            path.lineTo(*points[1])
            return path
        for index in range(len(points) - 1):
            p0 = points[max(0, index - 1)]
            p1 = points[index]
            p2 = points[index + 1]
            p3 = points[min(len(points) - 1, index + 2)]
            c1x = p1[0] + (p2[0] - p0[0]) / 6.0
            c1y = p1[1] + (p2[1] - p0[1]) / 6.0
            c2x = p2[0] - (p3[0] - p1[0]) / 6.0
            c2y = p2[1] - (p3[1] - p1[1]) / 6.0
            path.cubicTo(c1x, c1y, c2x, c2y, p2[0], p2[1])
        return path

    @staticmethod
    def _display_bounds(
        minimum,
        maximum,
        valid,
        minimum_half_span: float = 16.0,
        vertical_scale: float = 1.0,
    ):
        if not np.any(valid):
            return -1.0, 1.0
        # Desktop/ZYNQ reference design: use the true visible extrema so a
        # narrow transmission peak is never discarded by robust statistics.
        low = float(np.min(minimum[valid]))
        high = float(np.max(maximum[valid]))
        center = (low + high) * 0.5
        span = max(0.0, high - low)
        scale = min(8.0, max(0.001, float(vertical_scale)))
        half_span = max(float(minimum_half_span), span * 0.55) * scale
        half_span = max(half_span, 1e-12)
        return center - half_span, center + half_span

    def _stabilize_auto_bounds(
        self, target: tuple[float, float], now: float | None = None,
    ) -> tuple[float, float]:
        """Expand immediately but contract slowly to prevent range flicker."""
        now = time.monotonic() if now is None else float(now)
        if self._auto_bounds_state is None or self._auto_bounds_time is None:
            self._auto_bounds_state = target
            self._auto_bounds_time = now
            return target
        elapsed = min(0.25, max(0.0, now - self._auto_bounds_time))
        # Roughly 0.8 s time constant: fast enough to follow a changing
        # baseline, slow enough that peaks leaving a rolling window do not
        # make the entire trace flash larger on the next frame.
        alpha = 1.0 - np.exp(-elapsed / 0.8)
        old_low, old_high = self._auto_bounds_state
        target_low, target_high = target
        low = (
            target_low if target_low < old_low
            else old_low + (target_low - old_low) * alpha
        )
        high = (
            target_high if target_high > old_high
            else old_high + (target_high - old_high) * alpha
        )
        self._auto_bounds_state = (float(low), float(high))
        self._auto_bounds_time = now
        return self._auto_bounds_state

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#08111f"))
        plot_rect = self._plot_rect()
        painter.setPen(QPen(QColor("#2c405e"), 1))
        for division in range(0, 11):
            x = plot_rect.left() + division * plot_rect.width() / 10
            painter.drawLine(
                QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom())
            )
        for division in range(0, 9):
            y = plot_rect.top() + division * plot_rect.height() / 8
            painter.drawLine(
                QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y)
            )

        if self.fixed_bounds is None:
            if self.minimum.size and np.any(self.valid):
                low, high = self._stabilize_auto_bounds(
                    self._display_bounds(
                        self.minimum, self.maximum, self.valid,
                        self.auto_minimum_half_span,
                        self.vertical_scale_multiplier,
                    )
                )
            else:
                low, high = -1.0, 1.0
        else:
            low, high = self.fixed_bounds

        painter.setPen(QColor("#9fb0c5"))
        painter.drawText(8, 18, "电压 (V)" if self.axis_unit == "V" else "ADC code")
        for division in range(0, 9):
            y = plot_rect.top() + division * plot_rect.height() / 8
            value = high - division * (high - low) / 8
            label_rect = QRectF(2, y - 9, 64, 18)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter,
                             self._axis_number(value))
        time_scale, time_unit = self._time_axis_scale(self.seconds_per_div)
        for division in range(0, 11):
            x = plot_rect.left() + division * plot_rect.width() / 10
            seconds = (division - 10) * self.seconds_per_div
            label_rect = QRectF(x - 31, plot_rect.bottom() + 4, 62, 18)
            painter.drawText(label_rect, Qt.AlignHCenter | Qt.AlignTop,
                             self._axis_number(seconds * time_scale))
        painter.drawText(
            QRectF(plot_rect.right() - 120, self.height() - 21, 120, 18),
            Qt.AlignRight | Qt.AlignVCenter,
            f"时间 ({time_unit})",
        )
        if self.trigger_enabled:
            trigger_x = int(plot_rect.left() + plot_rect.width() * 0.25)
            color = QColor("#22c55e" if self.trigger_locked else "#f59e0b")
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.drawLine(trigger_x, int(plot_rect.top()),
                             trigger_x, int(plot_rect.bottom()))
            painter.setPen(color)
            painter.drawText(trigger_x + 5, int(plot_rect.top()) + 16,
                             "TRIG" if self.trigger_locked else "WAIT")
        if not self.minimum.size:
            painter.setPen(QColor("#8190a5"))
            painter.drawText(plot_rect, Qt.AlignCenter, "等待 PL UDP 数据")
            return
        envelope_color = QColor(self.color)
        envelope_color.setAlpha(130)
        trace_color = QColor(self.color)
        count = len(self.minimum)
        # Interpolation is only used when each horizontal bin represents one
        # real sample. For reduced min/max envelopes it would invent a center
        # trace and conceal real extrema.
        smooth_trace = (
            self.smoothing and count <= 200 and np.any(self.valid) and
            np.array_equal(
                self.minimum[self.valid], self.maximum[self.valid]
            )
        )
        valid_indices = np.flatnonzero(self.valid)
        if not valid_indices.size:
            return
        x_values = np.rint(
            valid_indices.astype(np.float64)
            * plot_rect.width() / max(1, count - 1) + plot_rect.left()
        ).astype(np.int32)
        y0_values = np.rint(
            (high - self.minimum[valid_indices].astype(np.float64))
            * plot_rect.height() / (high - low) + plot_rect.top()
        ).astype(np.int32)
        y1_values = np.rint(
            (high - self.maximum[valid_indices].astype(np.float64))
            * plot_rect.height() / (high - low) + plot_rect.top()
        ).astype(np.int32)
        midpoint_y = (y0_values + y1_values) // 2

        # One invalid source bin starts a new segment. Building one Qt path
        # per frame avoids hundreds of Python-to-QPainter calls while keeping
        # real UDP/PL sample gaps visibly disconnected.
        segment_starts = np.r_[
            0, np.flatnonzero(np.diff(valid_indices) > 1) + 1
        ]
        segment_ends = np.r_[segment_starts[1:], valid_indices.size]

        painter.save()
        painter.setClipRect(plot_rect)
        if self.plot_mode == "envelope":
            path = QPainterPath()
            for x, y0, y1 in zip(x_values, y0_values, y1_values):
                path.moveTo(float(x), float(y0))
                path.lineTo(float(x), float(y1))
            painter.setPen(QPen(envelope_color, 1))
            painter.drawPath(path)
        elif self.plot_mode == "points":
            points = QPolygonF([
                QPointF(float(x), float(y))
                for x, y in zip(x_values, midpoint_y)
            ])
            painter.setPen(QPen(trace_color, 2))
            painter.drawPoints(points)
        elif smooth_trace:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(trace_color, 1))
            combined = QPainterPath()
            for start, end in zip(segment_starts, segment_ends):
                segment = list(zip(
                    x_values[start:end].tolist(),
                    midpoint_y[start:end].tolist(),
                ))
                combined.addPath(self._smooth_path(segment))
            painter.drawPath(combined)
        else:
            # QPainterPath.lineTo() is exceptionally slow for a live trace on
            # the Windows raster backend.  A polygon submits each continuous
            # run in one Qt call and keeps real sample gaps disconnected.
            # A two-pixel polyline is over an order of magnitude slower on the
            # Windows raster backend because every sharp ADC turn needs a wide
            # join.  A cosmetic one-pixel trace remains crisp and real-time.
            painter.setPen(QPen(trace_color, 1))
            for start, end in zip(segment_starts, segment_ends):
                if end - start <= 0:
                    continue
                polygon = QPolygonF([
                    QPointF(float(x), float(y))
                    for x, y in zip(
                        x_values[start:end], midpoint_y[start:end]
                    )
                ])
                if polygon.size() == 1:
                    painter.drawPoints(polygon)
                else:
                    painter.drawPolyline(polygon)
        painter.restore()


class ScopeWindow(QWidget):
    settings_changed = Signal()
    time_settings_changed = Signal()
    focus_requested = Signal(str)

    def __init__(self, channel: str, color: str, parent=None, *, embedded=False):
        super().__init__(parent)
        self.channel = channel
        self.adc_model = 0
        self.frozen = False
        self.trigger_locked = False
        self._last_trigger_visual: str | None = None
        self._last_caption_update = 0.0
        self.setWindowTitle(f"通道 {channel} 示波器")
        if not embedded:
            self.setStyleSheet(SCOPE_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        toolbar = QFrame()
        toolbar.setObjectName("scopeToolbar")
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(14, 10, 14, 10)
        toolbar_layout.setSpacing(8)
        heading = QHBoxLayout()
        channel_dot = QLabel("●")
        channel_dot.setStyleSheet(f"color:{color};font-size:16px")
        if embedded:
            channel_title = QPushButton(f"通道 {channel}  ·  单通道查看")
            channel_title.setObjectName("scopeChannelButton")
            channel_title.setCursor(Qt.PointingHandCursor)
            channel_title.setToolTip(f"在当前窗口中放大通道 {channel}")
            channel_title.clicked.connect(
                lambda _checked=False, name=channel: self.focus_requested.emit(name)
            )
            self.focus_button = channel_title
        else:
            channel_title = QLabel(f"通道 {channel}")
            channel_title.setObjectName("scopeChannel")
            self.focus_button = None
        heading.addWidget(channel_dot)
        heading.addWidget(channel_title)
        heading.addStretch(1)
        toolbar_layout.addLayout(heading)
        controls = QGridLayout()
        controls.setHorizontalSpacing(8)
        controls.setVerticalSpacing(7)
        self.timebase = QComboBox()
        for label, seconds in TIMEBASES_PER_DIV:
            self.timebase.addItem(label, seconds)
        self.timebase.setCurrentText("50 µs/div")
        self.fps = QComboBox()
        for value in DISPLAY_FPS_OPTIONS:
            self.fps.addItem(f"{value} FPS", value)
        self.fps.setCurrentText(f"{DISPLAY_FPS} FPS")
        self.scroll_speed = QComboBox()
        for label, divisor in SCROLL_DIVISORS:
            self.scroll_speed.addItem(label, divisor)
        self.units = QComboBox()
        self.y_range = QComboBox()
        self.trigger_mode = QComboBox()
        self.trigger_mode.addItem("自由运行", "off")
        self.trigger_mode.addItem("上升沿", "rising")
        self.trigger_mode.addItem("下降沿", "falling")
        self.trigger_level = QDoubleSpinBox()
        self.trigger_level.setDecimals(3)
        self.trigger_level.setKeyboardTracking(False)
        self.trigger_level.setMinimumWidth(92)
        self.trigger_status = QLabel("FREE")
        self.trigger_status.setObjectName("triggerWaiting")
        self.smoothing = VisibleCheckBox("插值平滑")
        self.smoothing.setChecked(False)
        self.smoothing.setToolTip(
            "只平滑屏幕连线，不改变真实采样点、网络数据或 CSV"
        )
        self.display_mode = QComboBox()
        self.display_mode.addItem("普通波形", "trace")
        self.display_mode.addItem("离散点", "points")
        self.display_mode.addItem("峰值包络", "envelope")
        self.display_mode.setToolTip(
            "普通波形连接压缩后的代表点；离散点完全不连线；"
            "峰值包络显示每个时间段的真实最小值和最大值"
        )
        self.freeze_button = QPushButton("暂停显示")
        self.freeze_button.setCheckable(True)
        self.vertical_scale = QDoubleSpinBox()
        self.vertical_scale.setRange(0.001, 8.0)
        self.vertical_scale.setDecimals(3)
        self.vertical_scale.setSingleStep(0.05)
        self.vertical_scale.setValue(1.0)
        self.vertical_scale.setSuffix(" ×")
        self.vertical_scale.setToolTip(
            "仅调整当前通道的显示纵轴倍率，不改变ADC原始数据"
        )
        self.controls_layout = controls
        self.control_labels = {
            key: QLabel(text) for key, text in (
                ("timebase", "时基"), ("fps", "帧率"),
                ("scroll", "滚动"), ("units", "纵轴"),
                ("range", "范围"), ("scale", "Y倍率"),
                ("trigger", "触发"), ("level", "电平"),
                ("display", "显示"),
            )
        }
        # Attach the layout before reflow calls show()/hide().  Otherwise its
        # still-parentless controls briefly become native top-level windows.
        toolbar_layout.addLayout(controls)
        self.set_compact_controls(embedded)
        self.caption = QLabel(f"通道 {channel}：--")
        self.caption.setObjectName("scopeCaption")
        self.plot = EnvelopePlot(color)
        readout = QFrame()
        readout.setObjectName("scopeReadout")
        readout_layout = QHBoxLayout(readout)
        readout_layout.setContentsMargins(14, 8, 14, 8)
        readout_layout.addWidget(self.caption)
        layout.addWidget(toolbar)
        layout.addWidget(readout)
        layout.addWidget(self.plot, 1)
        if embedded:
            self.plot.setMinimumSize(320, 220)
        else:
            self.resize(1040, 650)

        # The two channels share one sampled time axis, so only horizontal
        # display controls are linked.  Vertical scaling and trigger/display
        # choices remain local to each scope window.
        self.timebase.currentIndexChanged.connect(self.time_settings_changed)
        self.timebase.currentIndexChanged.connect(self._update_axes)
        self.fps.currentIndexChanged.connect(self.time_settings_changed)
        self.scroll_speed.currentIndexChanged.connect(self.time_settings_changed)
        self.units.currentIndexChanged.connect(self._display_changed)
        self.y_range.currentIndexChanged.connect(self._range_changed)
        self.vertical_scale.valueChanged.connect(self._range_changed)
        self.trigger_mode.currentIndexChanged.connect(self._trigger_changed)
        self.trigger_level.valueChanged.connect(self._trigger_changed)
        self.display_mode.currentIndexChanged.connect(
            self._display_mode_changed
        )
        self.smoothing.toggled.connect(self._smoothing_changed)
        self.freeze_button.toggled.connect(self._freeze_changed)
        self.plot.set_smoothing(self.smoothing.isChecked())
        self.plot.set_plot_mode(self.display_mode.currentData())
        self.configure_model(1)

    def _update_axes(self):
        self.plot.set_axes(
            float(self.timebase.currentData() or 50e-6),
            "ADC code" if self.units.currentData() == "raw" else "V",
        )

    def set_compact_controls(self, compact: bool):
        """Reflow controls for half-width combined or full-width scope mode."""
        if hasattr(self, "plot"):
            self.plot.setMinimumSize(
                320 if compact else 720,
                220 if compact else 340,
            )
        controls = self.controls_layout
        while controls.count():
            item = controls.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
        for column in range(12):
            controls.setColumnStretch(column, 0)

        fields = {
            "timebase": self.timebase,
            "fps": self.fps,
            "scroll": self.scroll_speed,
            "units": self.units,
            "range": self.y_range,
            "scale": self.vertical_scale,
            "trigger": self.trigger_mode,
            "level": self.trigger_level,
            "display": self.display_mode,
        }
        if compact:
            rows = (
                (("timebase", fields["timebase"]), ("fps", fields["fps"])),
                (("scroll", fields["scroll"]), ("units", fields["units"])),
                (("range", fields["range"]), ("scale", fields["scale"])),
                (("trigger", fields["trigger"]), ("level", fields["level"])),
                (("display", fields["display"]),),
            )
            for row, pairs in enumerate(rows):
                for column, (key, widget) in enumerate(pairs):
                    controls.addWidget(self.control_labels[key], row, column * 2)
                    controls.addWidget(widget, row, column * 2 + 1)
            controls.addWidget(self.trigger_status, 3, 4)
            controls.addWidget(self.smoothing, 4, 2)
            controls.addWidget(self.freeze_button, 4, 4)
            controls.setColumnStretch(4, 1)
        else:
            for column, key in enumerate((
                "timebase", "fps", "scroll", "units", "range",
            )):
                controls.addWidget(self.control_labels[key], 0, column * 2)
                controls.addWidget(fields[key], 0, column * 2 + 1)
            controls.addWidget(self.control_labels["trigger"], 1, 0)
            controls.addWidget(self.trigger_mode, 1, 1)
            controls.addWidget(self.control_labels["level"], 1, 2)
            controls.addWidget(self.trigger_level, 1, 3)
            controls.addWidget(self.trigger_status, 1, 4, 1, 2)
            controls.addWidget(self.control_labels["display"], 1, 6)
            controls.addWidget(self.display_mode, 1, 7)
            controls.addWidget(self.smoothing, 1, 8)
            controls.addWidget(self.control_labels["scale"], 1, 9)
            controls.addWidget(self.vertical_scale, 1, 10)
            controls.addWidget(self.freeze_button, 1, 11)
            controls.setColumnStretch(11, 1)

        for widget in (
            *self.control_labels.values(), *fields.values(),
            self.trigger_status, self.smoothing, self.freeze_button,
        ):
            widget.show()
        controls.invalidate()
        self.updateGeometry()

    def configure_model(self, model: int):
        self.adc_model = int(model)
        previous = self.units.currentData()
        self.units.blockSignals(True)
        self.units.clear()
        self.units.addItem("原始 ADC 码", "raw")
        self.units.addItem("模块输入电压 ±5 V", "module")
        index = self.units.findData(previous)
        self.units.setCurrentIndex(index if index >= 0 else min(1, self.units.count() - 1))
        self.units.blockSignals(False)
        self._rebuild_y_ranges()

    def _rebuild_y_ranges(self):
        previous = self.y_range.currentData()
        voltage_mode = self.units.currentData() != "raw"
        self.control_labels["range"].setText(
            "电压范围" if voltage_mode else "ADC范围"
        )
        self.y_range.blockSignals(True)
        self.y_range.clear()
        self.y_range.addItem("自动", "auto")
        if not voltage_mode:
            self.y_range.addItem("满量程（±32768 code）", "full")
            for value in (10_000.0, 5_000.0, 2_000.0, 1_000.0,
                          500.0, 200.0, 100.0, 50.0, 20.0, 10.0):
                self.y_range.addItem(f"±{value:g} code", value)
        else:
            self.y_range.addItem("满量程（±5 V）", "full")
            for value in (
                5.0, 2.0, 1.0, .5, .2, .1, .05, .02, .01,
                .005, .002, .001, .0005, .0002, .0001,
            ):
                text = (
                    f"±{value:g} V" if value >= .1
                    else f"±{value * 1000:g} mV"
                )
                self.y_range.addItem(text, value)
        index = self.y_range.findData(previous)
        self.y_range.setCurrentIndex(index if index >= 0 else 0)
        self.y_range.blockSignals(False)
        self._apply_display()

    def _display_changed(self):
        self._rebuild_y_ranges()
        self.settings_changed.emit()

    def _range_changed(self):
        self._apply_display()
        self.settings_changed.emit()

    def _freeze_changed(self, checked: bool):
        self.frozen = bool(checked)
        self.freeze_button.setText("继续显示" if checked else "暂停显示")
        self.freeze_button.setToolTip(
            "只暂停绘图；UDP接收与CSV录制继续运行" if checked
            else "暂停当前波形显示，后台采集不停止"
        )

    def _trigger_changed(self):
        enabled = self.trigger_mode.currentData() != "off"
        self.trigger_level.setEnabled(enabled)
        self.trigger_status.setText("WAIT" if enabled else "FREE")
        self.trigger_status.setObjectName(
            "triggerWaiting" if enabled else "scopeCaption"
        )
        self.trigger_status.style().unpolish(self.trigger_status)
        self.trigger_status.style().polish(self.trigger_status)
        self.settings_changed.emit()

    def _smoothing_changed(self, checked: bool):
        self.plot.set_smoothing(checked)
        self.settings_changed.emit()

    def _display_mode_changed(self):
        mode = str(self.display_mode.currentData() or "trace")
        self.plot.set_plot_mode(mode)
        self.smoothing.setEnabled(mode == "trace")
        self.settings_changed.emit()

    def _apply_display(self):
        mode = self.units.currentData()
        if mode == "adc":
            scale, offset, full = 2.0 / 255.0, 0.0, (0.0, 2.0)
        elif mode == "module" and not self.adc_model:
            scale, offset, full = 10.0 / 255.0, -5.0, (-5.0, 5.0)
        elif mode == "module":
            scale, offset, full = 5.0 / 32768.0, 0.0, (-5.0, 5.0)
        elif self.adc_model:
            scale, offset, full = 1.0, 0.0, (-32768.0, 32767.0)
        else:
            scale, offset, full = 1.0, 0.0, (0.0, 255.0)
        previous_level = self.trigger_level.value()
        self.trigger_level.blockSignals(True)
        self.trigger_level.setRange(float(full[0]), float(full[1]))
        self.trigger_level.setSingleStep(max(0.001, (full[1] - full[0]) / 200.0))
        self.trigger_level.setSuffix(
            " code" if mode == "raw" else " V"
        )
        if previous_level < full[0] or previous_level > full[1]:
            self.trigger_level.setValue((full[0] + full[1]) / 2.0)
        self.trigger_level.blockSignals(False)
        selected = self.y_range.currentData()
        if selected == "auto":
            bounds = None
        elif selected == "full" or selected is None:
            center = (full[0] + full[1]) * 0.5
            half_span = (full[1] - full[0]) * 0.5 * self.vertical_scale.value()
            bounds = (center - half_span, center + half_span)
        else:
            center = (full[0] + full[1]) / 2.0
            # Numeric entries represent the complete visible voltage/code
            # half-range directly (±value), not a per-division value.
            half_span = float(selected) * self.vertical_scale.value()
            bounds = (center - half_span, center + half_span)
        auto_minimum_half_span = 16.0 * abs(scale)
        self.plot.set_display(
            scale,
            offset,
            bounds,
            auto_minimum_half_span,
            self.vertical_scale.value(),
        )
        self._update_axes()

    def required_samples(self, rate: float) -> int:
        seconds_per_div = float(self.timebase.currentData() or 50e-6)
        # At 20 MSPS, 0.1 us/div is a 20-sample window. Keeping that short
        # window intact is essential for viewing a 5 MHz waveform rather than
        # compressing many cycles into a min/max band.
        return max(16, int(max(1.0, rate) * seconds_per_div * 10.0))

    @property
    def refresh_fps(self) -> int:
        return int(self.fps.currentData() or DISPLAY_FPS)

    @property
    def scroll_divisor(self) -> int:
        return int(self.scroll_speed.currentData() or 1)

    @property
    def trigger_config(self):
        mode = self.trigger_mode.currentData()
        if mode == "off":
            return None
        raw_level = ((self.trigger_level.value() - self.plot.value_offset) /
                     self.plot.value_scale)
        return (0 if self.channel == "A" else 1,
                float(raw_level), mode == "rising")

    @staticmethod
    def _set_combo_data(combo: QComboBox, value):
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def restore_settings(self, settings: QSettings, prefix: str):
        self._set_combo_data(
            self.timebase, float(settings.value(
                f"{prefix}/timebase", self.timebase.currentData()))
        )
        self._set_combo_data(
            self.fps, int(settings.value(
                f"{prefix}/fps", self.fps.currentData()))
        )
        self._set_combo_data(
            self.scroll_speed, int(settings.value(
                f"{prefix}/scroll", self.scroll_speed.currentData()))
        )
        self._set_combo_data(
            self.units, settings.value(
                f"{prefix}/units", self.units.currentData())
        )
        self._set_combo_data(
            self.y_range, settings.value(
                f"{prefix}/range", self.y_range.currentData())
        )
        self._set_combo_data(
            self.trigger_mode, settings.value(
                f"{prefix}/trigger_mode", "off")
        )
        self._set_combo_data(
            self.display_mode, settings.value(
                f"{prefix}/display_mode", "trace")
        )
        self.smoothing.setChecked(
            str(settings.value(
                f"{prefix}/smoothing", "false"
            )).lower() in ("1", "true", "yes")
        )
        self.trigger_level.setValue(float(settings.value(
            f"{prefix}/trigger_level", self.trigger_level.value())))
        self.vertical_scale.setValue(float(settings.value(
            f"{prefix}/vertical_scale", 1.0)))
        self._apply_display()

    def save_settings(self, settings: QSettings, prefix: str):
        settings.setValue(f"{prefix}/timebase", self.timebase.currentData())
        settings.setValue(f"{prefix}/fps", self.fps.currentData())
        settings.setValue(f"{prefix}/scroll", self.scroll_speed.currentData())
        settings.setValue(f"{prefix}/units", self.units.currentData())
        settings.setValue(f"{prefix}/range", self.y_range.currentData())
        settings.setValue(
            f"{prefix}/trigger_mode", self.trigger_mode.currentData()
        )
        settings.setValue(
            f"{prefix}/display_mode", self.display_mode.currentData()
        )
        settings.setValue(f"{prefix}/smoothing", self.smoothing.isChecked())
        settings.setValue(
            f"{prefix}/trigger_level", self.trigger_level.value()
        )
        settings.setValue(
            f"{prefix}/vertical_scale", self.vertical_scale.value()
        )

    def update_data(self, minimum, maximum, valid, rate,
                    trigger_locked: bool | None = None):
        if self.frozen:
            return
        enabled = self.trigger_mode.currentData() != "off"
        self.trigger_locked = bool(trigger_locked) if enabled else False
        self.plot.set_trigger_state(enabled, self.trigger_locked)
        if enabled:
            visual = "LOCK" if self.trigger_locked else "WAIT"
            object_name = (
                "triggerLocked" if self.trigger_locked else "triggerWaiting"
            )
        else:
            visual = "FREE"
            object_name = "scopeCaption"
        if visual != self._last_trigger_visual:
            self._last_trigger_visual = visual
            self.trigger_status.setText(visual)
            self.trigger_status.setObjectName(object_name)
            self.trigger_status.style().unpolish(self.trigger_status)
            self.trigger_status.style().polish(self.trigger_status)
        self.plot.set_envelope(minimum, maximum, valid)
        now = time.monotonic()
        if np.any(valid) and now - self._last_caption_update >= 0.1:
            self._last_caption_update = now
            valid_indices = np.flatnonzero(valid)
            last = int(valid_indices[-1])
            current_code = (float(minimum[last]) + float(maximum[last])) / 2.0
            current = current_code * self.plot.value_scale + self.plot.value_offset
            valid_min = float(np.min(minimum[valid])) * self.plot.value_scale + self.plot.value_offset
            valid_max = float(np.max(maximum[valid])) * self.plot.value_scale + self.plot.value_offset
            unit = "code" if self.units.currentData() == "raw" else "V"
            span = float(self.timebase.currentData() or 0.0) * 10.0
            window_text = (
                f"{span:.3f} s" if span >= 1.0
                else f"{span * 1e3:.3f} ms"
            )
            self.caption.setText(
                f"实测速率 {rate / 1e6:.3f} MSPS    窗口 {window_text}    "
                f"当前 {current:.4g} {unit}    最小 {min(valid_min, valid_max):.4g}    "
                f"最大 {max(valid_min, valid_max):.4g}"
            )


class MainWindow(QMainWindow):
    def __init__(self, preset_model: int | None = None,
                 settings: QSettings | None = None,
                 snapshot_provider=None,
                 dlc_service=None,
                 snapshot_consumer=None,
                 falc_window_opener=None):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowTitle("Zynq-7020 双 ADC 采集卡")
        self.resize(1280, 760)
        self.setMinimumSize(1100, 640)
        self.setStyleSheet(APP_STYLE)
        self.settings = settings or QSettings(
            "ZynqDAQ", "DualADCMonitor"
        )
        self._closing = False
        self.fpga_programmer: FpgaProgrammer | None = None
        self.fpga_program_output: list[str] = []
        self.fpga_bit_path: Path | None = None
        self.snapshot_provider = snapshot_provider
        self.falc_window_opener = falc_window_opener
        self.dlc_session = DlcScanSession(
            service=dlc_service,
            owns_service=dlc_service is None,
            snapshot_provider=snapshot_provider,
            parent=self,
        )
        self.dlc_settings_dialog: DlcProSettingsDialog | None = None
        self.ring = DualSampleRingBuffer()
        self.control: ControlClient | None = None
        self.receiver: UdpDualReceiver | None = None
        self.poller: StatusPoller | None = None
        self.acquisition_starter: AcquisitionStarter | None = None
        self.stream_id: int | None = None
        self.metrics = {}
        self.latest_status = None
        self.recorder: Hdf5Recorder | None = None
        self.record_temp_path: Path | None = None
        self.record_mode = "a"
        self.record_metadata_mode = str(self.settings.value(
            "record/content_mode",
            RecordingOptionsDialog.WAVEFORM_ONLY,
        ))
        self.record_dropped = 0
        self.last_event_count = 0
        self.last_event_time = time.monotonic()
        self.event_rate = 0.0
        self.plot_tick = 0
        # A and B are independent top-level instruments. Their controls are
        # fully laid out before either window is shown, avoiding transient
        # native child windows during ADC-page construction.
        self.scope_a = ScopeWindow("A", "#22d3ee")
        self.scope_b = ScopeWindow("B", "#fb7185")
        # Compatibility for launchers that used the former combined member.
        self.scope_window = self.scope_a

        scroll = QScrollArea()
        scroll.setObjectName("appScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        root = QWidget()
        root.setObjectName("appRoot")
        scroll.setWidget(root)
        self.setCentralWidget(scroll)
        page = QVBoxLayout(root)
        page.setContentsMargins(24, 20, 24, 22)
        page.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("hero")
        header = QHBoxLayout(hero)
        header.setContentsMargins(22, 16, 22, 16)
        header.setSpacing(16)
        heading = QVBoxLayout()
        heading.setSpacing(1)
        eyebrow = QLabel("ZYNQ-7020  ·  PL UDP ACQUISITION")
        eyebrow.setObjectName("heroEyebrow")
        title = QLabel("双 ADC 实时采集")
        title.setObjectName("heroTitle")
        subtitle = QLabel("PL 网口实时波形 · PS DDR 峰事件 · 双控制面")
        subtitle.setObjectName("heroSubtitle")
        heading.addWidget(eyebrow)
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch(1)
        self.connection_pill = QLabel("●  未连接")
        self.connection_pill.setObjectName("statePill")
        self.connection_pill.setProperty("state", "idle")
        header.addWidget(self.connection_pill, 0, Qt.AlignVCenter)
        page.addWidget(hero)

        panel = QFrame()
        panel.setObjectName("card")
        panel.setMinimumHeight(184)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 15, 18, 16)
        panel_layout.setSpacing(11)
        panel_title = QLabel("采集配置")
        panel_title.setObjectName("sectionTitle")
        panel_layout.addWidget(panel_title)
        config_grid = QGridLayout()
        config_grid.setHorizontalSpacing(14)
        config_grid.setVerticalSpacing(11)
        config_grid.setColumnStretch(1, 1)
        config_grid.setColumnStretch(3, 1)
        config_grid.setRowMinimumHeight(0, 38)
        config_grid.setRowMinimumHeight(1, 38)
        config_grid.setRowMinimumHeight(2, 38)
        self.board_ip = QLineEdit(PL_BOARD_IP)
        self.model = QComboBox()
        self.model.addItem("AD9269（J24，S16 A/B）", 1)
        self.model.setEnabled(False)
        self.model.setToolTip("最终 bitstream 仅保留 AD9269；J25 已全部释放")
        self.rate = QComboBox()
        self.test_mode = QComboBox()
        self.test_mode.addItem("关闭", 0)
        for mode in range(1, 8):
            self.test_mode.addItem(f"测试码 {mode}", mode)
        self.channel_swap = VisibleCheckBox("手动交换 A/B")
        self.channel_swap.setToolTip(
            "默认已自动校正AD9269的DCO边沿顺序：INA显示为通道A，INB显示为通道B。"
            "仅在需要故意互换两个逻辑通道时勾选。"
        )
        self.jumbo = VisibleCheckBox("约 9 KB 巨帧（20 MSPS 双通道推荐）")
        # VisibleCheckBox draws its own label, so reserve explicit space for
        # the full text even when Windows display scaling is above 100%.
        self.channel_swap.setMinimumWidth(230)
        self.jumbo.setMinimumWidth(390)
        # Standard-MTU mode is the safest default for first-link validation.
        # Enable jumbo explicitly for sustained 20 MSPS AD9269 monitoring.
        self.jumbo.setChecked(False)
        self.window_samples = QSpinBox()
        self.window_samples.setRange(2_000, 2_000_000)
        self.window_samples.setValue(DISPLAY_SAMPLES)
        config_grid.addWidget(QLabel("PL 板卡地址"), 0, 0)
        config_grid.addWidget(self.board_ip, 0, 1)
        config_grid.addWidget(QLabel("ADC 型号"), 0, 2)
        config_grid.addWidget(self.model, 0, 3)
        config_grid.addWidget(QLabel("采样率"), 1, 0)
        config_grid.addWidget(self.rate, 1, 1)
        config_grid.addWidget(QLabel("测试模式"), 1, 2)
        config_grid.addWidget(self.test_mode, 1, 3)
        options = QGridLayout()
        options.setContentsMargins(0, 3, 0, 0)
        options.setHorizontalSpacing(30)
        options.setColumnStretch(0, 1)
        options.setColumnStretch(1, 2)
        options.addWidget(self.channel_swap, 0, 0, Qt.AlignLeft)
        options.addWidget(self.jumbo, 0, 1, Qt.AlignLeft)
        config_grid.addLayout(options, 2, 0, 1, 4)
        panel_layout.addLayout(config_grid)
        # Kept for API compatibility with older launchers/tests. The visible
        # scope timebase now determines the sample window directly.
        self.window_samples.hide()
        page.addWidget(panel)

        action_card = QFrame()
        action_card.setObjectName("card")
        self.action_card = action_card
        action_layout = QGridLayout(action_card)
        action_layout.setContentsMargins(14, 12, 14, 12)
        action_layout.setSpacing(9)
        self.connect_button = QPushButton("发现并连接")
        self.start_button = QPushButton("START")
        self.stop_button = QPushButton("STOP")
        self.record_button = QPushButton("开始 HDF5 录制")
        self.record_channels = QComboBox()
        self.record_channels.addItem("仅录制 A", "a")
        self.record_channels.addItem("仅录制 B", "b")
        self.record_channels.setToolTip(
            "HDF5仅保存所选单通道，同时保留原始ADC码和换算电压"
        )
        self.record_rate = QComboBox()
        self.record_rate.addItem("1 MSPS", 1_000_000)
        self.record_rate.addItem("100 kSPS", 100_000)
        self.record_rate.addItem("10 kSPS", 10_000)
        self.record_rate.addItem("1 kSPS", 1_000)
        self.record_rate.setCurrentIndex(self.record_rate.findData(100_000))
        self.record_rate.setToolTip(
            "按真实64位样点索引等间隔抽取；不会改变FPGA实际采样率"
        )
        self.record_content = QComboBox()
        self.record_content.addItem(
            "仅保存ADC波形",
            RecordingOptionsDialog.WAVEFORM_ONLY,
        )
        self.record_content.addItem(
            "ADC波形＋DLC pro参数",
            RecordingOptionsDialog.WITH_DLCPRO,
        )
        stored_content_index = self.record_content.findData(
            self.record_metadata_mode
        )
        self.record_content.setCurrentIndex(
            stored_content_index if stored_content_index >= 0 else 0
        )
        self.record_content.setToolTip(
            "组合模式会同步保存Scan Offset、Scan Amplitude及必要的扫描上下文"
        )
        self.record_path_button = QPushButton("选择保存路径")
        self.record_path_button.setToolTip("可选择U盘、移动SSD或本地磁盘")
        self.record_path_button.setMinimumWidth(150)
        self.record_path_button.setMaximumWidth(220)
        self.record_path_button.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )
        self.scan_control_button = QPushButton("扫频控制")
        self.auto_lock_button = QPushButton("自动锁频")
        self.dlc_status_label = QLabel("DLC pro：未连接")
        self.scope_a_button = QPushButton("打开通道 A")
        self.scope_b_button = QPushButton("打开通道 B")
        # Compatibility alias: the generic scope action opens channel A.
        self.scope_button = self.scope_a_button
        self.fpga_select_button = QPushButton("选择bit")
        self.fpga_program_button = QPushButton("下载FPGA")
        self.fpga_path_label = QLabel("未选择bitstream")
        self.fpga_path_label.setObjectName("muted")
        self.fpga_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.fpga_progress = QProgressBar()
        self.fpga_progress.setRange(0, 100)
        self.fpga_progress.setValue(0)
        self.fpga_progress.setFormat("等待下载")
        # Scope launchers are peer actions. Keep them visually equal instead
        # of letting the recording-path stretch column make channel A huge.
        self.scope_a_button.setMinimumWidth(150)
        self.scope_b_button.setMinimumWidth(150)
        self.connect_button.setObjectName("primaryButton")
        self.start_button.setObjectName("startButton")
        self.stop_button.setObjectName("stopButton")
        self.record_button.setObjectName("recordButton")
        self.record_button.setCheckable(True)
        for button in (self.start_button, self.stop_button, self.record_button):
            button.setEnabled(False)
        action_layout.addWidget(self.connect_button, 0, 0)
        action_layout.addWidget(self.start_button, 0, 1)
        action_layout.addWidget(self.stop_button, 0, 2)
        action_layout.addWidget(self.dlc_status_label, 0, 3)
        action_layout.addWidget(self.scan_control_button, 0, 4)
        action_layout.addWidget(self.auto_lock_button, 0, 5)
        action_layout.addWidget(self.scope_a_button, 0, 6)
        action_layout.addWidget(self.scope_b_button, 0, 7)
        action_layout.addWidget(QLabel("录制设置"), 1, 0)
        action_layout.addWidget(self.record_channels, 1, 1)
        action_layout.addWidget(self.record_rate, 1, 2)
        action_layout.addWidget(self.record_content, 1, 3, 1, 2)
        action_layout.addWidget(self.record_path_button, 1, 5)
        action_layout.addWidget(self.record_button, 1, 7)
        action_layout.setColumnStretch(3, 1)
        page.addWidget(action_card)

        # FPGA programming is a maintenance operation, separate from normal
        # acquisition/recording controls so neither row gets squeezed.
        self.fpga_card = QFrame()
        self.fpga_card.setObjectName("card")
        fpga_card_layout = QVBoxLayout(self.fpga_card)
        fpga_card_layout.setContentsMargins(16, 12, 16, 13)
        fpga_card_layout.setSpacing(9)
        fpga_header = QHBoxLayout()
        fpga_title = QLabel("FPGA 下载（JTAG）")
        fpga_title.setObjectName("sectionTitle")
        fpga_hint = QLabel("自动连接本机硬件服务器与 Zynq-7000，无需打开 Vivado GUI")
        fpga_hint.setObjectName("muted")
        fpga_header.addWidget(fpga_title)
        fpga_header.addSpacing(12)
        fpga_header.addWidget(fpga_hint)
        fpga_header.addStretch(1)
        fpga_card_layout.addLayout(fpga_header)

        self.fpga_controls_layout = QGridLayout()
        self.fpga_controls_layout.setHorizontalSpacing(12)
        self.fpga_controls_layout.setVerticalSpacing(0)
        self.fpga_controls_layout.setColumnStretch(2, 1)
        self.fpga_path_label.setMinimumWidth(230)
        self.fpga_progress.setMinimumWidth(270)
        self.fpga_controls_layout.addWidget(QLabel("Bitstream"), 0, 0)
        self.fpga_controls_layout.addWidget(self.fpga_select_button, 0, 1)
        self.fpga_controls_layout.addWidget(self.fpga_path_label, 0, 2)
        self.fpga_controls_layout.addWidget(self.fpga_program_button, 0, 3)
        self.fpga_controls_layout.addWidget(self.fpga_progress, 0, 4)
        fpga_card_layout.addLayout(self.fpga_controls_layout)
        page.addWidget(self.fpga_card)

        metric_strip = QHBoxLayout()
        metric_strip.setSpacing(9)
        self.metric_values: dict[str, QLabel] = {}
        self.metric_hints: dict[str, QLabel] = {}
        for key, title, value, hint in (
            ("link", "采集状态", "未连接", "PL UDP"),
            ("rate", "实测采样率", "--", "ADC sample pairs"),
            ("network", "PL 吞吐", "0.0 Mbit/s", "UDP payload"),
            ("loss", "网络丢包", "0", "packet sequence"),
            ("ddr", "DDR 事件路径", "未武装", "Linux SG DMA"),
        ):
            tile = QFrame()
            tile.setObjectName("metricTile")
            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(13, 9, 13, 9)
            tile_layout.setSpacing(1)
            title_label = QLabel(title)
            title_label.setObjectName("metricTitle")
            value_label = QLabel(value)
            value_label.setObjectName("metricValue")
            hint_label = QLabel(hint)
            hint_label.setObjectName("metricHint")
            tile_layout.addWidget(title_label)
            tile_layout.addWidget(value_label)
            tile_layout.addWidget(hint_label)
            metric_strip.addWidget(tile, 1)
            self.metric_values[key] = value_label
            self.metric_hints[key] = hint_label
        page.addLayout(metric_strip)

        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(18, 15, 18, 16)
        status_layout.setSpacing(7)
        status_title = QLabel("运行状态")
        status_title.setObjectName("sectionTitle")
        status_layout.addWidget(status_title)
        self.state_label = QLabel("等待连接 PL 板卡")
        self.state_label.setObjectName("statusHeadline")
        self.metrics_label = QLabel(
            f"PC PL 网卡应配置为 {PC_PL_IP}/24；PS/DLCpro 继续使用 192.168.10.x"
        )
        self.metrics_label.setObjectName("metrics")
        self.metrics_label.setWordWrap(True)
        self.metrics_label.setToolTip(
            "“未武装抑制”是 Linux 尚未提交并启动64个DMA描述符时检测到的峰，"
            "不属于数据丢失；“DDR背压丢帧”只统计事件路径已武装后的真实拥塞。"
        )
        status_layout.addWidget(self.state_label)
        status_layout.addWidget(self.metrics_label)
        network_note = QLabel(
            "PL 网口 192.168.20.x 仅用于采集；PS/DLCpro 保持 192.168.10.x"
        )
        network_note.setObjectName("muted")
        status_layout.addWidget(network_note)
        page.addWidget(status_card)
        page.addStretch(1)

        self.model.currentIndexChanged.connect(self._model_changed)
        self.rate.currentIndexChanged.connect(self._rate_changed)
        self.connect_button.clicked.connect(self.connect_board)
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_path_button.clicked.connect(self.choose_record_path)
        self.record_content.currentIndexChanged.connect(
            self._record_content_changed
        )
        self.scan_control_button.clicked.connect(self.show_scan_control)
        self.auto_lock_button.clicked.connect(self.show_peak_lock)
        self.scope_a_button.clicked.connect(self.show_scope_a)
        self.scope_b_button.clicked.connect(self.show_scope_b)
        self.fpga_select_button.clicked.connect(self.choose_fpga_bit)
        self.fpga_program_button.clicked.connect(self.program_fpga)
        self.scope_a.time_settings_changed.connect(
            lambda: self._scope_settings_changed(self.scope_a, self.scope_b)
        )
        self.scope_b.time_settings_changed.connect(
            lambda: self._scope_settings_changed(self.scope_b, self.scope_a)
        )
        self.dlc_session.connection_changed.connect(
            self._dlc_connection_changed
        )
        self.dlc_session.error.connect(self._dlc_error)
        if snapshot_consumer is not None:
            self.dlc_session.write_snapshot_changed.connect(snapshot_consumer)
        self.peak_lock_controller = AdcPeakBalanceController(
            self.ring, self.dlc_session,
            acquisition_running=lambda: self.stream_id is not None,
            parent=self,
        )
        # Auto-lock and both scopes remain independent top-level windows.
        # The scope buttons inside auto-lock only tile windows on the desktop;
        # no QWidget is reparented or embedded.
        self.peak_lock_window = AdcPeakBalanceWindow(
            self.peak_lock_controller,
            self.settings,
            parent=None,
            falc_window_opener=self.falc_window_opener,
            embedded=False,
        )
        # Compatibility alias retained for the main launcher.
        self.auto_lock_workspace = self.peak_lock_window
        self.peak_lock_window.scope_requested.connect(
            self._tile_scope_with_peak_lock
        )
        self.scan_control_window = DlcScanControlWindow(
            self.dlc_session, self.settings, parent=None
        )
        self.peak_lock_window.scan_control_requested.connect(
            self.show_scan_control
        )
        self.peak_lock_controller.running_changed.connect(
            self._peak_lock_running_changed
        )
        self._restore_settings(preset_model)

        self.plot_timer = QTimer(self)
        self.plot_timer.setTimerType(Qt.PreciseTimer)
        self.plot_timer.setInterval(
            max(1, round(1000 / self.scope_a.refresh_fps))
        )
        self.plot_timer.timeout.connect(self.refresh_plots)
        self.plot_timer.start()

    def _set_connection_state(self, text: str, state: str):
        self.connection_pill.setText(text)
        self.connection_pill.setProperty("state", state)
        self.connection_pill.style().unpolish(self.connection_pill)
        self.connection_pill.style().polish(self.connection_pill)

    @staticmethod
    def _bool_setting(value) -> bool:
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    @staticmethod
    def _select_combo_data(combo: QComboBox, value):
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _restore_settings(self, preset_model: int | None):
        geometry = self.settings.value("main/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        self.board_ip.setText(str(self.settings.value(
            "main/board_ip", PL_BOARD_IP
        )))
        model = 1
        self._select_combo_data(self.model, model)
        self._model_changed()
        # Acquisition always starts from the conservative standard-MTU
        # baseline.  A previous 20 MSPS session must not silently carry its
        # high-rate network requirements into the next launch.
        self._select_combo_data(self.rate, 10_000_000)
        self.settings.remove("main/rate")
        self._select_combo_data(
            self.test_mode, int(self.settings.value("main/test_mode", 0))
        )
        # V2 makes the board's fixed DDR-edge correction automatic.  Do not
        # carry an old workaround checkbox into the new logical mapping.
        if not self._bool_setting(
            self.settings.value("main/channel_mapping_v2", False)
        ):
            self.channel_swap.setChecked(False)
            self.settings.setValue("main/channel_swap", False)
            self.settings.setValue("main/channel_mapping_v2", True)
        else:
            self.channel_swap.setChecked(self._bool_setting(
                self.settings.value("main/channel_swap", False)
            ))
        # Startup is always 10 MSPS with standard MTU.  Selecting 20 MSPS
        # later in this session still enables jumbo mode in _rate_changed().
        self.jumbo.setChecked(False)
        self.settings.remove("main/jumbo")
        stored_bit = str(self.settings.value("fpga/bit_path", "")).strip()
        if stored_bit:
            self.fpga_bit_path = Path(stored_bit)
        elif DEFAULT_FPGA_BIT.is_file():
            self.fpga_bit_path = DEFAULT_FPGA_BIT
            self.settings.setValue("fpga/bit_path", str(DEFAULT_FPGA_BIT))
        self._update_fpga_bit_display()
        self._select_combo_data(
            self.record_channels,
            str(self.settings.value("record/channel", "a")),
        )
        self._select_combo_data(
            self.record_rate,
            int(self.settings.value("record/rate_hz", 100_000)),
        )
        self.scope_a.restore_settings(self.settings, "scope_a")
        self.scope_b.restore_settings(self.settings, "scope_b")
        if not self._bool_setting(
            self.settings.value("scope/performance_v2_migrated", False)
        ):
            for prefix, scope in (
                ("scope_a", self.scope_a), ("scope_b", self.scope_b)
            ):
                scope.smoothing.setChecked(False)
                self.settings.setValue(f"{prefix}/smoothing", False)
            self.settings.setValue("scope/performance_v2_migrated", True)
        # One-time migration from the former 10 FPS default.  Later manual
        # choices remain persistent because the migration flag is retained.
        if not self._bool_setting(
            self.settings.value("scope/fps_60_default_migrated", False)
        ):
            for scope in (self.scope_a, self.scope_b):
                index = scope.fps.findData(DISPLAY_FPS)
                if index >= 0:
                    scope.fps.setCurrentIndex(index)
            self.settings.setValue("scope/fps_60_default_migrated", True)
        workspace_geometry = self.settings.value("auto_lock_window/geometry")
        if workspace_geometry is None:
            workspace_geometry = self.settings.value(
                "auto_lock_workspace/geometry"
            )
        if workspace_geometry is not None:
            self.auto_lock_workspace.restoreGeometry(workspace_geometry)
        for scope, key in (
            (self.scope_a, "scope_a/geometry"),
            (self.scope_b, "scope_b/geometry"),
        ):
            scope_geometry = self.settings.value(key)
            if scope_geometry is not None:
                scope.restoreGeometry(scope_geometry)
    def _save_settings(self):
        self.settings.setValue("main/geometry", self.saveGeometry())
        self.settings.setValue("main/board_ip", self.board_ip.text().strip())
        self.settings.setValue("main/model", self.model.currentData())
        self.settings.remove("main/rate")
        self.settings.setValue("main/test_mode", self.test_mode.currentData())
        self.settings.setValue("main/channel_swap",
                               self.channel_swap.isChecked())
        self.settings.setValue(
            "fpga/bit_path",
            str(self.fpga_bit_path) if self.fpga_bit_path else "",
        )
        self.settings.setValue(
            "record/channel", self.record_channels.currentData()
        )
        self.settings.setValue(
            "record/rate_hz", self.record_rate.currentData()
        )
        self.scope_a.save_settings(self.settings, "scope_a")
        self.scope_b.save_settings(self.settings, "scope_b")
        self.settings.setValue("scope_a/geometry", self.scope_a.saveGeometry())
        self.settings.setValue("scope_b/geometry", self.scope_b.saveGeometry())
        self.settings.setValue(
            "auto_lock_window/geometry",
            self.peak_lock_window.saveGeometry(),
        )
        self.settings.sync()

    def _update_fpga_bit_display(self):
        path = self.fpga_bit_path
        available = bool(path and path.is_file())
        self.fpga_program_button.setEnabled(
            available and not (
                self.fpga_programmer and self.fpga_programmer.isRunning()
            )
        )
        if path is None:
            self.fpga_path_label.setText("未选择bitstream")
            self.fpga_path_label.setToolTip("请先选择要下载的.bit文件")
            return
        state = "已选择" if available else "文件不存在"
        self.fpga_path_label.setText(f"{path.name} · {state}")
        self.fpga_path_label.setToolTip(str(path))

    def choose_fpga_bit(self):
        current = self.fpga_bit_path
        if current and current.is_file():
            initial = str(current)
        elif DEFAULT_FPGA_BIT.parent.is_dir():
            initial = str(DEFAULT_FPGA_BIT.parent)
        else:
            initial = str(Path.home() / "Desktop")
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "选择要下载到FPGA的bitstream",
            initial,
            "Xilinx Bitstream (*.bit)",
        )
        if not selected:
            return
        path = Path(selected).resolve()
        if path.suffix.lower() != ".bit" or not path.is_file():
            QMessageBox.warning(self, "bitstream无效", "请选择有效的.bit文件。")
            return
        self.fpga_bit_path = path
        self.settings.setValue("fpga/bit_path", str(path))
        self.settings.sync()
        self.fpga_progress.setValue(0)
        self.fpga_progress.setFormat("已选择，等待下载")
        self._update_fpga_bit_display()

    def program_fpga(self):
        bitstream = self.fpga_bit_path
        if bitstream is None or not bitstream.is_file():
            QMessageBox.warning(self, "无法下载FPGA", "请先选择有效的.bit文件。")
            self._update_fpga_bit_display()
            return
        if self.fpga_programmer and self.fpga_programmer.isRunning():
            return
        if self.recorder is not None:
            QMessageBox.warning(
                self, "无法下载FPGA", "请先停止HDF5录制，再下载bitstream。"
            )
            return
        vivado = find_vivado_batch()
        if vivado is None:
            QMessageBox.critical(
                self,
                "未找到Vivado",
                "未找到Vivado批处理工具。请确认Vivado或Lab Edition已经安装。",
            )
            return
        if not FPGA_PROGRAM_TCL.is_file():
            QMessageBox.critical(
                self, "下载脚本缺失", f"找不到：\n{FPGA_PROGRAM_TCL}"
            )
            return

        # Reconfiguring PL invalidates the current UDP/control session.
        if self.stream_id is not None:
            self.stop_acquisition()
        if self.control is not None or self.receiver is not None:
            self.disconnect_board()

        self.fpga_program_output.clear()
        worker = FpgaProgrammer(
            vivado, FPGA_PROGRAM_TCL, bitstream, parent=self
        )
        self.fpga_programmer = worker
        worker.progress.connect(self._fpga_program_progress)
        worker.output.connect(self._fpga_program_output)
        worker.program_succeeded.connect(self._fpga_program_succeeded)
        worker.program_failed.connect(self._fpga_program_failed)
        worker.finished.connect(self._fpga_program_thread_finished)
        self.fpga_select_button.setEnabled(False)
        self.fpga_program_button.setEnabled(False)
        self.fpga_progress.setValue(5)
        self.fpga_progress.setFormat("正在启动后台下载…")
        self.state_label.setText(f"正在后台下载FPGA：{bitstream.name}")
        worker.start()

    def _fpga_program_progress(self, value: int, message: str):
        self.fpga_progress.setValue(int(value))
        self.fpga_progress.setFormat(f"{message} · %p%")
        self.state_label.setText(message)

    def _fpga_program_output(self, line: str):
        self.fpga_program_output.append(str(line))
        self.fpga_program_output = self.fpga_program_output[-80:]

    def _fpga_program_succeeded(self, bitstream: str):
        self.fpga_progress.setValue(100)
        self.fpga_progress.setFormat("FPGA下载完成 · 100%")
        self.state_label.setText(
            f"FPGA下载完成：{Path(bitstream).name}；请重新连接PL板卡"
        )
        if not self._closing:
            QMessageBox.information(
                self,
                "FPGA下载完成",
                "bitstream已写入PL配置RAM。开发板断电后该配置会消失。\n"
                "请点击“发现并连接”重新建立采集连接。",
            )

    def _fpga_program_failed(self, detail: str):
        self.fpga_progress.setFormat("FPGA下载失败")
        self.state_label.setText("FPGA下载失败")
        if not self._closing:
            QMessageBox.critical(
                self, "FPGA下载失败", str(detail)[-5000:]
            )

    def _fpga_program_thread_finished(self):
        worker = self.fpga_programmer
        self.fpga_programmer = None
        self.fpga_select_button.setEnabled(True)
        self._update_fpga_bit_display()
        if worker is not None:
            worker.deleteLater()

    def _scope_settings_changed(self, source: ScopeWindow, peer: ScopeWindow):
        for source_widget, peer_widget in (
            (source.timebase, peer.timebase),
            (source.fps, peer.fps),
            (source.scroll_speed, peer.scroll_speed),
        ):
            peer_widget.blockSignals(True)
            peer_widget.setCurrentIndex(source_widget.currentIndex())
            peer_widget.blockSignals(False)
        if hasattr(self, "plot_timer"):
            self.plot_timer.setInterval(
                max(1, round(1000 / source.refresh_fps))
            )
        self.plot_tick = 0

    def _model_changed(self):
        model = int(self.model.currentData() or 0)
        current = self.rate.currentData()
        self.rate.clear()
        rates = (5, 10, 20)
        for value in rates:
            self.rate.addItem(f"{value} MSPS", value * 1_000_000)
        index = self.rate.findData(current)
        self.rate.setCurrentIndex(index if index >= 0 else 1)
        dual = model == 1
        self.scope_a.configure_model(model)
        self.scope_b.configure_model(model)
        self.channel_swap.setEnabled(dual)
        self.scope_b_button.setVisible(dual)
        if not dual:
            self.scope_b.close()
        self._rate_changed()

    def _rate_changed(self):
        rate = int(self.rate.currentData() or 0)
        if rate >= 20_000_000:
            self.jumbo.setChecked(True)
        self.jumbo.setEnabled(True)
        self.jumbo.setToolTip(
            "PL UDP 仅支持 5/10/20 MSPS；40/80 MSPS 请由 Linux 使用 Scope/Event DMA"
        )

    def connect_board(self):
        self.disconnect_board()
        try:
            self.control = ControlClient(
                self.board_ip.text().strip(), adc_model=1
            )
            response = self.control.request(Command.DISCOVER)
            self.receiver = UdpDualReceiver(
                self.ring,
                board_ip=self.board_ip.text().strip(),
                packet_callback=self._record_packet,
            )
            self.receiver.metrics.connect(self._metrics_received)
            self.receiver.failed.connect(self._receiver_failed)
            self.receiver.start()
            if not self.receiver.wait_until_ready(1.0):
                raise RuntimeError(self.receiver.startup_error or "UDP/5001 接收端口启动失败")
            self.poller = StatusPoller(self.control)
            self.poller.received.connect(self._status_received)
            self.poller.start()
            self._status_received(response)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.connect_button.setText("重新连接")
        except Exception as exc:
            self.disconnect_board()
            self._set_connection_state("●  连接失败", "error")
            self.state_label.setText("未连接到 PL 板卡")
            QMessageBox.critical(self, "连接失败", str(exc))

    def start_acquisition(self):
        if (not self.control or not self.receiver or
                (self.acquisition_starter and
                 self.acquisition_starter.isRunning())):
            return
        try:
            if self.jumbo.isChecked():
                jumbo_ready, detail = windows_jumbo_status()
                if jumbo_ready is False:
                    raise RuntimeError(
                        "PC 的 PL 网卡尚未启用 9 KB 巨帧，继续发送会导致波形冻结。\n"
                        f"{detail}\n请在网卡高级属性中把“巨型帧”设为 9014 Bytes。"
                    )
                if jumbo_ready is None:
                    answer = QMessageBox.question(
                        self, "无法确认巨帧配置",
                        f"{detail}。\n确认 PC 的 PL 网卡已启用 9014 Bytes 后再继续。",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
                    )
                    if answer != QMessageBox.Yes:
                        return
            flags = int(self.test_mode.currentData()) << CONFIG_TEST_SHIFT
            flags |= ad9269_config_channel_swap(
                self.channel_swap.isChecked()
            )
            previous_stream = int(self.latest_status.stream_id) if self.latest_status else -1
            self.model.setEnabled(False)
            self.rate.setEnabled(False)
            self.start_button.setEnabled(False)
            self.connect_button.setEnabled(False)
            self.state_label.setText("正在启动采集…")
            worker = AcquisitionStarter(
                self.control,
                sample_rate_hz=int(self.rate.currentData()),
                flags=flags,
                jumbo_enabled=self.jumbo.isChecked(),
                previous_stream=previous_stream,
                parent=self,
            )
            self.acquisition_starter = worker
            worker.succeeded.connect(self._acquisition_started)
            worker.failed.connect(self._acquisition_start_failed)
            worker.finished.connect(self._acquisition_start_finished)
            worker.start()
        except Exception as exc:
            self._acquisition_start_failed(str(exc))

    def _acquisition_started(self, response):
        if self._closing or self.receiver is None:
            return
        self.stream_id = int(response.stream_id)
        self.receiver.prepare_stream(self.stream_id)
        self.record_button.setEnabled(True)
        self._status_received(response)
        self.show_scope_a()

    def _acquisition_start_failed(self, message: str):
        self.stream_id = None
        self.model.setEnabled(False)
        self.rate.setEnabled(True)
        self.start_button.setEnabled(self.control is not None)
        self.record_button.setEnabled(False)
        if not self._closing:
            QMessageBox.critical(self, "启动失败", str(message))

    def _acquisition_start_finished(self):
        worker = self.acquisition_starter
        self.acquisition_starter = None
        self.connect_button.setEnabled(True)
        if worker is not None:
            worker.deleteLater()

    def stop_acquisition(self):
        if self.acquisition_starter and self.acquisition_starter.isRunning():
            self.acquisition_starter.requestInterruption()
        if self.peak_lock_controller.running:
            self.peak_lock_controller.stop("ADC采集停止，自动锁频终止")
        if self.control:
            try:
                self._status_received(self.control.request(Command.STOP))
            except Exception as exc:
                QMessageBox.warning(self, "停止警告", str(exc))
        self.stream_id = None
        self.model.setEnabled(False)
        self.rate.setEnabled(True)
        self.start_button.setEnabled(self.control is not None)
        self.record_button.setEnabled(False)
        if self.recorder:
            self.toggle_recording()

    def _metrics_received(self, metrics: dict):
        if self.stream_id is not None and int(metrics.get("stream_id", -1)) != self.stream_id:
            return
        self.metrics = metrics
        self._render_status()

    def _status_received(self, status):
        now = time.monotonic()
        elapsed = now - self.last_event_time
        if elapsed > 0:
            delta = max(0, int(status.event_count) - self.last_event_count)
            self.event_rate = delta / elapsed
        self.last_event_count = int(status.event_count)
        self.last_event_time = now
        self.latest_status = status
        self._render_status()

    def _render_status(self):
        status = self.latest_status
        if status is None:
            return
        model = "AD9269 S16 A/B"
        running = status.daq_state == 3
        self.state_label.setText(
            f"{'运行中' if running else '已停止'} · {model} · Stream {status.stream_id}"
        )
        self._set_connection_state(
            "●  正在采集" if running else "●  已连接",
            "running" if running else "connected",
        )
        throughput = float(self.metrics.get("throughput_mbps", 0.0))
        loss = int(self.metrics.get("packet_loss", 0))
        pl_gap = int(self.metrics.get("pl_sample_gap", 0))
        gap_actual = self.metrics.get("last_gap_actual")
        gap_location = (
            f"，最近恢复索引 {int(gap_actual)}"
            if pl_gap and gap_actual is not None else ""
        )
        interval_samples = status.peak_interval_q16 / 65536.0
        interval_text = (f"{interval_samples:.3f} 样点" if interval_samples else "--")
        if self.recorder:
            self.record_dropped = self.recorder.dropped_samples
        record_text = (f" | 录制队列丢样 {self.record_dropped}"
                       if self.recorder else "")
        event_path_text = "已武装" if status.event_path_enabled else "未武装"
        self.metric_values["link"].setText("运行中" if running else "已连接")
        self.metric_values["rate"].setText(
            f"{status.dco_frequency_hz / 1e6:.3f} MSPS"
        )
        self.metric_values["network"].setText(f"{throughput:.1f} Mbit/s")
        self.metric_values["loss"].setText(f"网包 {loss} / PL样点 {pl_gap}")
        self.metric_values["ddr"].setText(event_path_text)
        self.metric_hints["ddr"].setText(
            f"抑制 {status.suppressed_event_count} · 丢帧 {status.dropped_event_count}"
        )
        self.metrics_label.setText(
            f"设定 {status.sample_rate_hz / 1e6:.3f} MSPS | "
            f"实测 {status.dco_frequency_hz / 1e6:.3f} MSPS | "
            f"PL 网口 {throughput:.1f} Mbit/s | 网络丢包 {loss} | "
            f"PL样点空洞 {pl_gap}{gap_location} | "
            f"采集 FIFO {status.fifo_level} | PL监视丢样 {status.blocks_dropped} | "
            f"OTR A/B {status.otr_a_count}/{status.otr_b_count} | "
            f"事件率 {self.event_rate:.2f}/s | 峰间距 {interval_text} | "
            f"DDR {event_path_text} | 未武装抑制 {status.suppressed_event_count} | "
            f"DDR背压丢帧 {status.dropped_event_count} | 错误 {status.last_error}"
            f"{record_text}"
        )

    def refresh_plots(self):
        self.plot_tick += 1
        divisor = max(self.scope_a.scroll_divisor, self.scope_b.scroll_divisor)
        if self.plot_tick % divisor:
            self._drain_recorder()
            return
        rate = self.ring.effective_rate_hz
        visible_a = self.scope_a.isVisible() and not self.scope_a.frozen
        visible_b = (int(self.model.currentData()) == 1 and
                     self.scope_b.isVisible() and not self.scope_b.frozen)
        if not visible_a and not visible_b:
            if self.plot_timer.interval() != 250:
                self.plot_timer.setInterval(250)
            self._drain_recorder()
            return
        target_interval = max(
            1, round(1000 / max(
                self.scope_a.refresh_fps if visible_a else 1,
                self.scope_b.refresh_fps if visible_b else 1,
            ))
        )
        if self.plot_timer.interval() != target_interval:
            self.plot_timer.setInterval(target_interval)
        if visible_a or visible_b:
            samples = max(
                self.scope_a.required_samples(rate) if visible_a else 0,
                self.scope_b.required_samples(rate) if visible_b else 0,
            )
            pixels = min(900, max(
                self.scope_a.plot.width() if visible_a else 0,
                self.scope_b.plot.width() if visible_b else 0,
            ))
            trigger_scope = None
            if samples > RAW_ENVELOPE_SAMPLE_LIMIT:
                # Long timebases are served from the rolling 1 ms min/max
                # cache. Cost is bounded by screen width and is independent
                # of 5/10/20 MSPS raw input rate.
                span_seconds = max(
                    float(self.scope_a.timebase.currentData() or 0.0)
                    if visible_a else 0.0,
                    float(self.scope_b.timebase.currentData() or 0.0)
                    if visible_b else 0.0,
                ) * 10.0
                envelope = self.ring.history_envelope(
                    span_seconds, max(200, pixels)
                )
            else:
                if visible_a and self.scope_a.trigger_config is not None:
                    trigger_scope = self.scope_a
                elif visible_b and self.scope_b.trigger_config is not None:
                    trigger_scope = self.scope_b
                if trigger_scope is not None:
                    channel, level, rising = trigger_scope.trigger_config
                    envelope = self.ring.triggered_envelope(
                        samples, max(200, pixels), channel=channel,
                        level=level, rising=rising
                    )
                else:
                    envelope = self.ring.envelope(
                        samples, max(200, pixels)
                    )
            if envelope is not None:
                if trigger_scope is not None:
                    amin, amax, bmin, bmax, valid, trigger_locked = envelope
                else:
                    amin, amax, bmin, bmax, valid = envelope
                    trigger_locked = None
                if visible_a:
                    self.scope_a.update_data(
                        amin, amax, valid, rate,
                        trigger_locked if trigger_scope is self.scope_a else None
                    )
                if visible_b:
                    self.scope_b.update_data(
                        bmin, bmax, valid, rate,
                        trigger_locked if trigger_scope is self.scope_b else None
                    )
        self._drain_recorder()

    def _drain_recorder(self):
        # Recording is fed directly by accepted UDP packets in the receiver
        # thread.  Plot refresh must never act as a high-speed recorder clock.
        if self.recorder:
            self.record_dropped = self.recorder.dropped_samples

    def _record_packet(self, packet):
        recorder = self.recorder
        if recorder is not None:
            recorder.append_packet(time.time(), packet)

    def show_dlc_settings(self):
        if self.dlc_settings_dialog is None:
            self.dlc_settings_dialog = DlcProSettingsDialog(
                self.dlc_session, self.settings, self
            )
            self.dlc_settings_dialog.set_scan_edit_locked(
                self.peak_lock_controller.running
                and not self.peak_lock_controller.observe_only
            )
        show_window_front(self.dlc_settings_dialog)

    def show_peak_lock(self):
        show_window_front(self.peak_lock_window)

    def show_scan_control(self):
        show_window_front(self.scan_control_window)

    def show_scope(self):
        self.show_scope_a()

    def show_scope_a(self):
        self._show_scope_channel(self.scope_a)

    def show_scope_b(self):
        self._show_scope_channel(self.scope_b)

    def _show_scope_channel(self, scope: ScopeWindow):
        scope.set_compact_controls(False)
        show_window_front(scope)
        if hasattr(self, "plot_timer"):
            self.plot_timer.setInterval(
                max(1, round(1000 / scope.refresh_fps))
            )

    def _tile_scope_with_peak_lock(self, channel: str):
        scope = self.scope_a if str(channel).upper() == "A" else self.scope_b
        # Tiling intentionally positions two peer windows as one layout.
        # Suppress delayed per-window fitting long enough for any timers from
        # an earlier standalone opening to expire, otherwise they overlap.
        for peer in (self.peak_lock_window, scope):
            peer.setProperty("suppressScheduledScreenFit", True)
        show_window_front(self.peak_lock_window)
        scope.showNormal()
        scope.show()

        screen = QApplication.screenAt(
            self.peak_lock_window.frameGeometry().center()
        ) or QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry().adjusted(12, 12, -12, -12)
            gap = 10
            available_width = max(2, area.width() - gap)
            if available_width >= 1440:
                scope.set_compact_controls(False)
                left_width = available_width // 2
            else:
                # On a narrow desktop both remain separate windows, but the
                # scope toolbar uses its compact layout so side-by-side tiling
                # still fits instead of overlapping.
                scope.set_compact_controls(True)
                left_width = min(
                    available_width - 320,
                    max(420, int(available_width * 0.55)),
                )
            left_width = min(
                left_width, self.peak_lock_window.maximumWidth()
            )
            right_width = max(1, available_width - left_width)
            title_inset = max(
                0,
                self.peak_lock_window.geometry().top()
                - self.peak_lock_window.frameGeometry().top(),
                scope.geometry().top() - scope.frameGeometry().top(),
            )
            height = min(
                max(1, area.height() - title_inset),
                max(700, self.peak_lock_window.height(), scope.height()),
            )
            top = min(
                max(self.peak_lock_window.y(), area.top() + title_inset),
                area.bottom() - height + 1,
            )
            self.peak_lock_window.setGeometry(
                area.left(), top, left_width, height
            )
            scope.setGeometry(
                area.left() + left_width + gap,
                top,
                right_width,
                height,
            )
        for peer in (self.peak_lock_window, scope):
            QTimer.singleShot(
                180,
                lambda target=peer: target.setProperty(
                    "suppressScheduledScreenFit", False
                ),
            )
        scope.raise_()
        scope.activateWindow()

    def _peak_lock_running_changed(self, running: bool):
        owns_scan_writes = running and not self.peak_lock_controller.observe_only
        self.scan_control_button.setEnabled(not owns_scan_writes)
        if self.dlc_settings_dialog is not None:
            self.dlc_settings_dialog.set_scan_edit_locked(owns_scan_writes)
        self.scan_control_window.set_scan_edit_locked(owns_scan_writes)

    def _dlc_connection_changed(self, connected: bool, text: str):
        self.dlc_status_label.setText(
            f"DLC pro：{'已连接' if connected else text}"
        )
        if not connected and self.recorder is not None:
            self.recorder.mark_dlcpro_incomplete(text)

    def _dlc_error(self, message: str):
        self.state_label.setText(f"DLC pro：{message}")

    def _record_content_changed(self):
        self.record_metadata_mode = str(self.record_content.currentData())
        self.settings.setValue(
            "record/content_mode", self.record_metadata_mode
        )

    def _choose_recording_mode(self) -> str | None:
        channel = "A" if self.record_channels.currentData() == "a" else "B"
        requested_rate = int(self.record_rate.currentData())
        rate_text = (
            "全部样点" if requested_rate <= 0
            else f"{requested_rate / 1000:g} kSPS"
        )
        path_text = (
            str(self.record_temp_path)
            if self.record_temp_path is not None else "尚未选择"
        )
        summary = (
            f"通道：{channel}\n"
            f"记录速率：{rate_text}\n"
            f"保存位置：{path_text}"
        )
        return RecordingOptionsDialog.get_mode(
            self,
            str(self.record_content.currentData()),
            summary,
            self.dlc_session.is_connected,
        )

    def choose_record_path(self) -> Path | None:
        previous_directory = Path(str(self.settings.value(
            "record_directory", str(Path.cwd())
        )))
        if not previous_directory.is_dir():
            previous_directory = Path.cwd()
        default_path = self.record_temp_path or previous_directory / (
            f"zynq_ad9269_{time.strftime('%Y%m%d_%H%M%S')}.h5"
        )
        selected, _ = QFileDialog.getSaveFileName(
            self, "选择HDF5采集保存位置", str(default_path),
            "HDF5实验数据 (*.h5)"
        )
        if not selected:
            return None
        target = Path(selected)
        if target.suffix.lower() != ".h5":
            target = target.with_suffix(".h5")
        self.record_temp_path = target
        self.settings.setValue("record_directory", str(target.parent))
        self.record_path_button.setText(target.name)
        self.record_path_button.setToolTip(str(target))
        return target

    def toggle_recording(self):
        if self.recorder:
            self._finish_recording()
            return

        metadata_mode = self._choose_recording_mode()
        if metadata_mode is None:
            self.record_button.setChecked(False)
            return
        include_dlcpro = (
            metadata_mode == RecordingOptionsDialog.WITH_DLCPRO
        )
        if include_dlcpro and (
            not self.dlc_session.is_connected
            or self.dlc_session.snapshot() is None
        ):
            self.record_button.setChecked(False)
            QMessageBox.warning(
                self,
                "DLC pro未连接",
                "“波形＋DLC pro扫描参数”模式需要先连接DLC pro并取得扫描参数。",
            )
            self.show_dlc_settings()
            return
        self.record_metadata_mode = metadata_mode
        content_index = self.record_content.findData(metadata_mode)
        if content_index >= 0:
            self.record_content.setCurrentIndex(content_index)
        self.settings.setValue("record/content_mode", metadata_mode)

        source_rate = int(self.rate.currentData())
        if source_rate >= 20_000_000 and not self.jumbo.isChecked():
            self.record_button.setChecked(False)
            QMessageBox.critical(
                self,
                "20 MSPS录制需要巨帧",
                "20 MSPS双通道在标准MTU下包率过高，录制会挤占UDP接收并产生样点空洞。\n"
                "请启用“约9 KB巨帧”并确认网卡为9014 Bytes，或改用10 MSPS。",
            )
            return

        target = self.record_temp_path or self.choose_record_path()
        if target is None:
            self.record_button.setChecked(False)
            return

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            free_bytes = shutil.disk_usage(target.parent).free
        except OSError as exc:
            self.record_button.setChecked(False)
            QMessageBox.critical(
                self, "录制失败", f"无法使用所选保存位置：\n{exc}"
            )
            return

        self.record_mode = str(self.record_channels.currentData())
        channel = "A" if self.record_mode == "a" else "B"
        requested_rate = int(self.record_rate.currentData())
        if requested_rate <= 0:
            self.record_button.setChecked(False)
            QMessageBox.critical(
                self,
                "录制速率不安全",
                "20 MSPS全部样点会超过当前HDF5实时写入能力。\n"
                "请选择1 MSPS、100 kSPS、10 kSPS或1 kSPS。",
            )
            return
        effective_rate = (
            source_rate if requested_rate <= 0
            else min(source_rate, requested_rate)
        )
        # raw + voltage + 64-bit index + validity plus HDF5 overhead.
        estimated_bytes_per_second = effective_rate * 18.0
        reserve_bytes = 10 * 1024 ** 3
        usable_seconds = max(
            0.0, (free_bytes - reserve_bytes) / estimated_bytes_per_second
        )
        if usable_seconds < 60:
            self.record_button.setChecked(False)
            QMessageBox.critical(
                self, "磁盘空间不足",
                f"所选磁盘可用空间仅 {free_bytes / 1024 ** 3:.1f} GiB。\n"
                "程序需预留10 GiB系统安全空间，当前配置不足以安全录制1分钟。"
            )
            return

        try:
            self.recorder = Hdf5Recorder(
                target,
                channel=channel,
                record_rate_hz=requested_rate,
                snapshot_provider=(
                    self.dlc_session.snapshot if include_dlcpro else None
                ),
                include_dlcpro=include_dlcpro,
            )
            self.record_dropped = 0
            self.record_channels.setEnabled(False)
            self.record_rate.setEnabled(False)
            self.record_content.setEnabled(False)
            self.record_path_button.setEnabled(False)
            self.record_button.setText("结束 HDF5 录制")
            self.record_button.setChecked(True)
            self.state_label.setText(
                f"正在录制到 {target} · 预计安全时长约"
                f"{usable_seconds / 60:.1f}分钟 · "
                f"{channel}通道 {effective_rate / 1000:g} kSPS · "
                f"{'含DLC pro参数' if include_dlcpro else '仅波形'}"
            )
        except Exception as exc:
            self.recorder = None
            self.record_channels.setEnabled(True)
            self.record_rate.setEnabled(True)
            self.record_content.setEnabled(True)
            self.record_path_button.setEnabled(True)
            self.record_button.setChecked(False)
            QMessageBox.critical(
                self, "录制失败", f"无法开始HDF5录制：\n{exc}"
            )

    def _finish_recording(self):
        recorder = self.recorder
        saved_path = self.record_temp_path
        self.recorder = None
        self.record_channels.setEnabled(True)
        self.record_rate.setEnabled(True)
        self.record_content.setEnabled(True)
        self.record_path_button.setEnabled(True)
        self.record_button.setText("开始 HDF5 录制")
        self.record_button.setChecked(False)
        if recorder is not None:
            try:
                recorder.update_quality(self.metrics)
                recorder.close()
                self.record_dropped = recorder.dropped_samples
            except Exception as exc:
                QMessageBox.critical(
                    self, "录制失败",
                    f"HDF5文件写入失败：\n{exc}"
                )
        self.record_temp_path = None
        self.record_path_button.setText("选择保存路径")
        self.record_path_button.setToolTip("可选择U盘、移动SSD或本地磁盘")
        if saved_path is not None and saved_path.exists():
            self.state_label.setText(
                f"HDF5已保存：{saved_path} · "
                f"录制队列丢样 {self.record_dropped}"
            )

    def _receiver_failed(self, message: str):
        self.state_label.setText(f"UDP 接收错误：{message}")
        self._set_connection_state("●  UDP 错误", "error")

    def disconnect_board(self):
        if hasattr(self, "peak_lock_controller") and self.peak_lock_controller.running:
            self.peak_lock_controller.stop("PL板卡断开，自动锁频终止")
        if self.poller:
            self.poller.stop()
            self.poller.wait(1500)
            self.poller = None
        if self.receiver:
            self.receiver.stop()
            self.receiver.wait(1500)
            self.receiver = None
        self.control = None
        self._set_connection_state("●  未连接", "idle")
        if hasattr(self, "metric_values"):
            self.metric_values["link"].setText("未连接")
            self.metric_values["network"].setText("0.0 Mbit/s")

    def closeEvent(self, event):
        self._closing = True
        if self.acquisition_starter and self.acquisition_starter.isRunning():
            self.acquisition_starter.requestInterruption()
            self.acquisition_starter.wait(2500)
        if self.fpga_programmer and self.fpga_programmer.isRunning():
            self.fpga_programmer.cancel()
            self.fpga_programmer.wait(5000)
        if self.control:
            try:
                self.control.request(Command.STOP)
            except Exception:
                pass
        if self.recorder:
            self._finish_recording()
        if hasattr(self, "peak_lock_controller"):
            self.peak_lock_controller.stop("ADC程序退出")
        if hasattr(self, "auto_lock_workspace"):
            self.auto_lock_workspace.close()
        if hasattr(self, "scope_a"):
            self.scope_a.close()
        if hasattr(self, "scope_b"):
            self.scope_b.close()
        if hasattr(self, "scan_control_window"):
            self.scan_control_window.close()
        self._save_settings()
        self.disconnect_board()
        self.dlc_session.shutdown()
        event.accept()


def main(preset_model: int | None = None):
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(preset_model=preset_model)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
