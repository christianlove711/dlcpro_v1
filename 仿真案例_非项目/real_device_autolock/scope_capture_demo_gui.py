from __future__ import annotations

import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from tektronix_scope_capture import capture_once, query_idn, require_pyvisa


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "scope_captures"
LATEST_CSV = CAPTURE_DIR / "latest_scope_frame.csv"


@dataclass(frozen=True)
class SignalFrame:
    time_s: list[float]
    transmission_v: list[float]
    error_v: list[float]


def load_signal_frame(path: Path) -> SignalFrame:
    time_s: list[float] = []
    transmission_v: list[float] = []
    error_v: list[float] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_s.append(float(row["time"]))
            transmission_v.append(float(row["transmission"]))
            error_v.append(float(row["error"]))
    if not time_s:
        raise RuntimeError(f"CSV is empty: {path}")
    t0 = time_s[0]
    time_s = [t - t0 for t in time_s]
    return SignalFrame(time_s, transmission_v, error_v)


def frame_summary(frame: SignalFrame, path: Path) -> str:
    def limits(values: list[float]) -> tuple[float, float, float]:
        return min(values), max(values), sum(values) / len(values)

    t_span = frame.time_s[-1] - frame.time_s[0]
    trans_min, trans_max, trans_mean = limits(frame.transmission_v)
    err_min, err_max, err_mean = limits(frame.error_v)
    return (
        f"CSV: {path}\n"
        f"Samples: {len(frame.time_s)}    Time span: {t_span:.6g} s\n"
        f"Transmission: min {trans_min:.6g} V, max {trans_max:.6g} V, mean {trans_mean:.6g} V\n"
        f"Error:        min {err_min:.6g} V, max {err_max:.6g} V, mean {err_mean:.6g} V"
    )


class CaptureWorker(QObject):
    finished = Signal(str, str)
    failed = Signal(str)

    def __init__(
        self,
        resource: str,
        output: Path,
        points: int | None,
        transmission_channel: int,
        error_channel: int,
    ) -> None:
        super().__init__()
        self.resource = resource
        self.output = output
        self.points = points
        self.transmission_channel = transmission_channel
        self.error_channel = error_channel

    @Slot()
    def run(self) -> None:
        try:
            capture_once(
                self.resource,
                self.output,
                self.points,
                self.transmission_channel,
                self.error_channel,
            )
            self.finished.emit(str(self.output), time.strftime("%H:%M:%S"))
        except Exception as exc:
            self.failed.emit(str(exc))


class ScopeCaptureDemo(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tektronix Scope Capture Demo")
        self.resize(1200, 760)

        self.worker_thread: QThread | None = None
        self.current_worker: CaptureWorker | None = None
        self.capture_running = False
        self.loop_timer = QTimer(self)
        self.loop_timer.timeout.connect(self.capture_frame)

        self.connection_type = QComboBox()
        self.connection_type.addItems(["LAN Socket", "USB / VISA"])
        self.connection_type.currentTextChanged.connect(self.update_connection_form)

        self.lan_ip = QLineEdit("169.254.101.103")
        self.lan_port = QSpinBox()
        self.lan_port.setRange(1, 65535)
        self.lan_port.setValue(4000)

        self.usb_resource = QComboBox()
        self.usb_resource.setEditable(True)
        self.refresh_usb_button = QPushButton("刷新 USB")
        self.refresh_usb_button.clicked.connect(self.refresh_usb_resources)

        self.transmission_channel = QSpinBox()
        self.transmission_channel.setRange(1, 4)
        self.transmission_channel.setValue(1)
        self.error_channel = QSpinBox()
        self.error_channel.setRange(1, 4)
        self.error_channel.setValue(2)

        self.points_mode = QComboBox()
        self.points_mode.addItems(["完整屏幕记录长度", "手动点数"])
        self.points_mode.currentTextChanged.connect(self.update_points_state)
        self.points = QSpinBox()
        self.points.setRange(100, 5_000_000)
        self.points.setValue(10000)
        self.points.setEnabled(False)

        self.interval = QDoubleSpinBox()
        self.interval.setRange(0.5, 60.0)
        self.interval.setDecimals(1)
        self.interval.setSingleStep(0.5)
        self.interval.setValue(3.0)
        self.interval.setSuffix(" s")

        self.test_button = QPushButton("测试连接")
        self.capture_button = QPushButton("采集一帧并刷新")
        self.start_button = QPushButton("开始慢速刷新")
        self.stop_button = QPushButton("停止")
        self.load_csv_button = QPushButton("打开已有 CSV")

        self.test_button.clicked.connect(self.test_connection)
        self.capture_button.clicked.connect(self.capture_frame)
        self.start_button.clicked.connect(self.start_loop)
        self.stop_button.clicked.connect(self.stop_loop)
        self.load_csv_button.clicked.connect(self.open_csv)
        self.stop_button.setEnabled(False)

        self.status_label = QLabel("未连接")
        self.status_label.setObjectName("statusLabel")

        self.figure = Figure(figsize=(8, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.summary = QPlainTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setMaximumHeight(120)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)

        self.lan_rows: list[QWidget] = [self.lan_ip, self.lan_port]
        self.usb_rows: list[QWidget] = [self.usb_resource, self.refresh_usb_button]

        self.setCentralWidget(self.build_ui())
        self.apply_style()
        self.update_connection_form()
        self.plot_empty()
        if LATEST_CSV.exists():
            self.load_and_plot(LATEST_CSV)

    def build_ui(self) -> QWidget:
        root = QWidget()
        main = QGridLayout(root)
        main.setColumnStretch(0, 0)
        main.setColumnStretch(1, 1)
        main.setRowStretch(0, 1)

        left = QVBoxLayout()
        left.addWidget(self.build_connection_group())
        left.addWidget(self.build_capture_group())
        left.addWidget(self.build_log_group(), 1)
        main.addLayout(left, 0, 0)

        right = QVBoxLayout()
        right.addWidget(self.status_label)
        right.addWidget(self.canvas, 1)
        right.addWidget(self.summary)
        main.addLayout(right, 0, 1)
        return root

    def build_connection_group(self) -> QGroupBox:
        group = QGroupBox("示波器连接")
        form = QFormLayout(group)
        form.addRow("连接方式", self.connection_type)
        form.addRow("LAN IP", self.lan_ip)
        form.addRow("LAN Port", self.lan_port)

        usb_line = QHBoxLayout()
        usb_line.addWidget(self.usb_resource, 1)
        usb_line.addWidget(self.refresh_usb_button)
        form.addRow("USB Resource", usb_line)

        buttons = QHBoxLayout()
        buttons.addWidget(self.test_button)
        buttons.addWidget(self.load_csv_button)
        form.addRow(buttons)
        return group

    def build_capture_group(self) -> QGroupBox:
        group = QGroupBox("采集设置")
        form = QFormLayout(group)
        form.addRow("Transmission 通道", self.transmission_channel)
        form.addRow("Error 通道", self.error_channel)
        form.addRow("采样长度", self.points_mode)
        form.addRow("手动点数", self.points)
        form.addRow("刷新间隔", self.interval)

        buttons = QHBoxLayout()
        buttons.addWidget(self.capture_button)
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.stop_button)
        form.addRow(buttons)
        return group

    def build_log_group(self) -> QGroupBox:
        group = QGroupBox("日志")
        layout = QVBoxLayout(group)
        layout.addWidget(self.log)
        return group

    def apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f6f7f9;
                color: #1f2933;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #d5dbe3;
                border-radius: 6px;
                margin-top: 10px;
                padding: 12px 10px 10px 10px;
                background: #ffffff;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
                background: #ffffff;
                border: 1px solid #c8d0da;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background: #245c9f;
                color: white;
                border: 0;
                border-radius: 5px;
                padding: 7px 10px;
                min-height: 22px;
            }
            QPushButton:disabled {
                background: #aab4c0;
            }
            QPushButton:hover:!disabled {
                background: #1e4f8a;
            }
            QLabel#statusLabel {
                background: #ffffff;
                border: 1px solid #d5dbe3;
                border-radius: 6px;
                padding: 8px 10px;
                font-weight: 600;
            }
            """
        )

    def resource(self) -> str:
        if self.connection_type.currentText().startswith("LAN"):
            return f"SOCKET::{self.lan_ip.text().strip()}::{self.lan_port.value()}"
        return self.usb_resource.currentText().strip()

    def selected_points(self) -> int | None:
        if self.points_mode.currentText().startswith("完整"):
            return None
        return self.points.value()

    @Slot()
    def update_connection_form(self) -> None:
        is_lan = self.connection_type.currentText().startswith("LAN")
        self.lan_ip.setEnabled(is_lan)
        self.lan_port.setEnabled(is_lan)
        self.usb_resource.setEnabled(not is_lan)
        self.refresh_usb_button.setEnabled(not is_lan)

    @Slot()
    def update_points_state(self) -> None:
        self.points.setEnabled(self.points_mode.currentText().startswith("手动"))

    @Slot()
    def refresh_usb_resources(self) -> None:
        self.usb_resource.clear()
        try:
            pyvisa = require_pyvisa()
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            self.usb_resource.addItems(resources)
            self.append_log(f"找到 {len(resources)} 个 VISA resource。")
        except Exception as exc:
            self.append_log(f"刷新 USB/VISA 失败：{exc}")
            QMessageBox.warning(self, "USB/VISA", f"刷新 USB/VISA 失败：\n{exc}")

    @Slot()
    def test_connection(self) -> None:
        resource = self.resource()
        if not resource:
            QMessageBox.warning(self, "连接测试", "请先输入示波器资源。")
            return
        self.set_busy(True)
        QApplication.processEvents()
        try:
            idn = query_idn(resource, timeout_ms=2500)
            if idn:
                self.status_label.setText(f"连接成功：{idn}")
                self.append_log(f"连接成功：{resource} -> {idn}")
            else:
                self.status_label.setText("连接失败：没有收到 *IDN? 响应")
                self.append_log(f"连接失败：{resource}")
        except Exception as exc:
            self.status_label.setText("连接失败")
            self.append_log(f"连接失败：{exc}")
        finally:
            self.set_busy(False)

    @Slot()
    def capture_frame(self) -> None:
        if self.capture_running:
            return
        resource = self.resource()
        if not resource:
            QMessageBox.warning(self, "采集", "请先输入示波器资源。")
            return
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        output = LATEST_CSV
        stamp = time.strftime("%H:%M:%S")
        self.append_log(f"{stamp} 开始采集：{resource}")
        self.start_worker(resource, output)

    def start_worker(self, resource: str, output: Path) -> None:
        self.capture_running = True
        self.set_busy(True)
        self.worker_thread = QThread(self)
        worker = CaptureWorker(
            resource,
            output,
            self.selected_points(),
            self.transmission_channel.value(),
            self.error_channel.value(),
        )
        self.current_worker = worker
        worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(worker.run)
        worker.finished.connect(self.capture_finished)
        worker.failed.connect(self.capture_failed)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.finished.connect(self.worker_thread.quit)
        worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.clear_worker)
        self.worker_thread.start()

    @Slot(str, str)
    def capture_finished(self, csv_path: str, finished_at: str) -> None:
        self.capture_running = False
        self.set_busy(False)
        path = Path(csv_path)
        self.append_log(f"{finished_at} 采集完成：{path}")
        self.load_and_plot(path)

    @Slot(str)
    def capture_failed(self, message: str) -> None:
        self.capture_running = False
        self.set_busy(False)
        self.append_log(f"采集失败：{message}")
        self.status_label.setText("采集失败")

    @Slot()
    def start_loop(self) -> None:
        self.loop_timer.start(int(self.interval.value() * 1000))
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.capture_frame()
        self.append_log("开始慢速刷新。")

    @Slot()
    def stop_loop(self) -> None:
        self.loop_timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.append_log("停止慢速刷新。")

    @Slot()
    def open_csv(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "打开示波器 CSV",
            str(CAPTURE_DIR),
            "CSV Files (*.csv);;All Files (*.*)",
        )
        if file_name:
            self.load_and_plot(Path(file_name))

    def load_and_plot(self, path: Path) -> None:
        try:
            frame = load_signal_frame(path)
        except Exception as exc:
            self.append_log(f"读取 CSV 失败：{exc}")
            return
        self.plot_frame(frame)
        summary = frame_summary(frame, path)
        self.summary.setPlainText(summary)
        self.status_label.setText(summary.splitlines()[1])

    def plot_empty(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_title("等待采集 CSV")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(True, alpha=0.25)
        self.canvas.draw_idle()

    def plot_frame(self, frame: SignalFrame) -> None:
        self.figure.clear()
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212, sharex=ax1)
        ax1.plot(frame.time_s, frame.transmission_v, color="#1f77b4", linewidth=0.8)
        ax1.set_ylabel("Transmission (V)")
        ax1.grid(True, alpha=0.25)
        ax1.set_title("Transmission")

        ax2.plot(frame.time_s, frame.error_v, color="#d62728", linewidth=0.8)
        ax2.set_ylabel("Error (V)")
        ax2.set_xlabel("Time (s)")
        ax2.grid(True, alpha=0.25)
        ax2.set_title("PDH Error")
        self.canvas.draw_idle()

    def set_busy(self, busy: bool) -> None:
        self.test_button.setEnabled(not busy)
        self.capture_button.setEnabled(not busy)
        self.load_csv_button.setEnabled(not busy)
        self.connection_type.setEnabled(not busy)
        self.transmission_channel.setEnabled(not busy)
        self.error_channel.setEnabled(not busy)
        self.points_mode.setEnabled(not busy)
        self.update_points_state()
        if busy:
            self.points.setEnabled(False)

    def append_log(self, message: str) -> None:
        self.log.appendPlainText(message)

    @Slot()
    def clear_worker(self) -> None:
        self.worker_thread = None
        self.current_worker = None


def main() -> int:
    app = QApplication(sys.argv)
    window = ScopeCaptureDemo()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
