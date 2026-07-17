from __future__ import annotations

import csv
import socket
import struct
import sys
import time
from dataclasses import dataclass

import numpy as np
import serial
from serial.tools import list_ports

from PySide6.QtCore import QPointF, QThread, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from daq_protocol import (
    DATA_PORT,
    FLAG_DMA_ERROR,
    FLAG_FIFO_FULL,
    FLAG_FIFO_OVERFLOW,
    FLAG_LINK_UP,
    FLAG_RUNNING,
    Command,
)
from daq_udp import ControlClient, SampleRingBuffer, UdpReceiver


TIMEBASES = [
    ("100 us", 100e-6),
    ("200 us", 200e-6),
    ("1 ms", 1e-3),
    ("10 ms", 10e-3),
    ("100 ms", 100e-3),
    ("1 s", 1.0),
]

DISPLAY_REFRESH_RATES = [
    ("5 FPS", 5),
    ("10 FPS", 10),
    ("15 FPS", 15),
    ("30 FPS", 30),
]


@dataclass
class SerialConfig:
    port: str
    baud: int
    sample_rate_mhz: int
    size: int = 4096


class SerialCaptureThread(QThread):
    captured = Signal(object, float)
    failed = Signal(str)

    def __init__(self, config: SerialConfig):
        super().__init__()
        self.config = config

    def run(self):
        started = time.perf_counter()
        try:
            with serial.Serial(
                self.config.port,
                self.config.baud,
                timeout=2.0,
                write_timeout=2.0,
            ) as port:
                port.reset_input_buffer()
                command = bytearray([self.config.sample_rate_mhz])
                command.extend(struct.pack("<H", self.config.size))
                command.extend((3, 128, 0))
                port.write(command)
                port.flush()
                raw = bytearray()
                deadline = time.monotonic() + 5.0
                while len(raw) < self.config.size and time.monotonic() < deadline:
                    raw.extend(port.read(self.config.size - len(raw)))
            if len(raw) != self.config.size:
                raise TimeoutError(f"仅收到 {len(raw)} / {self.config.size} 字节")
            words = np.frombuffer(raw, dtype="<u2")
            self.captured.emit((words & 0xFF).astype(np.uint8), time.perf_counter() - started)
        except Exception as exc:
            self.failed.emit(str(exc))


class StatusPoller(QThread):
    received = Signal(object)
    failed = Signal(str)

    def __init__(self, control: ControlClient):
        super().__init__()
        self.control = control
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        while not self._stop_requested:
            try:
                self.received.emit(self.control.request(Command.STATUS))
            except Exception as exc:
                if not self._stop_requested:
                    self.failed.emit(str(exc))
            for _ in range(20):
                if self._stop_requested:
                    return
                self.msleep(50)


class WaveformWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(520, 360)
        self.minimum = np.empty(0)
        self.maximum = np.empty(0)
        self.valid = np.empty(0, dtype=np.bool_)
        self.duration = 1e-3
        self.y_label = "SMA input / V"
        self.y_range = (-5.0, 5.0)

    def set_envelope(self, minimum, maximum, valid, duration, y_label, y_range):
        self.minimum = np.asarray(minimum, dtype=np.float32)
        self.maximum = np.asarray(maximum, dtype=np.float32)
        self.valid = np.asarray(valid, dtype=np.bool_)
        self.duration = float(duration)
        self.y_label = y_label
        self.y_range = y_range
        self.update()

    def clear(self):
        self.minimum = np.empty(0)
        self.maximum = np.empty(0)
        self.valid = np.empty(0, dtype=np.bool_)
        self.update()

    @staticmethod
    def _time_text(seconds):
        if seconds < 1e-3:
            return f"{seconds * 1e6:.0f} us"
        if seconds < 1.0:
            return f"{seconds * 1e3:.1f} ms"
        return f"{seconds:.2f} s"

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#fbfcfe"))
        area = self.rect().adjusted(66, 24, -20, -48)

        painter.setPen(QPen(QColor("#c9d1dc"), 1))
        painter.drawRect(area)
        painter.setPen(QPen(QColor("#e3e8ef"), 1))
        for index in range(1, 5):
            y = area.top() + area.height() * index / 5
            painter.drawLine(area.left(), int(y), area.right(), int(y))
        for index in range(1, 8):
            x = area.left() + area.width() * index / 8
            painter.drawLine(int(x), area.top(), int(x), area.bottom())

        painter.setPen(QColor("#4b5565"))
        painter.drawText(12, area.top() + 14, self.y_label)
        painter.drawText(area.left(), self.height() - 16, f"-{self._time_text(self.duration)}")
        painter.drawText(area.right() - 18, self.height() - 16, "0")

        if self.minimum.size == 0:
            painter.setPen(QColor("#7a8493"))
            painter.drawText(area, Qt.AlignCenter, "等待数据")
            return

        finite = self.valid & np.isfinite(self.minimum) & np.isfinite(self.maximum)
        if self.y_range is None and finite.any():
            ymin = float(self.minimum[finite].min())
            ymax = float(self.maximum[finite].max())
            if ymax - ymin < 1e-6:
                ymin -= 0.5
                ymax += 0.5
            padding = (ymax - ymin) * 0.06
            ymin -= padding
            ymax += padding
        elif self.y_range is not None:
            ymin, ymax = self.y_range
        else:
            ymin, ymax = -1.0, 1.0

        painter.drawText(8, area.top() + 4, f"{ymax:.4g}")
        painter.drawText(8, area.bottom(), f"{ymin:.4g}")
        span = max(1e-12, ymax - ymin)
        count = self.minimum.size
        painter.save()
        painter.setClipRect(area)
        painter.setPen(QPen(QColor("#1467d8"), 1))
        for index in range(count):
            if not finite[index]:
                continue
            x = area.left() + index * area.width() / max(1, count - 1)
            y1 = area.bottom() - (float(self.minimum[index]) - ymin) * area.height() / span
            y2 = area.bottom() - (float(self.maximum[index]) - ymin) * area.height() / span
            painter.drawLine(int(x), int(y1), int(x), int(y2))
        painter.restore()


def codes_to_voltage(codes, mode):
    codes = np.asarray(codes, dtype=np.float32)
    if mode == "adc":
        return codes * (2.0 / 255.0)
    return (codes * (2.0 / 255.0) - 1.0) * 5.0


def make_envelope(codes, valid, pixels):
    count = int(codes.size)
    if count == 0:
        return np.empty(0), np.empty(0), np.empty(0, dtype=np.bool_)
    bins = min(max(1, pixels), count)
    boundaries = np.linspace(0, count, bins + 1, dtype=np.int64)
    minimum = np.minimum.reduceat(codes, boundaries[:-1])
    maximum = np.maximum.reduceat(codes, boundaries[:-1])
    validity = np.logical_and.reduceat(valid, boundaries[:-1])
    return minimum, maximum, validity


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AD9280 Continuous DAQ")
        self.resize(1180, 720)
        self.setMinimumSize(980, 620)
        self.setStyleSheet(STYLE)

        self.ring = SampleRingBuffer()
        self.control = None
        self.receiver = None
        self.status_poller = None
        self.serial_thread = None
        self.connected = False
        self.streaming = False
        self.frozen = False
        self.frozen_codes = np.empty(0, dtype=np.uint8)
        self.frozen_valid = np.empty(0, dtype=np.bool_)
        self.frozen_first_sample = 0
        self.metrics = {}
        self.board_status = None

        self.backend_combo = QComboBox()
        self.backend_combo.addItem("UDP 高速", "udp")
        self.backend_combo.addItem("UART 诊断", "uart")
        self.board_ip = QLineEdit("192.168.10.2")
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("刷新")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["115200", "230400", "460800", "921600"])
        self.rate_combo = QComboBox()
        for rate in (5, 10, 15, 20, 24):
            self.rate_combo.addItem(f"{rate} MSPS", rate * 1_000_000)
        self.rate_combo.setCurrentText("20 MSPS")
        self.timebase_combo = QComboBox()
        for label, seconds in TIMEBASES:
            self.timebase_combo.addItem(label, seconds)
        self.timebase_combo.setCurrentText("1 ms")
        self.refresh_rate_combo = QComboBox()
        for label, fps in DISPLAY_REFRESH_RATES:
            self.refresh_rate_combo.addItem(label, fps)
        self.refresh_rate_combo.setCurrentText("10 FPS")
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItem("自由运行", 0)
        self.trigger_combo.addItem("高于阈值", 1)
        self.trigger_combo.addItem("低于阈值", 2)
        self.trigger_combo.addItem("立即标记", 3)
        self.trigger_combo.addItem("外部触发", 4)
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 255)
        self.threshold_spin.setValue(128)
        self.voltage_combo = QComboBox()
        self.voltage_combo.addItem("模块 SMA -5 V 至 +5 V", "module")
        self.voltage_combo.addItem("AD9280 AIN 0 V 至 2 V", "adc")
        self.y_range_combo = QComboBox()
        self.y_range_combo.addItem("固定量程", "fixed")
        self.y_range_combo.addItem("自动量程", "auto")

        self.connect_button = QPushButton("连接")
        self.start_button = QPushButton("开始")
        self.stop_button = QPushButton("停止")
        self.freeze_button = QPushButton("冻结窗口")
        self.freeze_button.setCheckable(True)
        self.save_button = QPushButton("保存快照")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.freeze_button.setEnabled(False)
        self.save_button.setEnabled(False)

        self.plot = WaveformWidget()
        self.summary_label = QLabel("未连接")
        self.summary_label.setObjectName("Summary")
        self.health_label = QLabel("吞吐 --   丢包 --   FIFO --   DMA --")
        self.health_label.setObjectName("Health")
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self._build_ui()
        self._connect_signals()
        self.refresh_ports()
        self._update_backend()

        self.plot_timer = QTimer(self)
        self.plot_timer.setTimerType(Qt.PreciseTimer)
        self._update_plot_interval()
        self.plot_timer.timeout.connect(self.refresh_plot)
        self.plot_timer.start()

    def _build_ui(self):
        header = QHBoxLayout()
        title = QLabel("AD9280 连续采集")
        title.setObjectName("Title")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.summary_label)

        controls = QFrame()
        controls.setObjectName("Controls")
        form = QFormLayout(controls)
        form.setContentsMargins(16, 16, 16, 16)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.addRow("链路", self.backend_combo)
        form.addRow("板卡 IP", self.board_ip)
        port_row = QHBoxLayout()
        port_row.addWidget(self.port_combo, 1)
        port_row.addWidget(self.refresh_button)
        form.addRow("串口", port_row)
        form.addRow("波特率", self.baud_combo)
        form.addRow("采样率", self.rate_combo)
        form.addRow("时间基", self.timebase_combo)
        form.addRow("显示刷新", self.refresh_rate_combo)
        form.addRow("触发标记", self.trigger_combo)
        form.addRow("阈值", self.threshold_spin)
        form.addRow("输入量程", self.voltage_combo)
        form.addRow("Y 轴", self.y_range_combo)

        connect_row = QHBoxLayout()
        connect_row.addWidget(self.connect_button)
        connect_row.addWidget(self.start_button)
        connect_row.addWidget(self.stop_button)
        form.addRow(connect_row)
        snapshot_row = QHBoxLayout()
        snapshot_row.addWidget(self.freeze_button)
        snapshot_row.addWidget(self.save_button)
        form.addRow(snapshot_row)

        plot_panel = QFrame()
        plot_panel.setObjectName("Plot")
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.setContentsMargins(14, 12, 14, 12)
        plot_layout.addWidget(self.health_label)
        plot_layout.addWidget(self.plot, 1)

        content = QHBoxLayout()
        content.setSpacing(14)
        content.addWidget(controls)
        content.addWidget(plot_panel, 1)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(18, 14, 18, 14)
        root_layout.setSpacing(12)
        root_layout.addLayout(header)
        root_layout.addLayout(content, 1)
        root = QWidget()
        root.setLayout(root_layout)
        self.setCentralWidget(root)

    def _connect_signals(self):
        self.backend_combo.currentIndexChanged.connect(self._update_backend)
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_backend)
        self.start_button.clicked.connect(self.start_stream)
        self.stop_button.clicked.connect(self.stop_stream)
        self.freeze_button.clicked.connect(self.toggle_freeze)
        self.save_button.clicked.connect(self.save_snapshot)
        self.voltage_combo.currentIndexChanged.connect(self.refresh_plot)
        self.y_range_combo.currentIndexChanged.connect(self.refresh_plot)
        self.refresh_rate_combo.currentIndexChanged.connect(self._update_plot_interval)
        self.trigger_combo.currentIndexChanged.connect(
            lambda: self.threshold_spin.setEnabled(self.trigger_combo.currentData() in (1, 2))
        )

    def _update_plot_interval(self):
        fps = int(self.refresh_rate_combo.currentData() or 10)
        if hasattr(self, "plot_timer"):
            self.plot_timer.setInterval(max(1, round(1000 / fps)))

    def _update_backend(self):
        udp = self.backend_combo.currentData() == "udp"
        self.board_ip.setEnabled(udp)
        self.port_combo.setEnabled(not udp)
        self.refresh_button.setEnabled(not udp)
        self.baud_combo.setEnabled(not udp)
        self.connect_button.setText("连接板卡" if udp else "检查串口")
        self.stop_stream()
        self.connected = False
        self.start_button.setEnabled(False)

    def refresh_ports(self):
        current = self.port_combo.currentText()
        ports = [item.device for item in list_ports.comports()]
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)

    def connect_backend(self):
        if self.backend_combo.currentData() == "uart":
            port = self.port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "串口", "没有可用串口")
                return
            try:
                with serial.Serial(port, int(self.baud_combo.currentText()), timeout=0.2):
                    pass
            except Exception as exc:
                QMessageBox.critical(self, "串口连接失败", str(exc))
                return
            self.connected = True
            self.start_button.setEnabled(True)
            self.summary_label.setText(f"UART {port}")
            return

        try:
            socket.inet_aton(self.board_ip.text().strip())
            self.control = ControlClient(self.board_ip.text().strip(), timeout=0.6)
            response = self.control.request(Command.GET_INFO)
        except Exception as exc:
            QMessageBox.critical(self, "板卡连接失败", str(exc))
            return
        self.connected = True
        self.control.timeout = 0.2
        self.board_status = response
        self.start_button.setEnabled(True)
        self.summary_label.setText(
            f"{self.board_ip.text().strip()}   {response.sample_rate_hz / 1e6:.0f} MSPS"
        )
        self.status.showMessage("控制链路已连接", 3000)

    def start_stream(self):
        if not self.connected:
            self.connect_backend()
            if not self.connected:
                return
        if self.backend_combo.currentData() == "uart":
            self.start_uart_capture()
            return
        if self.streaming:
            return

        self.ring.clear()
        self.receiver = UdpReceiver(self.ring, DATA_PORT)
        self.receiver.metrics.connect(self.update_metrics)
        self.receiver.failed.connect(self.receiver_failed)
        self.receiver.start()
        if not self.receiver.wait_until_ready(1.0):
            message = self.receiver.startup_error or "UDP data port 5001 startup timed out"
            self.receiver.stop()
            self.receiver.wait(1000)
            self.receiver = None
            QMessageBox.critical(self, "UDP", message)
            return
        try:
            try:
                self.control.request(Command.STOP)
            except Exception:
                pass
            self.control.request(
                Command.CONFIG,
                sample_rate_hz=self.rate_combo.currentData(),
                trigger_mode=self.trigger_combo.currentData(),
                threshold=self.threshold_spin.value(),
            )
            response = self.control.request(Command.START, value0=DATA_PORT)
        except Exception as exc:
            self.receiver.stop()
            self.receiver.wait(1000)
            self.receiver = None
            QMessageBox.critical(self, "启动失败", str(exc))
            return

        self.streaming = True
        self.board_status = response
        self.status_poller = StatusPoller(self.control)
        self.status_poller.received.connect(self.update_board_status)
        self.status_poller.failed.connect(
            lambda message: self.status.showMessage(f"Status query failed: {message}", 1500)
        )
        self.status_poller.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.freeze_button.setEnabled(True)
        self.summary_label.setText(
            f"运行中   {response.sample_rate_hz / 1e6:.0f} MSPS   Stream {response.stream_id}"
        )

    def start_uart_capture(self):
        if self.serial_thread is not None and self.serial_thread.isRunning():
            return
        config = SerialConfig(
            self.port_combo.currentText(),
            int(self.baud_combo.currentText()),
            self.rate_combo.currentData() // 1_000_000,
        )
        self.serial_thread = SerialCaptureThread(config)
        self.serial_thread.captured.connect(self.uart_captured)
        self.serial_thread.failed.connect(
            lambda message: QMessageBox.critical(self, "UART 采集失败", message)
        )
        self.serial_thread.start()

    def uart_captured(self, codes, elapsed):
        valid = np.ones(codes.size, dtype=np.bool_)
        minimum, maximum, valid_bins = make_envelope(codes, valid, self.plot.width())
        self._show_envelope(minimum, maximum, valid_bins, codes.size / self.rate_combo.currentData())
        self.frozen_codes = codes
        self.frozen_valid = valid
        self.save_button.setEnabled(True)
        self.health_label.setText(f"UART 单帧   {codes.size} samples   {elapsed:.3f} s")

    def stop_stream(self):
        if self.status_poller is not None:
            self.status_poller.stop()
            self.status_poller.wait(500)
            self.status_poller = None
        if self.control is not None and self.streaming:
            try:
                self.control.request(Command.STOP)
            except Exception:
                pass
        if self.receiver is not None:
            self.receiver.stop()
            self.receiver.wait(1200)
            self.receiver = None
        self.streaming = False
        self.stop_button.setEnabled(False)
        self.freeze_button.setEnabled(False)
        self.freeze_button.setChecked(False)
        self.frozen = False
        if self.connected:
            self.start_button.setEnabled(True)

    def toggle_freeze(self, checked):
        self.frozen = bool(checked)
        self.freeze_button.setText("继续滚动" if checked else "冻结窗口")
        if checked:
            count = int(self.rate_combo.currentData() * self.timebase_combo.currentData())
            codes, valid, first = self.ring.snapshot(count)
            self.frozen_codes = codes
            self.frozen_valid = valid
            self.frozen_first_sample = first
            self.save_button.setEnabled(codes.size > 0)
            self.refresh_plot()

    def _show_envelope(self, minimum, maximum, valid, duration):
        mode = self.voltage_combo.currentData()
        minimum_v = codes_to_voltage(minimum, mode)
        maximum_v = codes_to_voltage(maximum, mode)
        y_label = "AD9280 AIN / V" if mode == "adc" else "SMA input / V"
        y_range = None
        if self.y_range_combo.currentData() == "fixed":
            y_range = (0.0, 2.0) if mode == "adc" else (-5.0, 5.0)
        self.plot.set_envelope(minimum_v, maximum_v, valid, duration, y_label, y_range)

    def refresh_plot(self):
        if self.frozen and self.frozen_codes.size:
            minimum, maximum, valid = make_envelope(
                self.frozen_codes, self.frozen_valid, self.plot.width()
            )
            duration = self.frozen_codes.size / max(1, self.rate_combo.currentData())
            self._show_envelope(minimum, maximum, valid, duration)
            return
        if not self.streaming:
            return
        sample_rate = self.metrics.get("sample_rate_hz") or self.rate_combo.currentData()
        duration = self.timebase_combo.currentData()
        result = self.ring.envelope(int(sample_rate * duration), self.plot.width())
        if result is None:
            return
        minimum, maximum, valid, _, _ = result
        self._show_envelope(minimum, maximum, valid, duration)

    def update_metrics(self, metrics):
        self.metrics = metrics
        flags = metrics["flags"]
        board = self.board_status
        overflow_count = board.fifo_overflow if board is not None else 0
        dma_errors = board.dma_errors if board is not None else 0
        board_drops = board.blocks_dropped if board is not None else 0
        fifo = "溢出" if flags & FLAG_FIFO_OVERFLOW else (
            "满" if flags & FLAG_FIFO_FULL else "正常"
        )
        dma = "错误" if flags & FLAG_DMA_ERROR else "正常"
        self.health_label.setText(
            f"吞吐 {metrics['throughput_mbps']:.1f} Mbit/s   "
            f"包 {metrics['packets']}   丢包 {metrics['packet_loss']}   "
            f"丢块 {metrics['block_loss']} / 板卡 {board_drops}   "
            f"FIFO {fifo}({overflow_count})   DMA {dma}({dma_errors})"
        )

    def poll_status(self):
        if not self.streaming or self.control is None:
            return
        try:
            self.board_status = self.control.request(Command.STATUS)
        except Exception as exc:
            self.status.showMessage(f"状态查询失败: {exc}", 1500)

    def update_board_status(self, response):
        self.board_status = response

    def receiver_failed(self, message):
        if self.streaming:
            self.stop_stream()
            QMessageBox.critical(self, "UDP 接收失败", message)

    def save_snapshot(self):
        if self.frozen_codes.size == 0:
            return
        path, selected = QFileDialog.getSaveFileName(
            self,
            "保存冻结窗口",
            "ad9280_snapshot.npy",
            "NumPy (*.npy);;CSV (*.csv)",
        )
        if not path:
            return
        if selected.startswith("NumPy") or path.lower().endswith(".npy"):
            if not path.lower().endswith(".npy"):
                path += ".npy"
            np.save(path, self.frozen_codes)
        else:
            if not path.lower().endswith(".csv"):
                path += ".csv"
            voltages = codes_to_voltage(self.frozen_codes, self.voltage_combo.currentData())
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["absolute_sample", "adc_code_8bit", "voltage", "valid"])
                for index, (code, voltage, valid) in enumerate(
                    zip(self.frozen_codes, voltages, self.frozen_valid)
                ):
                    writer.writerow(
                        [self.frozen_first_sample + index, int(code), float(voltage), int(valid)]
                    )
        self.status.showMessage(f"已保存 {path}", 4000)

    def closeEvent(self, event):
        self.stop_stream()
        event.accept()


STYLE = """
QMainWindow { background: #eef1f5; }
QLabel#Title { color: #172033; font-size: 22px; font-weight: 700; }
QLabel#Summary { color: #334155; font-size: 13px; font-weight: 600; }
QLabel#Health { color: #334155; padding: 3px 2px; }
QFrame#Controls, QFrame#Plot {
    background: #ffffff;
    border: 1px solid #d5dce6;
    border-radius: 6px;
}
QFrame#Controls { min-width: 310px; max-width: 350px; }
QLabel { color: #293548; }
QLineEdit, QComboBox, QSpinBox {
    min-height: 30px;
    padding: 2px 8px;
    border: 1px solid #c5ceda;
    border-radius: 5px;
    background: #fbfcfe;
    color: #172033;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #2868c7; }
QPushButton {
    min-height: 32px;
    padding: 3px 12px;
    border: 1px solid #bdc7d5;
    border-radius: 5px;
    background: #ffffff;
    color: #243247;
    font-weight: 600;
}
QPushButton:hover { background: #f1f5fa; }
QPushButton:disabled { color: #9aa5b3; background: #f3f5f8; }
QPushButton:checked { color: #ffffff; background: #315e9f; border-color: #315e9f; }
QStatusBar { background: #eef1f5; color: #526075; }
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AD9280 Continuous DAQ")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
