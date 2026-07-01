from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import rcParams
from matplotlib.figure import Figure

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from one_click_lock_app.algorithms.waveform_analysis import analyze_lock_candidate, downsample_xy
from one_click_lock_app.controllers.autolock_controller import AutoLockController, AutoLockPhase
from one_click_lock_app.models import DlcSnapshot, SignalFrame
from one_click_lock_app.services.dlcpro_service import DlcproService
from one_click_lock_app.services.scope_service import ScopeService, load_signal_frame


class TaskWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(self.fn())
        except Exception as exc:
            self.failed.emit(str(exc))


class StatusText(QPlainTextEdit):
    def __init__(self, text: str = "", max_height: int = 72) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(max_height)
        self.setPlainText(text)

    def setText(self, text: str) -> None:
        self.setPlainText(text)


class ConnectionBadge(QWidget):
    def __init__(self, label: str, detail: str = "未连接") -> None:
        super().__init__()
        self.setObjectName("ConnectionBadge")
        self.dot = QLabel("●")
        self.dot.setFixedWidth(16)
        self.text = QLabel(f"{label}: {detail}")
        self.text.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        layout.addWidget(self.dot)
        layout.addWidget(self.text)
        self.set_state(label, detail, False)

    def set_state(self, label: str, detail: str, connected: bool | None) -> None:
        color = "#16a34a" if connected else "#dc2626"
        if connected is None:
            color = "#d97706"
        self.dot.setStyleSheet(f"color: {color}; font-size: 16px;")
        self.text.setText(f"{label}: {detail}")


class ToolWindow(QMainWindow):
    def __init__(self, title: str, content: QWidget) -> None:
        super().__init__()
        self.force_close = False
        self.setWindowTitle(title)
        self.resize(520, 420)
        self.setCentralWidget(content)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.force_close:
            event.accept()
            return
        event.ignore()
        self.hide()

    def shutdown_close(self) -> None:
        self.force_close = True
        self.close()


class LogWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.force_close = False
        self.setWindowTitle("操作 / 自动锁频日志")
        self.resize(920, 600)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)

        self.process_log = QPlainTextEdit()
        self.process_log.setReadOnly(True)
        self.setCentralWidget(self.process_log)

    def append_process(self, message: str) -> None:
        self.process_log.appendPlainText(message)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.force_close:
            event.accept()
            return
        event.ignore()
        self.hide()

    def shutdown_close(self) -> None:
        self.force_close = True
        self.close()


class OneClickLockWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MSO64B + DLC pro 一键锁频")
        self.resize(1380, 860)

        self.scope = ScopeService()
        self.dlc = DlcproService()
        self.autolock = AutoLockController()
        self.log_window = LogWindow()
        self.scope_resource: str | None = None
        self.snapshot: DlcSnapshot | None = None
        self.last_frame: SignalFrame | None = None
        self.worker_thread: QThread | None = None
        self.worker: TaskWorker | None = None
        self.auto_apply_timers: dict[str, QTimer] = {}
        self.rendering_snapshot = False
        self.shutting_down = False
        self.step_button_groups: list[QButtonGroup] = []

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(2500)
        self.poll_timer.timeout.connect(self.refresh_dlc_snapshot)

        self.build_widgets()
        self.setCentralWidget(self.build_layout())
        self.apply_style()
        self.plot_empty()

    def make_gain_spin(self) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(-1_000_000.0, 1_000_000.0)
        spin.setDecimals(6)
        spin.setSingleStep(0.1)
        spin.setAccelerated(True)
        spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        spin.setKeyboardTracking(False)
        return spin

    def make_step_combo(self, steps: list[float], default: float) -> QComboBox:
        combo = QComboBox()
        for step in steps:
            combo.addItem(f"{step:g}", step)
        index = combo.findData(default)
        if index >= 0:
            combo.setCurrentIndex(index)
        return combo

    def configure_spin(self, spin: QDoubleSpinBox, step: float) -> None:
        spin.setSingleStep(step)
        spin.setAccelerated(True)
        spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        spin.setKeyboardTracking(False)

    def set_step_spin_active(self, spin: QDoubleSpinBox, active: bool) -> None:
        spin.setReadOnly(not active)
        spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows if active else QAbstractSpinBox.NoButtons)
        spin.setFocusPolicy(Qt.StrongFocus if active else Qt.NoFocus)
        spin.setProperty("stepActive", active)
        spin.style().unpolish(spin)
        spin.style().polish(spin)

    def update_step_target_state(self, mapping: dict[str, QDoubleSpinBox], active_key: str, step: float) -> None:
        for key, spin in mapping.items():
            active = key == active_key
            self.set_step_spin_active(spin, active)
            if active:
                spin.setSingleStep(max(step, 0.000001))

    def create_step_buttons(self, steps: tuple[float, ...], default: float, callback: Callable[[float], None]) -> list[QPushButton]:
        buttons: list[QPushButton] = []
        group = QButtonGroup(self)
        group.setExclusive(True)
        self.step_button_groups.append(group)
        for step in steps:
            button = QPushButton(f"{step:g}")
            button.setObjectName("StepButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, value=step: callback(value))
            if step == default:
                button.setChecked(True)
            group.addButton(button)
            buttons.append(button)
        return buttons

    def make_target_button(self, callback: Callable[[], None]) -> QPushButton:
        button = QPushButton("当前调节")
        button.setObjectName("TargetButton")
        button.setCheckable(True)
        button.clicked.connect(lambda _checked=False: callback())
        return button

    def build_widgets(self) -> None:
        self.scope_mode = QComboBox()
        self.scope_mode.addItems(["LAN Socket", "USB/VISA"])
        self.scope_ip = QLineEdit("192.168.43.20")
        self.scope_port = QSpinBox()
        self.scope_port.setRange(1, 65535)
        self.scope_port.setValue(4000)
        self.scope_usb = QLineEdit("")
        self.scope_trans_ch = QSpinBox()
        self.scope_trans_ch.setRange(1, 4)
        self.scope_trans_ch.setValue(1)
        self.scope_err_ch = QSpinBox()
        self.scope_err_ch.setRange(1, 4)
        self.scope_err_ch.setValue(2)
        self.scope_points = QSpinBox()
        self.scope_points.setRange(0, 5_000_000)
        self.scope_points.setValue(0)
        self.scope_points.setSpecialValueText("完整屏幕")
        self.scope_connect_btn = QPushButton("连接示波器")
        self.scope_capture_btn = QPushButton("采集一帧")
        self.open_csv_btn = QPushButton("打开 CSV")
        self.scope_badge = ConnectionBadge("示波器", "未连接")

        self.dlc_mode = QComboBox()
        self.dlc_mode.addItems(["LAN", "USB/Serial"])
        self.dlc_host = QLineEdit("192.168.43.30")
        self.dlc_subnet_mask = QLineEdit("255.255.255.0")
        self.dlc_cmd_port = QSpinBox()
        self.dlc_cmd_port.setRange(1, 65535)
        self.dlc_cmd_port.setValue(1998)
        self.dlc_mon_port = QSpinBox()
        self.dlc_mon_port.setRange(0, 65535)
        self.dlc_mon_port.setValue(1999)
        self.dlc_timeout = QDoubleSpinBox()
        self.dlc_timeout.setRange(0.5, 60.0)
        self.dlc_timeout.setDecimals(1)
        self.dlc_timeout.setValue(5.0)
        self.dlc_timeout.setSuffix(" s")
        self.dlc_serial = QLineEdit("COM3")
        self.dlc_baudrate = QSpinBox()
        self.dlc_baudrate.setRange(1200, 1_000_000)
        self.dlc_baudrate.setValue(115200)
        self.dlc_connect_btn = QPushButton("连接 DLC pro")
        self.dlc_refresh_btn = QPushButton("刷新 DLC 状态")
        self.dlc_badge = ConnectionBadge("DLC pro", "未连接")

        self.scan_offset = QDoubleSpinBox()
        self.scan_offset.setRange(-1000.0, 1000.0)
        self.scan_offset.setDecimals(4)
        self.scan_offset.setSuffix(" V")
        self.configure_spin(self.scan_offset, 0.01)
        self.scan_amp = QDoubleSpinBox()
        self.scan_amp.setRange(0.001, 1000.0)
        self.scan_amp.setDecimals(4)
        self.scan_amp.setValue(1.0)
        self.scan_amp.setSuffix(" Vpp")
        self.configure_spin(self.scan_amp, 0.01)
        self.scan_freq = QDoubleSpinBox()
        self.scan_freq.setRange(0.001, 1000.0)
        self.scan_freq.setDecimals(3)
        self.scan_freq.setValue(1.0)
        self.scan_freq.setSuffix(" Hz")
        self.configure_spin(self.scan_freq, 0.1)
        self.scan_step_value = 0.01
        self.scan_step_target = "amplitude"
        self.scan_step_buttons: list[QPushButton] = []
        self.scan_step_group = QButtonGroup(self)
        self.scan_step_group.setExclusive(True)
        for step in (100.0, 10.0, 1.0, 0.1, 0.01, 0.001, 0.0001, 0.00001, 0.000001):
            button = QPushButton(f"{step:g}")
            button.setObjectName("StepButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, value=step: self.select_scan_step(value))
            if step == self.scan_step_value:
                button.setChecked(True)
            self.scan_step_group.addButton(button)
            self.scan_step_buttons.append(button)
        self.scan_amp_target_btn = QPushButton("当前调节")
        self.scan_offset_target_btn = QPushButton("当前调节")
        self.scan_freq_target_btn = QPushButton("当前调节")
        self.scan_target_buttons = {
            "amplitude": self.scan_amp_target_btn,
            "offset": self.scan_offset_target_btn,
            "frequency": self.scan_freq_target_btn,
        }
        self.scan_target_group = QButtonGroup(self)
        self.scan_target_group.setExclusive(True)
        for target, button in self.scan_target_buttons.items():
            button.setObjectName("TargetButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, name=target: self.select_scan_target(name))
            self.scan_target_group.addButton(button)
        self.scan_amp_target_btn.setChecked(True)
        self.scan_enabled_check = QCheckBox("Enable")
        self.scan_hold_check = QCheckBox("Hold")
        self.scan_output = QComboBox()
        for label, value in [
            ("PC Voltage", 50),
            ("CC Current", 51),
            ("Out A", 20),
            ("Out B", 21),
            ("EOM Voltage Slow", 58),
            ("TC Set Temperature", 56),
        ]:
            self.scan_output.addItem(label, value)
        self.scan_shape = QComboBox()
        self.scan_shape.addItem("Triangle", 1)
        self.scan_shape.addItem("Sine", 0)
        self.configure_scan_btn = QPushButton("配置 1 Hz Piezo 扫描")
        self.apply_scan_btn = QPushButton("应用 SC/Master")
        self.scan_enable_btn = QPushButton("开启 Scan")
        self.scan_disable_btn = QPushButton("关闭 Scan")
        self.scan_status = StatusText("Scan 状态未知", max_height=88)

        self.lock_enabled_check = QCheckBox("Enable")
        self.lock_hold_check = QCheckBox("Hold")
        self.lock_input_signal = QComboBox()
        for label, value in [
            ("Fine In 1", 0),
            ("Fine In 2", 1),
            ("Fast In 3", 2),
            ("Fast In 4", 4),
            ("PDH In 1", 41),
            ("PDH In 2", 43),
        ]:
            self.lock_input_signal.addItem(label, value)
        self.lock_type = QComboBox()
        self.lock_type.addItem("Top of Fringe", 1)
        self.lock_type.addItem("Side of Fringe", 2)
        self.lock_type.addItem("Top of Fringe PDH", 3)
        self.error_signal = QComboBox()
        for label, value in [
            ("Fine In 1", 0),
            ("Fine In 2", 1),
            ("Fast In 3", 2),
            ("Fast In 4", 4),
            ("PDH Error 1", 40),
            ("PDH Error 2", 42),
        ]:
            self.error_signal.addItem(label, value)
        self.error_inverted_check = QCheckBox()
        self.pid_selection = QComboBox()
        self.pid_selection.addItem("None", 0)
        self.pid_selection.addItem("PID 1", 1)
        self.pid_selection.addItem("PID 2", 2)
        self.pid_selection.addItem("PID 1+2", 3)
        self.lock_without_lockpoint_check = QCheckBox()
        self.apply_lock_settings_btn = QPushButton("应用 Lock Settings")

        self.pid1_gain_all = self.make_gain_spin()
        self.pid1_gain_p = self.make_gain_spin()
        self.pid1_gain_i = self.make_gain_spin()
        self.pid1_gain_d = self.make_gain_spin()
        self.pid2_gain_all = self.make_gain_spin()
        self.pid2_gain_p = self.make_gain_spin()
        self.pid2_gain_i = self.make_gain_spin()
        self.pid2_gain_d = self.make_gain_spin()
        self.pid_step_value = 0.01
        self.pid_step_target = "pid1_gain_all"
        self.pid_step_buttons = self.create_step_buttons(
            (100.0, 10.0, 1.0, 0.1, 0.01, 0.001, 0.0001, 0.00001, 0.000001),
            self.pid_step_value,
            self.select_pid_step,
        )
        self.pid_target_buttons = {
            "pid1_gain_all": self.make_target_button(lambda: self.select_pid_target("pid1_gain_all")),
            "pid1_gain_p": self.make_target_button(lambda: self.select_pid_target("pid1_gain_p")),
            "pid1_gain_i": self.make_target_button(lambda: self.select_pid_target("pid1_gain_i")),
            "pid1_gain_d": self.make_target_button(lambda: self.select_pid_target("pid1_gain_d")),
            "pid2_gain_all": self.make_target_button(lambda: self.select_pid_target("pid2_gain_all")),
            "pid2_gain_p": self.make_target_button(lambda: self.select_pid_target("pid2_gain_p")),
            "pid2_gain_i": self.make_target_button(lambda: self.select_pid_target("pid2_gain_i")),
            "pid2_gain_d": self.make_target_button(lambda: self.select_pid_target("pid2_gain_d")),
        }
        self.pid_target_group = QButtonGroup(self)
        self.pid_target_group.setExclusive(True)
        for button in self.pid_target_buttons.values():
            self.pid_target_group.addButton(button)
        self.pid_target_buttons[self.pid_step_target].setChecked(True)
        self.apply_pid1_btn = QPushButton("应用 PID 1")
        self.apply_pid2_btn = QPushButton("应用 PID 2")

        self.lockin_enabled_check = QCheckBox("Enable")
        self.lockin_freq = QDoubleSpinBox()
        self.lockin_freq.setRange(0.0, 10_000_000.0)
        self.lockin_freq.setDecimals(1)
        self.lockin_freq.setSuffix(" Hz")
        self.configure_spin(self.lockin_freq, 1.0)
        self.lockin_amp = QDoubleSpinBox()
        self.lockin_amp.setRange(0.0, 1000.0)
        self.lockin_amp.setDecimals(6)
        self.lockin_amp.setSuffix(" V")
        self.configure_spin(self.lockin_amp, 0.001)
        self.lockin_step_value = 0.001
        self.lockin_step_target = "amplitude"
        self.lockin_step_buttons = self.create_step_buttons(
            (100.0, 10.0, 1.0, 0.1, 0.01, 0.001, 0.0001, 0.00001, 0.000001),
            self.lockin_step_value,
            self.select_lockin_step,
        )
        self.lockin_target_buttons = {
            "frequency": self.make_target_button(lambda: self.select_lockin_target("frequency")),
            "amplitude": self.make_target_button(lambda: self.select_lockin_target("amplitude")),
        }
        self.lockin_target_group = QButtonGroup(self)
        self.lockin_target_group.setExclusive(True)
        for button in self.lockin_target_buttons.values():
            self.lockin_target_group.addButton(button)
        self.lockin_target_buttons[self.lockin_step_target].setChecked(True)
        self.apply_lockin_btn = QPushButton("应用 Lock-In")

        self.cc_set_current = QDoubleSpinBox()
        self.cc_set_current.setRange(-1000.0, 1000.0)
        self.cc_set_current.setDecimals(6)
        self.cc_set_current.setSuffix(" mA")
        self.configure_spin(self.cc_set_current, 0.01)
        self.pc_set_voltage = QDoubleSpinBox()
        self.pc_set_voltage.setRange(-1000.0, 1000.0)
        self.pc_set_voltage.setDecimals(6)
        self.pc_set_voltage.setSuffix(" V")
        self.configure_spin(self.pc_set_voltage, 0.01)
        self.tc_set_temp = QDoubleSpinBox()
        self.tc_set_temp.setRange(-273.15, 300.0)
        self.tc_set_temp.setDecimals(3)
        self.tc_set_temp.setSuffix(" °C")
        self.configure_spin(self.tc_set_temp, 0.01)
        self.laser_step_value = 0.01
        self.laser_step_target = "cc"
        self.laser_step_buttons = self.create_step_buttons(
            (100.0, 10.0, 1.0, 0.1, 0.01, 0.001, 0.0001, 0.00001, 0.000001),
            self.laser_step_value,
            self.select_laser_step,
        )
        self.laser_target_buttons = {
            "cc": self.make_target_button(lambda: self.select_laser_target("cc")),
            "pc": self.make_target_button(lambda: self.select_laser_target("pc")),
            "tc": self.make_target_button(lambda: self.select_laser_target("tc")),
        }
        self.laser_target_group = QButtonGroup(self)
        self.laser_target_group.setExclusive(True)
        for button in self.laser_target_buttons.values():
            self.laser_target_group.addButton(button)
        self.laser_target_buttons[self.laser_step_target].setChecked(True)
        self.apply_laser_setpoints_btn = QPushButton("应用 Laser")

        self.falc_index = QSpinBox()
        self.falc_index.setRange(1, 4)
        self.falc_index.setValue(1)
        self.falc_refresh_btn = QPushButton("刷新 FALC")
        self.falc_enable_guard = QCheckBox("允许写 FALC 使能")
        self.falc_enable_btn = QPushButton("使能 Main + Unlim")
        self.falc_disable_btn = QPushButton("关闭 Main + Unlim")
        self.falc_status = StatusText("FALC 状态未知", max_height=112)

        self.autolock_guard = QCheckBox("允许一键锁频自动使能 FALC")
        self.autolock_start_btn = QPushButton("一键锁频分析")
        self.autolock_stop_btn = QPushButton("停止状态机")
        self.autolock_status = StatusText("状态机 Idle", max_height=72)
        self.open_scan_window_btn = QPushButton("Scan 配置")
        self.open_falc_window_btn = QPushButton("FALC 控制")
        self.open_autolock_window_btn = QPushButton("一键锁频")
        self.open_log_btn = QPushButton("打开操作日志窗口")

        self.connection_log = QPlainTextEdit()
        self.connection_log.setReadOnly(True)
        self.connection_log.setMinimumHeight(220)

        self.figure = Figure(figsize=(8, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.frame_status = QLabel("波形：未采集")
        self.frame_status.setObjectName("FrameStatus")
        self.frame_status.setWordWrap(True)
        self.frame_status.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.scope_connect_btn.clicked.connect(self.connect_scope)
        self.scope_capture_btn.clicked.connect(self.capture_scope_frame)
        self.open_csv_btn.clicked.connect(self.open_csv)
        self.dlc_connect_btn.clicked.connect(self.connect_dlc)
        self.dlc_refresh_btn.clicked.connect(self.refresh_dlc_snapshot)
        self.configure_scan_btn.clicked.connect(self.configure_scan)
        self.apply_scan_btn.clicked.connect(lambda: self.apply_scan_values())
        self.scan_enable_btn.clicked.connect(lambda: self.set_scan_enabled(True))
        self.scan_disable_btn.clicked.connect(lambda: self.set_scan_enabled(False))
        self.apply_lock_settings_btn.clicked.connect(self.apply_lock_settings)
        self.apply_pid1_btn.clicked.connect(lambda: self.apply_pid_gains(1))
        self.apply_pid2_btn.clicked.connect(lambda: self.apply_pid_gains(2))
        self.apply_lockin_btn.clicked.connect(lambda: self.apply_lockin_settings())
        self.apply_laser_setpoints_btn.clicked.connect(lambda: self.apply_laser_setpoints())
        self.falc_refresh_btn.clicked.connect(self.refresh_dlc_snapshot)
        self.falc_enable_btn.clicked.connect(lambda: self.set_falc_paths(True, True))
        self.falc_disable_btn.clicked.connect(lambda: self.set_falc_paths(False, False))
        self.autolock_start_btn.clicked.connect(self.start_autolock)
        self.autolock_stop_btn.clicked.connect(self.stop_autolock)
        self.open_scan_window_btn.clicked.connect(self.show_scan_window)
        self.open_falc_window_btn.clicked.connect(self.show_falc_window)
        self.open_autolock_window_btn.clicked.connect(self.show_autolock_window)
        self.open_log_btn.clicked.connect(self.show_log_window)

        for widget in (
            self.scan_offset,
            self.scan_amp,
            self.scan_freq,
            self.scan_enabled_check,
            self.scan_hold_check,
            self.scan_output,
            self.scan_shape,
        ):
            self.connect_auto_apply(widget, "scan")
        for widget in (self.pid1_gain_all, self.pid1_gain_p, self.pid1_gain_i, self.pid1_gain_d):
            self.connect_auto_apply(widget, "pid1")
        for widget in (self.pid2_gain_all, self.pid2_gain_p, self.pid2_gain_i, self.pid2_gain_d):
            self.connect_auto_apply(widget, "pid2")
        for widget in (self.lockin_enabled_check, self.lockin_freq, self.lockin_amp):
            self.connect_auto_apply(widget, "lockin")
        for widget in (self.cc_set_current, self.pc_set_voltage, self.tc_set_temp):
            self.connect_auto_apply(widget, "laser")
        self.update_scan_step()
        self.update_pid_step()
        self.update_lockin_step()
        self.update_laser_step()

    def connect_auto_apply(self, widget: QWidget, kind: str) -> None:
        if isinstance(widget, QDoubleSpinBox):
            widget.valueChanged.connect(lambda *_: self.schedule_auto_apply(kind))
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(lambda *_: self.schedule_auto_apply(kind))
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(lambda *_: self.schedule_auto_apply(kind))

    def schedule_auto_apply(self, kind: str) -> None:
        if self.shutting_down or self.rendering_snapshot or self.dlc.dlc is None:
            return
        timer = self.auto_apply_timers.get(kind)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda k=kind: self.run_auto_apply(k))
            self.auto_apply_timers[kind] = timer
        timer.start(350)

    def run_auto_apply(self, kind: str) -> None:
        if self.dlc.dlc is None:
            return
        if self.worker_thread is not None:
            self.schedule_auto_apply(kind)
            return
        if kind == "scan":
            self.apply_scan_values(auto=True)
        elif kind == "pid1":
            self.apply_pid_gains(1, auto=True)
        elif kind == "pid2":
            self.apply_pid_gains(2, auto=True)
        elif kind == "lockin":
            self.apply_lockin_settings(auto=True)
        elif kind == "laser":
            self.apply_laser_setpoints(auto=True)

    def select_scan_step(self, step: float) -> None:
        self.scan_step_value = step
        self.update_scan_step()

    def select_scan_target(self, target: str) -> None:
        self.scan_step_target = target
        self.update_scan_step()

    def update_scan_step(self) -> None:
        step = float(self.scan_step_value)
        self.update_step_target_state({
            "amplitude": self.scan_amp,
            "offset": self.scan_offset,
            "frequency": self.scan_freq,
        }, self.scan_step_target, step)

    def select_pid_step(self, step: float) -> None:
        self.pid_step_value = step
        self.update_pid_step()

    def select_pid_target(self, target: str) -> None:
        self.pid_step_target = target
        self.update_pid_step()

    def update_pid_step(self) -> None:
        step = float(self.pid_step_value)
        self.update_step_target_state({
            "pid1_gain_all": self.pid1_gain_all,
            "pid1_gain_p": self.pid1_gain_p,
            "pid1_gain_i": self.pid1_gain_i,
            "pid1_gain_d": self.pid1_gain_d,
            "pid2_gain_all": self.pid2_gain_all,
            "pid2_gain_p": self.pid2_gain_p,
            "pid2_gain_i": self.pid2_gain_i,
            "pid2_gain_d": self.pid2_gain_d,
        }, self.pid_step_target, step)

    def update_lockin_step(self) -> None:
        step = float(self.lockin_step_value)
        self.update_step_target_state({
            "frequency": self.lockin_freq,
            "amplitude": self.lockin_amp,
        }, self.lockin_step_target, step)

    def select_lockin_step(self, step: float) -> None:
        self.lockin_step_value = step
        self.update_lockin_step()

    def select_lockin_target(self, target: str) -> None:
        self.lockin_step_target = target
        self.update_lockin_step()

    def select_laser_step(self, step: float) -> None:
        self.laser_step_value = step
        self.update_laser_step()

    def select_laser_target(self, target: str) -> None:
        self.laser_step_target = target
        self.update_laser_step()

    def update_laser_step(self) -> None:
        step = float(self.laser_step_value)
        self.update_step_target_state({
            "cc": self.cc_set_current,
            "pc": self.pc_set_voltage,
            "tc": self.tc_set_temp,
        }, self.laser_step_target, step)

    def build_layout(self) -> QWidget:
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.addWidget(self.top_status_panel())

        self.scan_window = ToolWindow("Scan 配置", self.scan_panel())
        self.falc_window = ToolWindow("FALC 控制", self.falc_panel())
        self.autolock_window = ToolWindow("一键锁频", self.autolock_panel())

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left = QVBoxLayout()
        left_widget.setLayout(left)
        left.addWidget(self.connection_panel())
        left.addWidget(self.control_panel())
        left.addWidget(self.log_panel())
        left.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(390)
        scroll.setWidget(left_widget)
        splitter.addWidget(scroll)

        right_widget = QWidget()
        right = QVBoxLayout()
        right_widget.setLayout(right)
        right.addWidget(self.canvas, 1)
        right.addWidget(self.frame_status)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([460, 920])

        outer.addWidget(splitter, 1)
        return root

    def top_status_panel(self) -> QWidget:
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.scope_badge)
        layout.addWidget(self.dlc_badge)
        layout.addStretch(1)
        return panel

    def connection_panel(self) -> QGroupBox:
        group = QGroupBox("连接")
        form = QFormLayout(group)
        form.addRow("示波器方式", self.scope_mode)
        form.addRow("MSO64B IP", self.scope_ip)
        form.addRow("MSO64B Port", self.scope_port)
        form.addRow("USB/VISA Resource", self.scope_usb)
        form.addRow("Transmission CH", self.scope_trans_ch)
        form.addRow("Error CH", self.scope_err_ch)
        form.addRow("采样点数", self.scope_points)
        row = QHBoxLayout()
        row.addWidget(self.scope_connect_btn)
        row.addWidget(self.scope_capture_btn)
        row.addWidget(self.open_csv_btn)
        form.addRow(row)
        form.addRow("DLC 方式", self.dlc_mode)
        form.addRow("DLC IP/Host", self.dlc_host)
        form.addRow("子网掩码", self.dlc_subnet_mask)
        form.addRow("Command Port", self.dlc_cmd_port)
        form.addRow("Monitor Port", self.dlc_mon_port)
        form.addRow("Timeout", self.dlc_timeout)
        form.addRow("DLC COM", self.dlc_serial)
        form.addRow("Baudrate", self.dlc_baudrate)
        row2 = QHBoxLayout()
        row2.addWidget(self.dlc_connect_btn)
        row2.addWidget(self.dlc_refresh_btn)
        form.addRow(row2)
        return group

    def control_panel(self) -> QGroupBox:
        group = QGroupBox("控制窗口")
        layout = QGridLayout(group)
        layout.addWidget(self.open_scan_window_btn, 0, 0)
        layout.addWidget(self.open_falc_window_btn, 0, 1)
        layout.addWidget(self.open_autolock_window_btn, 1, 0)
        layout.addWidget(self.open_log_btn, 1, 1)
        return group

    def step_button_row(self, buttons: list[QPushButton], columns: int = 5) -> QWidget:
        row = QWidget()
        layout = QGridLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        for index, button in enumerate(buttons):
            button.setMinimumWidth(58)
            button.setMaximumWidth(92)
            layout.addWidget(button, index // columns, index % columns)
        for column in range(columns):
            layout.setColumnStretch(column, 1)
        return row

    def scan_step_row(self) -> QWidget:
        return self.step_button_row(self.scan_step_buttons, columns=5)

    def compact_step_row(self, buttons: list[QPushButton]) -> QWidget:
        return self.step_button_row(buttons, columns=5)

    def pid_numeric_row(self, spin: QDoubleSpinBox, target_button: QPushButton) -> QWidget:
        row = self.scan_numeric_row(spin, target_button)
        target_button.setMinimumWidth(96)
        return row

    def scan_numeric_row(self, spin: QDoubleSpinBox, target_button: QPushButton) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(spin, 1)
        target_button.setMinimumWidth(112)
        layout.addWidget(target_button)
        return row

    def scan_panel(self) -> QWidget:
        panel = QWidget()
        outer = QVBoxLayout(panel)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setAlignment(Qt.AlignTop)

        sc_group = QGroupBox("SC - 扫描控制")
        sc_form = QFormLayout(sc_group)
        scan_enable_row = QHBoxLayout()
        scan_enable_row.addWidget(self.scan_enabled_check)
        scan_enable_row.addWidget(self.scan_hold_check)
        scan_enable_row.addStretch(1)
        sc_form.addRow(scan_enable_row)
        sc_form.addRow("调节步进", self.scan_step_row())
        sc_form.addRow("扫描幅度", self.scan_numeric_row(self.scan_amp, self.scan_amp_target_btn))
        sc_form.addRow("扫描偏置", self.scan_numeric_row(self.scan_offset, self.scan_offset_target_btn))
        sc_form.addRow("扫描输出", self.scan_output)
        sc_form.addRow("扫描频率", self.scan_numeric_row(self.scan_freq, self.scan_freq_target_btn))
        sc_form.addRow("扫描波形", self.scan_shape)
        sc_buttons = QHBoxLayout()
        sc_buttons.addWidget(self.configure_scan_btn)
        sc_form.addRow(sc_buttons)
        sc_quick = QHBoxLayout()
        sc_quick.addWidget(self.scan_enable_btn)
        sc_quick.addWidget(self.scan_disable_btn)
        sc_form.addRow(sc_quick)
        sc_form.addRow("读数", self.scan_status)

        lock_group = QGroupBox("Lock Settings")
        lock_form = QFormLayout(lock_group)
        lock_enable_row = QHBoxLayout()
        lock_enable_row.addWidget(self.lock_enabled_check)
        lock_enable_row.addWidget(self.lock_hold_check)
        lock_enable_row.addStretch(1)
        lock_form.addRow(lock_enable_row)
        lock_form.addRow("Lock Input Signal", self.lock_input_signal)
        lock_form.addRow("Lock Type", self.lock_type)
        lock_form.addRow("Error Signal", self.error_signal)
        lock_form.addRow("Error Signal Inverted", self.error_inverted_check)
        lock_form.addRow("PID Selection", self.pid_selection)
        lock_form.addRow("Lock Without Lockpoint", self.lock_without_lockpoint_check)
        lock_form.addRow(self.apply_lock_settings_btn)

        laser_group = QGroupBox("Laser")
        laser_form = QFormLayout(laser_group)
        laser_form.addRow("调节步进", self.compact_step_row(self.laser_step_buttons))
        laser_form.addRow("CC Set Current", self.scan_numeric_row(self.cc_set_current, self.laser_target_buttons["cc"]))
        laser_form.addRow("PC Set Voltage", self.scan_numeric_row(self.pc_set_voltage, self.laser_target_buttons["pc"]))
        laser_form.addRow("TC Set Temperature", self.scan_numeric_row(self.tc_set_temp, self.laser_target_buttons["tc"]))

        pid_step_group = QGroupBox("PID 调节步进")
        pid_step_layout = QVBoxLayout(pid_step_group)
        pid_step_layout.addWidget(self.compact_step_row(self.pid_step_buttons))
        pid1_group = self.pid_panel(
            "PID 1",
            self.pid1_gain_all,
            self.pid1_gain_p,
            self.pid1_gain_i,
            self.pid1_gain_d,
            self.apply_pid1_btn,
            self.pid_target_buttons["pid1_gain_all"],
            self.pid_target_buttons["pid1_gain_p"],
            self.pid_target_buttons["pid1_gain_i"],
            self.pid_target_buttons["pid1_gain_d"],
        )
        pid2_group = self.pid_panel(
            "PID 2",
            self.pid2_gain_all,
            self.pid2_gain_p,
            self.pid2_gain_i,
            self.pid2_gain_d,
            self.apply_pid2_btn,
            self.pid_target_buttons["pid2_gain_all"],
            self.pid_target_buttons["pid2_gain_p"],
            self.pid_target_buttons["pid2_gain_i"],
            self.pid_target_buttons["pid2_gain_d"],
        )

        lockin_group = QGroupBox("Lock-In")
        lockin_form = QFormLayout(lockin_group)
        lockin_form.addRow(self.lockin_enabled_check)
        lockin_form.addRow("调节步进", self.compact_step_row(self.lockin_step_buttons))
        lockin_form.addRow("Frequency", self.scan_numeric_row(self.lockin_freq, self.lockin_target_buttons["frequency"]))
        lockin_form.addRow("Amplitude", self.scan_numeric_row(self.lockin_amp, self.lockin_target_buttons["amplitude"]))

        for group in (sc_group, lock_group, laser_group, pid1_group, pid2_group, lockin_group, pid_step_group):
            group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        columns = QWidget()
        columns_layout = QHBoxLayout(columns)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(12)
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(lock_group)
        left_layout.addWidget(laser_group)
        left_layout.addStretch(1)
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(pid_step_group)
        right_layout.addWidget(pid1_group)
        right_layout.addWidget(pid2_group)
        right_layout.addWidget(lockin_group)
        right_layout.addStretch(1)
        columns_layout.addWidget(left_col, 1)
        columns_layout.addWidget(right_col, 1)

        body_layout.addWidget(sc_group)
        body_layout.addWidget(columns)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        return panel

    def pid_panel(
        self,
        title: str,
        gain_all: QDoubleSpinBox,
        gain_p: QDoubleSpinBox,
        gain_i: QDoubleSpinBox,
        gain_d: QDoubleSpinBox,
        apply_btn: QPushButton,
        target_all: QPushButton,
        target_p: QPushButton,
        target_i: QPushButton,
        target_d: QPushButton,
    ) -> QGroupBox:
        group = QGroupBox(title)
        form = QFormLayout(group)
        form.addRow("Gain", self.pid_numeric_row(gain_all, target_all))
        form.addRow("P", self.pid_numeric_row(gain_p, target_p))
        form.addRow("I", self.pid_numeric_row(gain_i, target_i))
        form.addRow("D", self.pid_numeric_row(gain_d, target_d))
        return group

    def falc_panel(self) -> QWidget:
        panel = QWidget()
        outer = QVBoxLayout(panel)
        group = QGroupBox("FALC 控制")
        form = QFormLayout(group)
        form.addRow("FALC 编号", self.falc_index)
        form.addRow(self.falc_refresh_btn)
        form.addRow(self.falc_enable_guard)
        row = QHBoxLayout()
        row.addWidget(self.falc_enable_btn)
        row.addWidget(self.falc_disable_btn)
        form.addRow(row)
        form.addRow("读数", self.falc_status)
        outer.addWidget(group)
        outer.addStretch(1)
        return panel

    def autolock_panel(self) -> QWidget:
        panel = QWidget()
        outer = QVBoxLayout(panel)
        group = QGroupBox("一键锁频")
        layout = QVBoxLayout(group)
        layout.addWidget(self.autolock_guard)
        row = QHBoxLayout()
        row.addWidget(self.autolock_start_btn)
        row.addWidget(self.autolock_stop_btn)
        layout.addLayout(row)
        layout.addWidget(self.autolock_status)
        outer.addWidget(group)
        outer.addStretch(1)
        return panel

    def log_panel(self) -> QGroupBox:
        group = QGroupBox("连接日志")
        layout = QVBoxLayout(group)
        layout.addWidget(self.connection_log)
        return group

    def apply_style(self) -> None:
        style = """
            QWidget { font-size: 13px; color: #1f2933; }
            QMainWindow, QWidget { background: #f5f7fa; }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #cfd7e2;
                border-radius: 6px;
                margin-top: 10px;
                padding: 12px 8px 8px 8px;
                font-weight: 600;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QLabel { background: transparent; }
            #ConnectionBadge {
                background: #ffffff;
                border: 1px solid #cfd7e2;
                border-radius: 6px;
            }
            #FrameStatus {
                background: #ffffff;
                border: 1px solid #d7dee8;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
                background: #ffffff;
                border: 1px solid #c4ccd8;
                border-radius: 4px;
                padding: 4px;
            }
            QDoubleSpinBox[stepActive="false"] {
                background: #eef2f7;
                color: #667085;
            }
            QDoubleSpinBox[stepActive="true"] {
                border: 1px solid #4f8f68;
            }
            QPushButton {
                background: #245c9f;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 7px 10px;
                min-height: 24px;
            }
            QPushButton:hover { background: #1f4f87; }
            QPushButton:disabled { background: #aab4c0; }
            QPushButton#StepButton, QPushButton#TargetButton {
                background: #eef2f7;
                color: #1f2933;
                border: 1px solid #b7c2d0;
                border-radius: 6px;
                padding: 7px 12px;
                min-height: 24px;
            }
            QPushButton#StepButton:hover, QPushButton#TargetButton:hover {
                background: #dde6f1;
            }
            QPushButton#StepButton:checked {
                background: #3f6f53;
                color: #ffffff;
                border: 1px solid #5b946f;
                font-weight: 700;
            }
            QPushButton#TargetButton:checked {
                background: #79613e;
                color: #ffffff;
                border: 1px solid #a48553;
                font-weight: 700;
            }
            """
        self.setStyleSheet(style)
        self.log_window.setStyleSheet(style)
        self.scan_window.setStyleSheet(style)
        self.falc_window.setStyleSheet(style)
        self.autolock_window.setStyleSheet(style)

    def run_task(self, fn: Callable[[], Any], on_finished: Callable[[Any], None], title: str) -> None:
        if self.shutting_down:
            return
        if self.worker_thread is not None:
            self.append_connection_log("已有后台任务在运行，先等它结束。")
            return
        self.append_connection_log(f"开始：{title}")
        self.worker_thread = QThread(self)
        self.worker = TaskWorker(fn)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(on_finished)
        self.worker.failed.connect(lambda msg: self.task_failed(title, msg))
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.failed.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.clear_worker)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    @Slot()
    def clear_worker(self) -> None:
        self.worker = None
        self.worker_thread = None

    def task_failed(self, title: str, message: str) -> None:
        self.append_connection_log(f"{title} 失败：{message}")
        if "示波器" in title:
            self.scope_badge.set_state("示波器", "连接失败", False)
        if "DLC" in title:
            self.dlc_badge.set_state("DLC pro", "连接失败", False)

    def scope_resource_text(self) -> str:
        if self.scope_mode.currentText().startswith("LAN"):
            return self.scope.resource_from_lan(self.scope_ip.text(), self.scope_port.value())
        return self.scope_usb.text().strip()

    def connect_scope(self) -> None:
        resource = self.scope_resource_text()
        self.run_task(lambda: self.scope.test_connection(resource), self.scope_connected, "连接示波器")

    def scope_connected(self, idn: str) -> None:
        self.scope_resource = self.scope_resource_text()
        self.scope_badge.set_state("示波器", "已连接", True)
        self.scope_badge.setToolTip(f"{self.scope_resource}\n{idn}")
        self.append_connection_log(f"示波器连接成功：{self.scope_resource}")

    def connect_dlc(self) -> None:
        if self.dlc_mode.currentText() == "LAN":
            host = self.dlc_host.text().strip()
            self.run_task(
                lambda: self.dlc.connect_network(
                    host,
                    command_line_port=self.dlc_cmd_port.value(),
                    monitoring_line_port=self.dlc_mon_port.value(),
                    timeout_s=self.dlc_timeout.value(),
                ),
                self.dlc_connected,
                "连接 DLC pro",
            )
        else:
            port = self.dlc_serial.text().strip()
            self.run_task(
                lambda: self.dlc.connect_serial(
                    port,
                    baudrate=self.dlc_baudrate.value(),
                    timeout_s=self.dlc_timeout.value(),
                ),
                self.dlc_connected,
                "连接 DLC pro",
            )

    def dlc_connected(self, ident: str) -> None:
        self.dlc_badge.set_state("DLC pro", "已连接", True)
        self.dlc_badge.setToolTip(ident)
        self.append_connection_log(f"DLC pro 连接成功：{ident}")
        if self.dlc_mode.currentText() == "LAN":
            self.append_connection_log(
                f"DLC LAN 配置：host={self.dlc_host.text().strip()}, "
                f"subnet={self.dlc_subnet_mask.text().strip()}, "
                f"cmd={self.dlc_cmd_port.value()}, monitor={self.dlc_mon_port.value()}, "
                f"timeout={self.dlc_timeout.value():.1f}s"
            )
        self.append_connection_log(f"SDK 路径：{self.dlc.sdk_module_path or '-'}")
        self.poll_timer.start()
        QTimer.singleShot(100, self.refresh_dlc_snapshot)

    def refresh_dlc_snapshot(self) -> None:
        if self.shutting_down or self.dlc.dlc is None:
            return
        falc_index = self.falc_index.value()
        self.run_task(lambda: self.dlc.read_snapshot(falc_index), self.render_snapshot, "刷新 DLC/FALC 状态")

    def set_spin_readback(self, spin: QDoubleSpinBox, value: float | None) -> None:
        if value is None or spin.hasFocus():
            return
        old_state = spin.blockSignals(True)
        try:
            spin.setValue(float(value))
        finally:
            spin.blockSignals(old_state)

    def set_combo_readback(self, combo: QComboBox, value: int | None) -> None:
        if value is None or combo.hasFocus():
            return
        index = combo.findData(value)
        if index >= 0:
            old_state = combo.blockSignals(True)
            try:
                combo.setCurrentIndex(index)
            finally:
                combo.blockSignals(old_state)

    def set_check_readback(self, checkbox: QCheckBox, value: bool | None) -> None:
        if value is None or checkbox.hasFocus():
            return
        old_state = checkbox.blockSignals(True)
        try:
            checkbox.setChecked(bool(value))
        finally:
            checkbox.blockSignals(old_state)

    def render_snapshot(self, snapshot: DlcSnapshot) -> None:
        self.snapshot = snapshot
        scan = snapshot.scan
        lock = snapshot.lock_settings
        lockin = snapshot.lockin
        laser_set = snapshot.laser_set
        falc = snapshot.falc
        self.dlc_badge.set_state(
            "DLC pro",
            f"{snapshot.system_label or snapshot.serial_number or '已连接'}",
            True,
        )
        self.dlc_badge.setToolTip(
            f"Serial: {snapshot.serial_number or '-'}\n"
            f"Firmware: {snapshot.firmware or '-'}\n"
            f"Emission: {snapshot.emission}\n"
            f"Interlock open: {snapshot.interlock_open}"
        )
        self.scan_status.setText(
            f"enabled={scan.enabled}, freq={scan.frequency_hz}, output={scan.output_channel}, "
            f"shape={scan.signal_type}, offset={scan.offset_v}, amp={scan.amplitude_vpp}, unit={scan.unit}"
        )
        self.set_check_readback(self.scan_enabled_check, scan.enabled)
        self.set_check_readback(self.scan_hold_check, scan.hold)
        self.set_combo_readback(self.scan_output, scan.output_channel)
        self.set_combo_readback(self.scan_shape, scan.signal_type)
        self.set_spin_readback(self.scan_offset, scan.offset_v)
        if scan.amplitude_vpp is not None and scan.amplitude_vpp > 0:
            self.set_spin_readback(self.scan_amp, scan.amplitude_vpp)
        if scan.frequency_hz is not None and scan.frequency_hz > 0:
            self.set_spin_readback(self.scan_freq, scan.frequency_hz)
        self.set_check_readback(self.lock_enabled_check, lock.enabled)
        self.set_check_readback(self.lock_hold_check, lock.hold)
        self.set_check_readback(self.error_inverted_check, lock.error_channel_inverted)
        self.set_check_readback(self.lock_without_lockpoint_check, lock.lock_without_lockpoint)
        self.set_combo_readback(self.lock_input_signal, lock.spectrum_input_channel)
        self.set_combo_readback(self.lock_type, lock.lock_type)
        self.set_combo_readback(self.error_signal, lock.error_channel)
        self.set_combo_readback(self.pid_selection, lock.pid_selection)
        self.set_spin_readback(self.pid1_gain_all, snapshot.pid1.gain_all)
        self.set_spin_readback(self.pid1_gain_p, snapshot.pid1.gain_p)
        self.set_spin_readback(self.pid1_gain_i, snapshot.pid1.gain_i)
        self.set_spin_readback(self.pid1_gain_d, snapshot.pid1.gain_d)
        self.set_spin_readback(self.pid2_gain_all, snapshot.pid2.gain_all)
        self.set_spin_readback(self.pid2_gain_p, snapshot.pid2.gain_p)
        self.set_spin_readback(self.pid2_gain_i, snapshot.pid2.gain_i)
        self.set_spin_readback(self.pid2_gain_d, snapshot.pid2.gain_d)
        self.set_check_readback(self.lockin_enabled_check, lockin.modulation_enabled)
        self.set_spin_readback(self.lockin_freq, lockin.frequency_hz)
        self.set_spin_readback(self.lockin_amp, lockin.amplitude)
        self.set_spin_readback(self.cc_set_current, laser_set.cc_current_ma)
        self.set_spin_readback(self.pc_set_voltage, laser_set.pc_voltage_v)
        self.set_spin_readback(self.tc_set_temp, laser_set.tc_temperature_c)
        self.falc_status.setText(
            f"FALC{falc.index} SN={falc.serial_number or '-'} | path={falc.path_selection} | "
            f"main={falc.main_enabled}/{falc.main_lock_state} gain={falc.main_gain_db} | "
            f"unlim={falc.unlim_enabled}/{falc.unlim_lock_state} range={falc.unlim_output_range_v}"
        )
        if snapshot.warnings:
            self.append_connection_log(f"部分参数不可读：{len(snapshot.warnings)} 项")

    def configure_scan(self) -> None:
        freq = self.scan_freq.value()
        self.run_task(
            lambda: self.dlc.configure_scan_for_piezo_triangle(freq),
            lambda _: QTimer.singleShot(100, self.refresh_dlc_snapshot),
            "配置 Scan",
        )

    def apply_scan_values(self, auto: bool = False) -> None:
        self.run_task(
            lambda: self.dlc.set_scan_settings(
                enabled=self.scan_enabled_check.isChecked(),
                hold=self.scan_hold_check.isChecked(),
                output_channel=int(self.scan_output.currentData()),
                signal_type=int(self.scan_shape.currentData()),
                frequency_hz=self.scan_freq.value(),
                offset_v=self.scan_offset.value(),
                amplitude_vpp=self.scan_amp.value(),
            ),
            lambda _: QTimer.singleShot(100, self.refresh_dlc_snapshot),
            "实时写入 SC/Master" if auto else "写入 SC/Master",
        )

    def set_scan_enabled(self, enabled: bool) -> None:
        self.run_task(
            lambda: self.dlc.set_scan_enabled(enabled),
            lambda _: QTimer.singleShot(100, self.refresh_dlc_snapshot),
            "切换 Scan",
        )

    def apply_lock_settings(self) -> None:
        self.run_task(
            lambda: self.dlc.set_lock_settings(
                enabled=self.lock_enabled_check.isChecked(),
                hold=self.lock_hold_check.isChecked(),
                spectrum_input_channel=int(self.lock_input_signal.currentData()),
                lock_type=int(self.lock_type.currentData()),
                error_channel=int(self.error_signal.currentData()),
                error_channel_inverted=self.error_inverted_check.isChecked(),
                pid_selection=int(self.pid_selection.currentData()),
                lock_without_lockpoint=self.lock_without_lockpoint_check.isChecked(),
            ),
            lambda _: QTimer.singleShot(100, self.refresh_dlc_snapshot),
            "写入 Lock Settings",
        )

    def apply_pid_gains(self, pid_index: int, auto: bool = False) -> None:
        if pid_index == 1:
            values = (self.pid1_gain_all.value(), self.pid1_gain_p.value(), self.pid1_gain_i.value(), self.pid1_gain_d.value())
        else:
            values = (self.pid2_gain_all.value(), self.pid2_gain_p.value(), self.pid2_gain_i.value(), self.pid2_gain_d.value())
        self.run_task(
            lambda: self.dlc.set_pid_gains(pid_index, *values),
            lambda _: QTimer.singleShot(100, self.refresh_dlc_snapshot),
            f"实时写入 PID {pid_index}" if auto else f"写入 PID {pid_index}",
        )

    def apply_lockin_settings(self, auto: bool = False) -> None:
        self.run_task(
            lambda: self.dlc.set_lockin_settings(
                enabled=self.lockin_enabled_check.isChecked(),
                frequency_hz=self.lockin_freq.value(),
                amplitude=self.lockin_amp.value(),
            ),
            lambda _: QTimer.singleShot(100, self.refresh_dlc_snapshot),
            "实时写入 Lock-In" if auto else "写入 Lock-In",
        )

    def apply_laser_setpoints(self, auto: bool = False) -> None:
        self.run_task(
            lambda: self.dlc.set_laser_setpoints(
                cc_current_ma=self.cc_set_current.value(),
                pc_voltage_v=self.pc_set_voltage.value(),
                tc_temperature_c=self.tc_set_temp.value(),
            ),
            lambda _: QTimer.singleShot(100, self.refresh_dlc_snapshot),
            "实时写入 Laser setpoints" if auto else "写入 Laser setpoints",
        )

    def set_falc_paths(self, main_enabled: bool, unlim_enabled: bool) -> None:
        if not self.falc_enable_guard.isChecked():
            QMessageBox.warning(self, "FALC", "请先勾选“允许写 FALC 使能”。")
            return
        index = self.falc_index.value()
        self.run_task(
            lambda: self.dlc.set_falc_paths_enabled(index, main_enabled, unlim_enabled),
            lambda _: QTimer.singleShot(100, self.refresh_dlc_snapshot),
            "写入 FALC 使能",
        )

    def capture_scope_frame(self) -> None:
        resource = self.scope_resource or self.scope_resource_text()
        points = self.scope_points.value() or None
        self.run_task(
            lambda: self.scope.capture_frame(resource, self.scope_trans_ch.value(), self.scope_err_ch.value(), points),
            self.frame_captured,
            "采集示波器帧",
        )

    def frame_captured(self, frame: SignalFrame) -> None:
        self.last_frame = frame
        self.plot_frame(frame)
        self.render_frame_summary(frame)
        if self.autolock.state.running:
            self.evaluate_autolock_frame(frame)

    def open_csv(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "打开 CSV", str(APP_DIR / "captures"), "CSV Files (*.csv)")
        if not filename:
            return
        frame = load_signal_frame(Path(filename))
        self.frame_captured(frame)

    def start_autolock(self) -> None:
        self.autolock.start()
        self.render_autolock_state()
        if self.dlc.dlc is None:
            self.append_process_log("DLC pro 未连接，不能配置扫描。")
            return
        self.run_task(
            lambda: self.autolock.prepare_scan(self.dlc, self.scan_freq.value()),
            lambda _: self.after_autolock_prepare(),
            "一键锁频准备扫描",
        )

    def after_autolock_prepare(self) -> None:
        self.render_autolock_state()
        QTimer.singleShot(100, self.refresh_dlc_snapshot)
        QTimer.singleShot(250, self.capture_scope_frame)

    def evaluate_autolock_frame(self, frame: SignalFrame) -> None:
        snapshot = self.snapshot or DlcSnapshot(connected=False)
        state = self.autolock.evaluate_frame(
            snapshot,
            frame,
            allow_falc_enable=self.autolock_guard.isChecked(),
            falc_index=self.falc_index.value(),
            dlc=self.dlc,
        )
        self.render_autolock_state()
        if state.phase == AutoLockPhase.READY_FOR_FALC:
            QMessageBox.information(self, "一键锁频", "已连续确认可锁，可以准备使能 FALC。")
        elif state.phase == AutoLockPhase.ANALYZE_FRAME and state.running:
            self.append_process_log("需要继续采集/调整；当前版本不会自动长时间循环写硬件。")

    def stop_autolock(self) -> None:
        self.autolock.stop()
        self.render_autolock_state()

    def render_autolock_state(self) -> None:
        state = self.autolock.state
        self.autolock_status.setText(f"状态机：{state.phase.value} | ready frames={state.stable_ready_frames}")
        while state.log:
            self.append_process_log(state.log.pop(0))

    def plot_empty(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_title("等待示波器/CSV：上路 Transmission，下路 Error")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(True, alpha=0.25)
        self.canvas.draw_idle()

    def plot_frame(self, frame: SignalFrame) -> None:
        self.figure.clear()
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212, sharex=ax1)
        tx, ty = downsample_xy(frame.time_s, frame.transmission_v)
        ex, ey = downsample_xy(frame.time_s, frame.error_v)
        ax1.plot(tx, ty, color="#1f77b4", linewidth=0.8)
        ax1.set_title("Transmission 透射峰信号")
        ax1.set_ylabel("Transmission (V)")
        ax1.grid(True, alpha=0.25)
        ax2.plot(ex, ey, color="#d62728", linewidth=0.8)
        ax2.set_title("Error 误差信号")
        ax2.set_ylabel("Error (V)")
        ax2.set_xlabel("Time (s)")
        ax2.grid(True, alpha=0.25)
        self.canvas.draw_idle()

    def render_frame_summary(self, frame: SignalFrame) -> None:
        analysis = analyze_lock_candidate(frame, self.snapshot.scan if self.snapshot else None)
        self.frame_status.setText(
            f"CSV: {frame.csv_path} | Samples: {frame.sample_count} | "
            f"Duration: {frame.duration_s:.6g} s | Peak: {analysis.has_peak} | "
            f"Error zero: {analysis.has_error_zero} | Ready: {analysis.ready_to_lock} | {analysis.message}"
        )

    def append_connection_log(self, message: str) -> None:
        self.connection_log.appendPlainText(message)

    def append_process_log(self, message: str) -> None:
        self.log_window.append_process(message)

    def show_scan_window(self) -> None:
        self.show_tool_window(self.scan_window)

    def show_falc_window(self) -> None:
        self.show_tool_window(self.falc_window)

    def show_autolock_window(self) -> None:
        self.show_tool_window(self.autolock_window)

    def show_tool_window(self, window: QMainWindow) -> None:
        window.show()
        window.raise_()
        window.activateWindow()

    def show_log_window(self) -> None:
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.shutting_down:
            event.accept()
            return
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要关闭一键锁频软件吗？\n\n将停止轮询、关闭弹窗并断开 DLC pro 连接。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            event.ignore()
            return
        self.shutdown_application()
        event.accept()
        QApplication.instance().quit()

    def shutdown_application(self) -> None:
        self.shutting_down = True
        self.poll_timer.stop()
        for timer in self.auto_apply_timers.values():
            timer.stop()
        self.autolock.stop()
        for window in (self.scan_window, self.falc_window, self.autolock_window, self.log_window):
            if hasattr(window, "shutdown_close"):
                window.shutdown_close()
            else:
                window.close()
        try:
            self.dlc.close()
        except Exception as exc:
            self.append_connection_log(f"退出时断开 DLC pro 失败：{exc}")
        thread = self.worker_thread
        if thread is not None and thread.isRunning():
            thread.requestInterruption()
            thread.quit()
            if not thread.wait(1500):
                thread.terminate()
                thread.wait(1500)


def main() -> int:
    app = QApplication(sys.argv)
    window = OneClickLockWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
