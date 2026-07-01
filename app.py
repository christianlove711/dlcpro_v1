from __future__ import annotations

import sys
from concurrent.futures import Future, ThreadPoolExecutor

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dlcpro_service import ConnectionSettings, DeviceSnapshot, DlcProService
from ui_text import (
    ARC_SIGNAL_OPTIONS,
    LOCK_ERROR_SIGNAL_OPTIONS,
    LOCK_FALC_SELECTION_OPTIONS,
    LOCK_INPUT_SIGNAL_OPTIONS,
    LOCK_PID_SELECTION_OPTIONS,
    LOCK_TYPE_OPTIONS,
    PID_OUTPUT_CHANNEL_OPTIONS,
    SCAN_OUTPUT_OPTIONS,
    SCAN_SHAPE_OPTIONS,
    TEXT,
)
from controllers import AutoLockController, AutoLock2Controller, LaserController, ScanLockController
from widgets.common_controls import SafeComboBox, SafeSpinBox
from ui_scaling import SCALE_OPTIONS, UiScaleManager, fit_window_to_screen
from windows import (
    AutoLockWindow,
    AutoLock2Window,
    FalcProWindow,
    LaserWindow,
    RelockWindow,
    ScanLockWindow,
    StabilizationWindow,
    build_laser_page,
    build_scan_lock_page,
)

AUTO_APPLY_DEBOUNCE_MS = 150


class MainWindow(QMainWindow):
    PRECISION_OPTIONS = [
        ("step_100", 100.0),
        ("step_10", 10.0),
        ("step_1_int", 1.0),
        ("step_1", 0.1),
        ("step_2", 0.01),
        ("step_3", 0.001),
        ("step_4", 0.0001),
        ("step_5", 0.00001),
        ("step_6", 0.000001),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.service = DlcProService()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dlcpro")
        self.language = "zh"
        self.scale_manager: UiScaleManager | None = None
        self.busy = False
        self.snapshot: DeviceSnapshot | None = None
        self.pending_future: Future | None = None
        self.pending_success_handler = None
        self.pending_task_kind = "action"
        self.current_set_dirty = False
        self.current_set_programmatic_update = False
        self.cc_programmatic_update = False
        self.feedforward_programmatic_update = False
        self.arc_programmatic_update = False
        self.tc_programmatic_update = False
        self.pc_programmatic_update = False
        self.sc_programmatic_update = False
        self.lock_programmatic_update = False
        self.last_device_current_set: float | None = None
        self.cc_precision_step = 0.1
        self.tc_precision_step = 0.001
        self.pc_precision_step = 0.000001
        self.sc_precision_step = 0.01
        self.pid_precision_step = 0.01
        self.module_precision_defaults: dict[str, QDoubleSpinBox] = {}
        self.module_precision_selected: dict[str, QDoubleSpinBox] = {}
        self.module_precision_target_buttons: dict[str, list[QPushButton]] = {
            "cc": [],
            "tc": [],
            "pc": [],
            "sc": [],
            "pid": [],
        }
        self.pending_followup_task: tuple[object, object, str] | None = None
        self.connection_loss_notified = False
        self.auto_lock_controller = AutoLockController(self)
        self.auto_lock2_controller = AutoLock2Controller(self)
        self.laser_controller = LaserController(self)
        self.scan_lock_controller = ScanLockController(self)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(500)
        self.refresh_timer.timeout.connect(self.refresh_snapshot)

        self.future_poll_timer = QTimer(self)
        self.future_poll_timer.setInterval(50)
        self.future_poll_timer.timeout.connect(self._poll_future)

        self.current_apply_timer = QTimer(self)
        self.current_apply_timer.setSingleShot(True)
        self.current_apply_timer.setInterval(AUTO_APPLY_DEBOUNCE_MS)
        self.current_apply_timer.timeout.connect(self._apply_current_if_needed)

        self._build_ui()
        self._configure_combo_boxes()
        self._apply_module_precisions()
        self._update_all_precision_buttons()
        self._apply_base_style()
        self._configure_ui_scaling()
        self._apply_texts()
        self._populate_environment_hints()
        self._set_connection_mode("network")
        self._set_busy(False)

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        header_layout = QHBoxLayout()
        self.language_label = QLabel()
        self.language_combo = SafeComboBox()
        self.language_combo.addItem("中文", "zh")
        self.language_combo.addItem("English", "en")
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        header_layout.addWidget(self.language_label)
        header_layout.addWidget(self.language_combo)
        self.ui_scale_label = QLabel()
        self.ui_scale_combo = SafeComboBox()
        for label, scale in SCALE_OPTIONS:
            self.ui_scale_combo.addItem(label, scale)
        self.ui_scale_combo.currentIndexChanged.connect(self._on_ui_scale_changed)
        header_layout.addWidget(self.ui_scale_label)
        header_layout.addWidget(self.ui_scale_combo)
        header_layout.addStretch(1)
        self.status_label = QLabel()
        self.status_label.setObjectName("StatusBadge")
        header_layout.addWidget(self.status_label)
        root.addLayout(header_layout)

        self.connection_group = self._build_connection_group()
        self.connection_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        root.addWidget(self.connection_group)

        self.workspace_group = QGroupBox()
        workspace_layout = QVBoxLayout(self.workspace_group)
        workspace_layout.setContentsMargins(12, 12, 12, 12)
        workspace_layout.setSpacing(12)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setSpacing(10)
        self.overview_button = self._create_nav_button(lambda: self.page_stack.setCurrentIndex(0))
        self.laser_button = self._create_nav_button(self._open_laser_window)
        self.falc_button = self._create_nav_button(self._open_falc_window)
        self.scan_lock_button = self._create_nav_button(self._open_scan_lock_window)
        self.auto_lock_button = self._create_nav_button(self._open_auto_lock_window)
        self.auto_lock2_button = self._create_nav_button(self._open_auto_lock2_window)
        self.relock_button = self._create_nav_button(self._open_relock_window)
        self.stabilization_button = self._create_nav_button(self._open_stabilization_window)
        for button in (
            self.overview_button,
            self.laser_button,
            self.falc_button,
            self.scan_lock_button,
            self.auto_lock_button,
            self.auto_lock2_button,
            self.relock_button,
            self.stabilization_button,
        ):
            self.nav_layout.addWidget(button)
        workspace_layout.addLayout(self.nav_layout)

        self.page_stack = QStackedWidget()
        self.page_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.overview_page = self._build_overview_page()
        self.laser_page = self._build_laser_page()

        self.page_stack.addWidget(self.overview_page)
        workspace_layout.addWidget(self.page_stack, 1)
        root.addWidget(self.workspace_group, 1)
        root.setStretch(0, 0)
        root.setStretch(1, 0)
        root.setStretch(2, 1)

        self.laser_window = LaserWindow(self.laser_page)
        self.falc_window = FalcProWindow(self)
        self.scan_lock_page = self._build_scan_lock_page()
        self.scan_lock_window = ScanLockWindow(self.scan_lock_page)
        self.auto_lock_window = AutoLockWindow(self, self.auto_lock_controller)
        self.auto_lock_controller.bind_window(self.auto_lock_window)
        self.auto_lock2_window = AutoLock2Window(self, self.auto_lock2_controller)
        self.auto_lock2_controller.bind_window(self.auto_lock2_window)
        self.relock_window = RelockWindow(self)
        self.stabilization_window = StabilizationWindow(self)

    def _build_connection_group(self) -> QGroupBox:
        box = QGroupBox()
        layout = QGridLayout(box)

        self.mode_label = QLabel()
        self.mode_combo = SafeComboBox()
        self.mode_combo.addItem("", "network")
        self.mode_combo.addItem("", "serial")
        self.mode_combo.currentIndexChanged.connect(
            lambda: self._set_connection_mode(self.mode_combo.currentData())
        )

        self.host_label = QLabel()
        self.host_edit = QLineEdit("169.254.5.11")
        self.serial_port_label = QLabel()
        self.serial_port_combo = SafeComboBox()
        self.baudrate_label = QLabel()
        self.baudrate_spin = SafeSpinBox()
        self.baudrate_spin.setRange(1200, 10000000)
        self.baudrate_spin.setValue(115200)
        self.timeout_label = QLabel()
        self.timeout_spin = SafeSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(5)

        self.connect_button = QPushButton()
        self.disconnect_button = QPushButton()
        self.refresh_button = QPushButton()
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.refresh_button.clicked.connect(self.refresh_snapshot)

        self.serial_ports_info = QTextEdit()
        self.serial_ports_info.setReadOnly(True)
        self.serial_ports_info.setMaximumHeight(68)
        self.network_info = QTextEdit()
        self.network_info.setReadOnly(True)
        self.network_info.setMaximumHeight(68)

        layout.addWidget(self.mode_label, 0, 0)
        layout.addWidget(self.mode_combo, 0, 1)
        layout.addWidget(self.host_label, 1, 0)
        layout.addWidget(self.host_edit, 1, 1, 1, 3)
        layout.addWidget(self.serial_port_label, 2, 0)
        layout.addWidget(self.serial_port_combo, 2, 1)
        layout.addWidget(self.baudrate_label, 2, 2)
        layout.addWidget(self.baudrate_spin, 2, 3)
        layout.addWidget(self.timeout_label, 3, 0)
        layout.addWidget(self.timeout_spin, 3, 1)
        layout.addWidget(self.connect_button, 3, 2)
        layout.addWidget(self.disconnect_button, 3, 3)
        layout.addWidget(self.refresh_button, 3, 4)
        layout.addWidget(self.network_info, 4, 0, 1, 5)
        layout.addWidget(self.serial_ports_info, 5, 0, 1, 5)
        return box

    def _build_overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.overview_title = QLabel()
        self.overview_title.setObjectName("PageTitle")
        layout.addWidget(self.overview_title)

        self.parameter_group = QGroupBox()
        group_layout = QVBoxLayout(self.parameter_group)
        self.parameter_table = QTableWidget(0, 2)
        self.parameter_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.parameter_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.parameter_table.horizontalHeader().setStretchLastSection(True)
        self.parameter_table.verticalHeader().setVisible(False)
        self.parameter_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.parameter_table.setSelectionMode(QTableWidget.NoSelection)
        self.parameter_table.setMinimumHeight(0)
        group_layout.addWidget(self.parameter_table)
        layout.addWidget(self.parameter_group, 1)
        return page

    def _build_laser_page(self) -> QWidget:
        return build_laser_page(self)

    def _build_scan_lock_page(self) -> QWidget:
        return build_scan_lock_page(self)

    def _create_target_row(self, module: str, spinbox: QDoubleSpinBox) -> QWidget:
        # 面板层只负责创建控件，目标绑定规则仍由主窗口统一管理。
        from windows.laser_window import _create_target_row

        return _create_target_row(self, module, spinbox)

    def _create_nav_button(self, slot) -> QPushButton:
        button = QPushButton()
        button.setMinimumHeight(42)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(slot)
        return button

    def _register_module_precision_targets(self, module: str, default_target: QDoubleSpinBox, *spinboxes: QDoubleSpinBox) -> None:
        self.module_precision_defaults[module] = default_target
        self.module_precision_selected[module] = default_target
        for spinbox in spinboxes:
            spinbox.setProperty("precision_module", module)
        self._sync_precision_target_buttons(module)

    def _select_precision_target(self, module: str, spinbox: QDoubleSpinBox) -> None:
        self.module_precision_selected[module] = spinbox
        self._sync_precision_target_buttons(module)

    def _sync_precision_target_buttons(self, module: str) -> None:
        current = self.module_precision_selected.get(module, self.module_precision_defaults.get(module))
        for button in self.module_precision_target_buttons.get(module, []):
            button.blockSignals(True)
            button.setChecked(button._precision_target is current)
            button.blockSignals(False)

    def _open_laser_window(self) -> None:
        if self.laser_window.isHidden():
            self.laser_window.move(self.x() + 40, self.y() + 40)
        self.laser_window.showNormal()
        self.laser_window.show()
        fit_window_to_screen(self.laser_window)
        self.laser_window.raise_()
        self.laser_window.activateWindow()

    def _open_falc_window(self) -> None:
        if self.falc_window.isHidden():
            self.falc_window.move(self.x() + 60, self.y() + 60)
        self.falc_window.showNormal()
        self.falc_window.show()
        fit_window_to_screen(self.falc_window)
        self.falc_window.raise_()
        self.falc_window.activateWindow()

    def _open_scan_lock_window(self) -> None:
        if self.scan_lock_window.isHidden():
            self.scan_lock_window.move(self.x() + 60, self.y() + 60)
        self.scan_lock_window.showNormal()
        self.scan_lock_window.show()
        fit_window_to_screen(self.scan_lock_window)
        self.scan_lock_window.raise_()
        self.scan_lock_window.activateWindow()

    def _open_auto_lock_window(self) -> None:
        if self.auto_lock_window.isHidden():
            self.auto_lock_window.move(self.x() + 80, self.y() + 80)
        self.auto_lock_window.showNormal()
        self.auto_lock_window.show()
        fit_window_to_screen(self.auto_lock_window)
        self.auto_lock_window.raise_()
        self.auto_lock_window.activateWindow()

    def _open_auto_lock2_window(self) -> None:
        if self.auto_lock2_window.isHidden():
            self.auto_lock2_window.move(self.x() + 90, self.y() + 90)
        self.auto_lock2_window.showNormal()
        self.auto_lock2_window.show()
        fit_window_to_screen(self.auto_lock2_window)
        self.auto_lock2_window.raise_()
        self.auto_lock2_window.activateWindow()

    def _open_relock_window(self) -> None:
        if self.relock_window.isHidden():
            self.relock_window.move(self.x() + 80, self.y() + 80)
        self.relock_window.showNormal()
        self.relock_window.show()
        fit_window_to_screen(self.relock_window)
        self.relock_window.raise_()
        self.relock_window.activateWindow()

    def _open_stabilization_window(self) -> None:
        if self.stabilization_window.isHidden():
            self.stabilization_window.move(self.x() + 100, self.y() + 100)
        self.stabilization_window.showNormal()
        self.stabilization_window.show()
        fit_window_to_screen(self.stabilization_window)
        self.stabilization_window.raise_()
        self.stabilization_window.activateWindow()

    def _apply_base_style(self) -> None:
        stylesheet = """
            QWidget {
                background: #2d2d2d;
                color: #f0f0f0;
                font-size: 14px;
            }
            QLabel {
                background: transparent;
            }
            QGroupBox {
                border: 1px solid #4e4e4e;
                border-radius: 14px;
                margin-top: 10px;
                padding-top: 10px;
                background: #343434;
                font-weight: 600;
            }
            QGroupBox::title {
                left: 12px;
                padding: 0 4px 0 4px;
            }
            QLineEdit, QComboBox, QTextEdit, QTableWidget {
                background: #4a4a4a;
                border: 1px solid #666;
                border-radius: 6px;
                padding: 6px 8px;
                color: #f6f6f6;
            }
            QSpinBox, QDoubleSpinBox {
                background: #4a4a4a;
                border: 1px solid #666;
                border-radius: 6px;
                padding: 2px 22px 2px 8px;
                color: #f6f6f6;
            }
            QScrollArea, QScrollArea > QWidget > QWidget {
                background: #2d2d2d;
            }
            QTableWidget {
                gridline-color: #5a5a5a;
            }
            QPushButton {
                background: #525252;
                border: 1px solid #6a6a6a;
                border-radius: 10px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background: #5e5e5e;
            }
            QPushButton:pressed {
                background: #4a4a4a;
            }
            QPushButton#ScopeModeButton {
                min-width: 76px;
                padding: 6px 12px;
                border-radius: 8px;
            }
            QPushButton#ScopeModeButton:checked {
                background: #455b79;
                border: 1px solid #7292c0;
                color: #f4f8ff;
                font-weight: 700;
            }
            QPushButton#ScopeOpenButton {
                min-width: 164px;
            }
            QPushButton#PrecisionButton {
                min-width: 72px;
                padding: 6px 10px;
                border-radius: 8px;
            }
            QPushButton#PrecisionButton:checked {
                background: #45614c;
                border: 1px solid #6b9474;
                color: #f7fbf8;
                font-weight: 700;
            }
            QPushButton#StepTargetButton {
                min-width: 88px;
                padding: 6px 10px;
                border-radius: 8px;
                background: #4a4a4a;
                border: 1px solid #666;
                color: #d8d8d8;
            }
            QPushButton#StepTargetButton:checked {
                background: #5d5140;
                border: 1px solid #8f7a58;
                color: #fff6e5;
                font-weight: 700;
            }
            QPushButton#ParameterHelpButton {
                min-width: 28px;
                max-width: 28px;
                padding: 6px 0;
                border-radius: 14px;
                background: #4a4a4a;
                border: 1px solid #777;
                color: #f0f0f0;
                font-weight: 700;
            }
            QPushButton#ParameterHelpButton:hover {
                background: #5a5a5a;
                border: 1px solid #8a8a8a;
            }
            QLabel#ParameterRoleBadge {
                min-width: 56px;
                border-radius: 10px;
                padding: 4px 8px;
                font-weight: 700;
                color: #f4f4f4;
                background: #505050;
                border: 1px solid #686868;
            }
            QLabel#ParameterRoleBadge[role="primary"] {
                background: #335b46;
                border: 1px solid #6da27f;
                color: #f2fff7;
            }
            QLabel#ParameterRoleBadge[role="secondary"] {
                background: #4d4f64;
                border: 1px solid #7c82b0;
                color: #f4f5ff;
            }
            QLabel#ParameterRoleBadge[role="guard"] {
                background: #5d5140;
                border: 1px solid #8f7a58;
                color: #fff6e5;
            }
            QLabel#ParameterRoleBadge[role="unused"] {
                background: #3f3f3f;
                border: 1px solid #5d5d5d;
                color: #aaa;
            }
            QLabel#StatusBadge {
                background: #1f3d2a;
                border: 1px solid #35654a;
                border-radius: 12px;
                padding: 5px 12px;
                font-weight: 600;
            }
            QLabel#PageTitle {
                font-size: 19px;
                font-weight: 700;
                color: #f5f5f5;
            }
            QLabel#SectionTitle {
                font-size: 17px;
                font-weight: 700;
                color: #f2f2f2;
            }
            QFrame#LaserPanel {
                background: #3a3a3a;
                border: 1px solid #5b5b5b;
                border-radius: 18px;
            }
            QLabel#ReadValue {
                background: #505050;
                border: 1px solid #686868;
                border-radius: 6px;
                padding: 8px 10px;
                min-height: 20px;
            }
            QLabel#SubtleHint, QLabel#PlaceholderBody {
                color: #c8c8c8;
            }
            QFrame#Divider {
                color: #595959;
            }
            """
        app = QApplication.instance()
        if app is not None and self.scale_manager is not None:
            self.scale_manager.base_stylesheet = stylesheet
            self.scale_manager.apply()
        elif app is not None:
            app.setStyleSheet(stylesheet)
        else:
            self.setStyleSheet(stylesheet)

    def _configure_ui_scaling(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        if self.scale_manager is None:
            self.scale_manager = UiScaleManager(app, app.styleSheet())
        self.scale_manager.register_windows(
            (
                (self, 980, 860),
                (self.laser_window, 860, 900),
                (self.falc_window, 760, 760),
                (self.scan_lock_window, 980, 1180),
                (self.auto_lock_window, 1120, 820),
                (self.auto_lock_window.scope_window, 1120, 760),
                (self.auto_lock2_window, 1180, 620),
                (self.auto_lock2_window.config_window, 720, 520),
                (self.auto_lock2_window.waveform_window, 1120, 700),
                (self.auto_lock2_window.log_window, 920, 620),
                (self.relock_window, 1180, 480),
                (self.stabilization_window, 920, 860),
            )
        )
        self.scale_manager.apply()

    def _on_ui_scale_changed(self) -> None:
        if self.scale_manager is None:
            return
        self.scale_manager.set_scale(self.ui_scale_combo.currentData())

    def _apply_texts(self) -> None:
        t = TEXT[self.language]
        self.setWindowTitle(t["window_title"])
        self.language_label.setText(t["language"])
        self.ui_scale_label.setText(t["ui_scale"])
        self.ui_scale_combo.setItemText(0, t["ui_scale_auto"])
        self.status_label.setText(t["disconnected"] if not self.service.is_connected else t["connected"])

        self.connection_group.setTitle(t["connection"])
        self.workspace_group.setTitle(t["workspace"])
        self.parameter_group.setTitle(t["device_parameters"])
        self.overview_title.setText(t["device_overview"])

        self.mode_label.setText(t["mode"])
        self.mode_combo.setItemText(0, t["network"])
        self.mode_combo.setItemText(1, t["serial"])
        self.host_label.setText(t["host"])
        self.serial_port_label.setText(t["serial_port"])
        self.baudrate_label.setText(t["baudrate"])
        self.timeout_label.setText(t["timeout"])
        self.connect_button.setText(t["connect"])
        self.disconnect_button.setText(t["disconnect"])
        self.refresh_button.setText(t["refresh"])
        self.parameter_table.setHorizontalHeaderLabels([t["parameter"], t["value"]])

        self.overview_button.setText(t["device_overview"])
        self.laser_button.setText(t["laser"])
        self.falc_button.setText(t["falc"])
        self.scan_lock_button.setText(t["scan_lock"])
        self.auto_lock_button.setText(t["auto_lock"])
        self.auto_lock2_button.setText(t["auto_lock2"])
        self.relock_button.setText(t["relock"])
        self.stabilization_button.setText(t["stabilization"])
        self.auto_lock_controller.apply_texts()
        self.auto_lock2_controller.apply_texts()
        self.falc_window.apply_texts(self.language)
        self.relock_window.apply_texts(self.language)
        self.stabilization_window.apply_texts(self.language)
        if self.snapshot is None:
            self.relock_window.reset_state(self.language)
            self.stabilization_window.reset_state(self.language)

        self.cc_status_label = t["cc_status"]
        self.laser_controller.apply_texts()
        self.scan_lock_controller.apply_texts()

        self._populate_arc_signal_options()
        self._populate_tc_arc_signal_options()
        self._populate_pc_arc_signal_options()
        self._populate_sc_output_options()
        self._populate_sc_shape_options()
        self._populate_lock_input_signal_options()
        self._populate_lock_type_options()
        self._populate_lock_pid_selection_options()
        self._populate_pid_output_channel_options(self.pid1_output_channel_combo)
        self._populate_pid_output_channel_options(self.pid2_output_channel_combo)
        self._populate_environment_hints()
        if self.snapshot is not None:
            self._render_snapshot(self.snapshot)

    def _populate_environment_hints(self) -> None:
        t = TEXT[self.language]
        adapters = self.service.list_network_adapters()
        serial_ports = self.service.list_serial_ports()
        network_lines = [t["network_adapters"]]
        serial_lines = [t["serial_ports"]]
        network_lines.extend(adapters or [t["not_available"]])
        serial_lines.extend(serial_ports or [t["not_available"]])
        self.network_info.setPlainText("\n".join(network_lines))
        self.serial_ports_info.setPlainText("\n".join(serial_lines))
        self.serial_port_combo.clear()
        self.serial_port_combo.addItem(t["select_serial_port"], "")
        for port in serial_ports:
            self.serial_port_combo.addItem(port, port)

    def _populate_arc_signal_options(self) -> None:
        self._populate_signal_combo(self.arc_signal_combo)

    def _populate_tc_arc_signal_options(self) -> None:
        self._populate_signal_combo(self.tc_arc_signal_combo)

    def _populate_pc_arc_signal_options(self) -> None:
        self._populate_signal_combo(self.pc_arc_signal_combo)

    def _populate_sc_output_options(self) -> None:
        current = self.scan_output_combo.currentData()
        self.scan_output_combo.blockSignals(True)
        self.scan_output_combo.clear()
        for text_key, value in SCAN_OUTPUT_OPTIONS:
            self.scan_output_combo.addItem(TEXT[self.language][text_key], value)
        if current is not None:
            index = self.scan_output_combo.findData(current)
            if index >= 0:
                self.scan_output_combo.setCurrentIndex(index)
        self.scan_output_combo.blockSignals(False)
        self._fit_combo_popup_width(self.scan_output_combo)

    def _populate_sc_shape_options(self) -> None:
        current = self.scan_shape_combo.currentData()
        self.scan_shape_combo.blockSignals(True)
        self.scan_shape_combo.clear()
        for text_key, value in SCAN_SHAPE_OPTIONS:
            self.scan_shape_combo.addItem(TEXT[self.language][text_key], value)
        if current is not None:
            index = self.scan_shape_combo.findData(current)
            if index >= 0:
                self.scan_shape_combo.setCurrentIndex(index)
        self.scan_shape_combo.blockSignals(False)
        self._fit_combo_popup_width(self.scan_shape_combo)

    def _populate_lock_input_signal_options(self) -> None:
        current = self.lock_input_signal_combo.currentData()
        self.lock_input_signal_combo.blockSignals(True)
        self.lock_input_signal_combo.clear()
        for text_key, value in LOCK_INPUT_SIGNAL_OPTIONS:
            self.lock_input_signal_combo.addItem(TEXT[self.language][text_key], value)
        if current is not None:
            index = self.lock_input_signal_combo.findData(current)
            if index >= 0:
                self.lock_input_signal_combo.setCurrentIndex(index)
        self.lock_input_signal_combo.blockSignals(False)
        self._fit_combo_popup_width(self.lock_input_signal_combo)

    def _populate_lock_type_options(self) -> None:
        current = self.lock_type_combo.currentData()
        self.lock_type_combo.blockSignals(True)
        self.lock_type_combo.clear()
        for text_key, value in LOCK_TYPE_OPTIONS:
            self.lock_type_combo.addItem(TEXT[self.language][text_key], value)
        if current is not None:
            index = self.lock_type_combo.findData(current)
            if index >= 0:
                self.lock_type_combo.setCurrentIndex(index)
        self.lock_type_combo.blockSignals(False)
        self._fit_combo_popup_width(self.lock_type_combo)

    def _populate_lock_pid_selection_options(self) -> None:
        current = self.lock_pid_selection_combo.currentData()
        self.lock_pid_selection_combo.blockSignals(True)
        self.lock_pid_selection_combo.clear()
        for text_key, value in LOCK_PID_SELECTION_OPTIONS:
            self.lock_pid_selection_combo.addItem(TEXT[self.language][text_key], value)
        if current is not None:
            index = self.lock_pid_selection_combo.findData(current)
            if index >= 0:
                self.lock_pid_selection_combo.setCurrentIndex(index)
        self.lock_pid_selection_combo.blockSignals(False)
        self._fit_combo_popup_width(self.lock_pid_selection_combo)

    def _populate_pid_output_channel_options(self, combo: QComboBox) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in PID_OUTPUT_CHANNEL_OPTIONS:
            combo.addItem(TEXT[self.language][text_key], value)
        if current is not None:
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)
        self._fit_combo_popup_width(combo)

    def _populate_signal_combo(self, combo: QComboBox) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in ARC_SIGNAL_OPTIONS:
            combo.addItem(TEXT[self.language][text_key], value)
        if current is not None:
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)
        self._fit_combo_popup_width(combo)

    def _configure_combo_boxes(self) -> None:
        combos = (
            self.language_combo,
            self.mode_combo,
            self.serial_port_combo,
            self.arc_signal_combo,
            self.tc_arc_signal_combo,
            self.pc_arc_signal_combo,
            self.scan_output_combo,
            self.scan_shape_combo,
            self.lock_input_signal_combo,
            self.lock_type_combo,
            self.lock_pid_selection_combo,
            self.pid1_output_channel_combo,
            self.pid2_output_channel_combo,
        )
        for combo in combos:
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._fit_combo_popup_width(combo)

    def _fit_combo_popup_width(self, combo: QComboBox) -> None:
        metrics = combo.fontMetrics()
        widths = [metrics.horizontalAdvance(combo.itemText(i)) for i in range(combo.count())]
        current_width = metrics.horizontalAdvance(combo.currentText()) if combo.currentText() else 0
        content_width = max(widths + [current_width, 120])
        target_width = content_width + 48
        combo.view().setMinimumWidth(target_width)
        combo.setMinimumWidth(min(target_width, 260))

    def _update_toggle_button(self, button: QPushButton, enabled: bool) -> None:
        button.blockSignals(True)
        button.setChecked(enabled)
        button.setText(f"{TEXT[self.language]['enable']}  {'●' if enabled else '○'}")
        button.setStyleSheet(
            "background: #45614c; border: 1px solid #6b9474;" if enabled
            else "background: #575757; border: 1px solid #757575;"
        )
        button.blockSignals(False)

    def _set_connection_mode(self, mode: str) -> None:
        is_network = mode == "network"
        self.host_edit.setEnabled(is_network)
        self.serial_port_combo.setEnabled(not is_network)
        self.baudrate_spin.setEnabled(not is_network)

    def _set_busy(self, busy: bool, freeze_controls: bool = True) -> None:
        laser_scroll = self._laser_scroll_value()
        scan_lock_scroll = self._scan_lock_scroll_value()
        self.busy = busy and freeze_controls
        t = TEXT[self.language]
        if busy and freeze_controls:
            self.status_label.setText(t["busy"])
        else:
            self.status_label.setText(t["connected"] if self.service.is_connected else t["disconnected"])
        auto_lock_running = self.auto_lock_controller.is_running or self.auto_lock2_controller.is_running
        self.connect_button.setEnabled(not busy and not auto_lock_running)
        self.disconnect_button.setEnabled(not busy)
        self.refresh_button.setEnabled(not busy and not auto_lock_running)
        writable = (not busy or not freeze_controls) and self.service.is_connected and not auto_lock_running
        previewable = (not busy or not freeze_controls) and not auto_lock_running

        # 这些下拉/勾选项即使未连接设备也允许先切换，用于界面预览和流程确认。
        for widget in (
            self.arc_signal_combo,
            self.tc_arc_signal_combo,
            self.pc_arc_signal_combo,
            self.scan_output_combo,
            self.scan_shape_combo,
            self.lock_input_signal_combo,
            self.lock_error_signal_combo,
            self.lock_type_combo,
            self.lock_pid_selection_combo,
            self.lock_falc_selection_combo,
            self.pid1_output_channel_combo,
            self.pid2_output_channel_combo,
            self.lock_without_lockpoint_check,
        ):
            widget.setEnabled(previewable)
        self.falc_window.set_writable(writable, previewable)
        self.auto_lock_window.set_writable(writable, previewable, auto_lock_running)
        self.auto_lock2_window.set_writable(writable, previewable, self.auto_lock2_controller.is_running)
        self.relock_window.set_writable(writable, previewable)
        self.stabilization_window.set_writable(writable, previewable)

        for widget in (
            self.current_set_spin,
            self.current_clip_spin,
            self.feedforward_factor_spin,
            self.arc_factor_spin,
            self.temp_set_spin,
            self.tc_arc_factor_spin,
            self.pc_voltage_set_spin,
            self.pc_slew_rate_spin,
            self.pc_arc_factor_spin,
            self.scan_amplitude_spin,
            self.scan_offset_spin,
            self.scan_frequency_spin,
            self.pressure_comp_factor_spin,
            self.cc_enable_button,
            self.feedforward_enable_button,
            self.arc_enable_button,
            self.tc_enable_button,
            self.tc_arc_enable_button,
            self.pc_enable_button,
            self.pc_slew_rate_enable_button,
            self.pc_arc_enable_button,
            self.sc_enable_button,
            self.lock_enable_button,
            self.lock_hold_button,
            self.lock_candidate_top_check,
            self.lock_candidate_bottom_check,
            self.lock_candidate_positive_edge_check,
            self.lock_candidate_negative_edge_check,
            self.lock_candidate_edge_level_spin,
            self.lock_candidate_peak_noise_tolerance_spin,
            self.lock_candidate_edge_min_distance_spin,
            self.lock_candidate_top_of_fringe_low_pass_check,
            self.pressure_comp_enable_button,
            self.pid1_gain_spin,
            self.pid1_p_spin,
            self.pid1_i_spin,
            self.pid1_d_spin,
            self.pid1_sign_check,
            self.pid1_use_i_cutoff_check,
            self.pid1_i_cutoff_spin,
            self.pid1_use_limit_check,
            self.pid1_limit_spin,
            self.pid1_enable_check,
            self.pid2_gain_spin,
            self.pid2_p_spin,
            self.pid2_i_spin,
            self.pid2_d_spin,
            self.pid2_sign_check,
            self.pid2_use_limit_check,
            self.pid2_limit_spin,
            self.pid2_enable_check,
        ):
            widget.setEnabled(writable)
        extra_pid_buttons = getattr(self, "pid_precision_buttons", [])
        for button in (*self.precision_buttons, *self.tc_precision_buttons, *self.pc_precision_buttons, *self.sc_precision_buttons, *extra_pid_buttons):
            button.setEnabled(not busy or not freeze_controls)
        for module_buttons in self.module_precision_target_buttons.values():
            for button in module_buttons:
                button.setEnabled(not busy or not freeze_controls)
        self._restore_laser_scroll(laser_scroll)
        self._restore_scan_lock_scroll(scan_lock_scroll)

    def _run_task(self, fn, on_success, task_kind: str = "action") -> bool:
        if self.busy:
            return False
        if self.pending_future is not None:
            if task_kind != "poll" and self.pending_task_kind == "poll":
                self.pending_followup_task = (fn, on_success, task_kind)
                return True
            return False
        freeze_controls = task_kind != "poll"
        self._set_busy(True, freeze_controls=freeze_controls)
        self.pending_success_handler = on_success
        self.pending_task_kind = task_kind
        self.pending_future = self.executor.submit(fn)
        self.future_poll_timer.start()
        return True

    def _poll_future(self) -> None:
        future = self.pending_future
        if future is None or not future.done():
            return

        self.future_poll_timer.stop()
        self.pending_future = None
        on_success = self.pending_success_handler
        self.pending_success_handler = None
        task_kind = self.pending_task_kind
        self.pending_task_kind = "action"

        try:
            result = future.result()
        except Exception as exc:  # noqa: BLE001
            self._handle_task_done(on_success, False, exc, task_kind)
            return

        self._handle_task_done(on_success, True, result, task_kind)

    def _handle_task_done(self, on_success, ok: bool, result: object, task_kind: str) -> None:
        self._set_busy(False, freeze_controls=task_kind != "poll")
        if ok:
            self.connection_loss_notified = False
            if on_success is not None:
                on_success(result)
            self._run_followup_task_if_needed()
            return
        if isinstance(result, Exception) and self._handle_connection_failure(result, task_kind):
            return
        if self.auto_lock_controller.is_running:
            self.auto_lock_controller.handle_task_failure(result)
        if self.auto_lock2_controller.is_running:
            self.auto_lock2_controller.handle_task_failure(result)
        message = self.service.format_error(result) if isinstance(result, Exception) else str(result)
        QMessageBox.critical(self, "Error", message)

    def _run_followup_task_if_needed(self) -> None:
        if self.pending_future is not None or self.pending_followup_task is None:
            return
        fn, on_success, task_kind = self.pending_followup_task
        self.pending_followup_task = None
        self._run_task(fn, on_success, task_kind)

    def _handle_connection_failure(self, exc: Exception, task_kind: str) -> bool:
        if task_kind != "poll":
            return False
        self._reset_after_disconnect(silent=True)
        if self.connection_loss_notified:
            return True
        self.connection_loss_notified = True
        t = TEXT[self.language]
        QMessageBox.critical(self, t["connection_lost_title"], self.service.format_error(exc))
        return True

    def _on_language_changed(self) -> None:
        self.language = self.language_combo.currentData()
        self._apply_texts()

    def _set_cc_precision(self, step: float) -> None:
        self.cc_precision_step = step
        self._apply_step(self._active_precision_target("cc"), step)
        self._update_precision_buttons(self.precision_buttons, step)

    def _set_tc_precision(self, step: float) -> None:
        self.tc_precision_step = step
        self._apply_step(self._active_precision_target("tc"), step)
        self._update_precision_buttons(self.tc_precision_buttons, step)

    def _set_pc_precision(self, step: float) -> None:
        self.pc_precision_step = step
        self._apply_step(self._active_precision_target("pc"), step)
        self._update_precision_buttons(self.pc_precision_buttons, step)

    def _set_sc_precision(self, step: float) -> None:
        self.sc_precision_step = step
        self._apply_step(self._active_precision_target("sc"), step)
        self._update_precision_buttons(self.sc_precision_buttons, step)

    def _set_pid_precision(self, step: float) -> None:
        self.pid_precision_step = step
        self._apply_step(self._active_precision_target("pid"), step)
        self._update_precision_buttons(self.pid_precision_buttons, step)

    def _active_precision_target(self, module: str) -> QDoubleSpinBox:
        return self.module_precision_selected.get(module, self.module_precision_defaults[module])

    def _apply_step(self, spinbox: QDoubleSpinBox, step: float) -> None:
        spinbox.setSingleStep(step)

    def _apply_module_precisions(self) -> None:
        self.current_set_spin.setSingleStep(self.cc_precision_step)
        self.temp_set_spin.setSingleStep(self.tc_precision_step)
        self.pc_voltage_set_spin.setSingleStep(self.pc_precision_step)
        self.scan_amplitude_spin.setSingleStep(self.sc_precision_step)
        if "pid" in self.module_precision_defaults:
            self._apply_step(self._active_precision_target("pid"), self.pid_precision_step)

    def _update_precision_buttons(self, buttons: list[QPushButton], current_step: float) -> None:
        for button in buttons:
            button.blockSignals(True)
            button.setChecked(abs(button._precision_step - current_step) < 1e-12)
            button.blockSignals(False)

    def _update_all_precision_buttons(self) -> None:
        self._update_precision_buttons(self.precision_buttons, self.cc_precision_step)
        self._update_precision_buttons(self.tc_precision_buttons, self.tc_precision_step)
        self._update_precision_buttons(self.pc_precision_buttons, self.pc_precision_step)
        self._update_precision_buttons(self.sc_precision_buttons, self.sc_precision_step)
        if hasattr(self, "pid_precision_buttons"):
            self._update_precision_buttons(self.pid_precision_buttons, self.pid_precision_step)

    def _format_value_with_unit(self, value: float, decimals: int, unit: str) -> str:
        return f"{value:.{decimals}f} {unit}"

    def _unit_only_text(self, unit: str) -> str:
        return unit

    def _laser_scroll_value(self) -> int | None:
        scroll_area = getattr(self, "laser_scroll_area", None)
        if scroll_area is None:
            return None
        return scroll_area.verticalScrollBar().value()

    def _restore_laser_scroll(self, value: int | None) -> None:
        if value is None:
            return
        scroll_area = getattr(self, "laser_scroll_area", None)
        if scroll_area is None:
            return
        scroll_area.verticalScrollBar().setValue(value)

    def _scan_lock_scroll_value(self) -> int | None:
        scroll_area = getattr(self, "scan_lock_scroll_area", None)
        if scroll_area is None:
            return None
        return scroll_area.verticalScrollBar().value()

    def _restore_scan_lock_scroll(self, value: int | None) -> None:
        if value is None:
            return
        scroll_area = getattr(self, "scan_lock_scroll_area", None)
        if scroll_area is None:
            return
        scroll_area.verticalScrollBar().setValue(value)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        return super().eventFilter(watched, event)

    def _on_current_set_changed(self) -> None:
        if self.current_set_programmatic_update:
            return
        self.current_set_dirty = True
        if self.service.is_connected:
            self.current_apply_timer.start()

    def _on_current_set_step_applied(self) -> None:
        if self.current_set_programmatic_update:
            return
        self.current_set_dirty = True
        self.current_apply_timer.stop()
        if not self.service.is_connected:
            return
        if self.busy or self.pending_future is not None:
            self.current_apply_timer.start(20)
            return
        self._apply_current_if_needed()

    def _apply_current_if_needed(self) -> None:
        if not self.service.is_connected or not self.current_set_dirty:
            return
        if self.busy or self.pending_future is not None:
            self.current_apply_timer.start(20)
            return

        value = self.current_set_spin.value()
        self.current_set_dirty = False
        if not self._run_task(lambda: self.service.set_current(value), self._on_snapshot_updated):
            self.current_set_dirty = True
            self.current_apply_timer.start()

    def _confirm_and_run(self, label: str, current: str, value: str, action) -> None:
        t = TEXT[self.language]
        confirmed = QMessageBox.question(
            self,
            t["confirm_large_change_title"],
            t["confirm_large_change_body"].format(label=label, current=current, value=value),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if confirmed == QMessageBox.Yes:
            self._run_task(action, self._on_snapshot_updated)

    def _on_current_clip_finished(self) -> None:
        if not self.service.is_connected or self.cc_programmatic_update or self.snapshot is None:
            return
        value = self.current_clip_spin.value()
        current = self.snapshot.current_clip
        if abs(value - current) < 1e-9:
            return
        self._confirm_and_run(
            TEXT[self.language]["maximum_current"],
            f"{current:.5f}",
            f"{value:.5f}",
            lambda: self.service.set_current_clip(value),
        )

    def _on_feedforward_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.feedforward_programmatic_update:
            return
        self._run_task(lambda: self.service.set_feedforward_enabled(checked), self._on_snapshot_updated)

    def _on_feedforward_factor_finished(self) -> None:
        if not self.service.is_connected or self.feedforward_programmatic_update or self.snapshot is None:
            return
        value = self.feedforward_factor_spin.value()
        current = self.snapshot.feedforward_factor
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_feedforward_factor(value), self._on_snapshot_updated)

    def _on_arc_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.arc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_arc_enabled(checked), self._on_snapshot_updated)

    def _on_arc_signal_changed(self) -> None:
        if not self.service.is_connected or self.arc_programmatic_update or self.snapshot is None:
            return
        value = int(self.arc_signal_combo.currentData())
        if value == self.snapshot.arc_signal:
            return
        self._run_task(lambda: self.service.set_arc_signal(value), self._on_snapshot_updated)

    def _on_arc_factor_finished(self) -> None:
        if not self.service.is_connected or self.arc_programmatic_update or self.snapshot is None:
            return
        value = self.arc_factor_spin.value()
        current = self.snapshot.arc_factor
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_arc_factor(value), self._on_snapshot_updated)

    def _on_tc_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.tc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_tc_enabled(checked), self._on_snapshot_updated)

    def _on_temp_set_finished(self) -> None:
        if not self.service.is_connected or self.tc_programmatic_update or self.snapshot is None:
            return
        value = self.temp_set_spin.value()
        current = self.snapshot.temp_set
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_temp_set(value), self._on_snapshot_updated)

    def _on_tc_arc_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.tc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_tc_arc_enabled(checked), self._on_snapshot_updated)

    def _on_tc_arc_signal_changed(self) -> None:
        if not self.service.is_connected or self.tc_programmatic_update or self.snapshot is None:
            return
        value = int(self.tc_arc_signal_combo.currentData())
        if value == self.snapshot.tc_arc_signal:
            return
        self._run_task(lambda: self.service.set_tc_arc_signal(value), self._on_snapshot_updated)

    def _on_tc_arc_factor_finished(self) -> None:
        if not self.service.is_connected or self.tc_programmatic_update or self.snapshot is None:
            return
        value = self.tc_arc_factor_spin.value()
        current = self.snapshot.tc_arc_factor
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_tc_arc_factor(value), self._on_snapshot_updated)

    def _on_pc_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.pc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_pc_enabled(checked), self._on_snapshot_updated)

    def _on_pc_voltage_set_finished(self) -> None:
        if not self.service.is_connected or self.pc_programmatic_update or self.snapshot is None:
            return
        value = self.pc_voltage_set_spin.value()
        current = self.snapshot.pc_voltage_set
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_pc_voltage_set(value), self._on_snapshot_updated)

    def _on_pc_slew_rate_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.pc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_pc_slew_rate_enabled(checked), self._on_snapshot_updated)

    def _on_pc_slew_rate_finished(self) -> None:
        if not self.service.is_connected or self.pc_programmatic_update or self.snapshot is None:
            return
        value = self.pc_slew_rate_spin.value()
        current = self.snapshot.pc_slew_rate
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_pc_slew_rate(value), self._on_snapshot_updated)

    def _on_pc_arc_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.pc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_pc_arc_enabled(checked), self._on_snapshot_updated)

    def _on_pc_arc_signal_changed(self) -> None:
        if not self.service.is_connected or self.pc_programmatic_update or self.snapshot is None:
            return
        value = int(self.pc_arc_signal_combo.currentData())
        if value == self.snapshot.pc_arc_signal:
            return
        self._run_task(lambda: self.service.set_pc_arc_signal(value), self._on_snapshot_updated)

    def _on_pc_arc_factor_finished(self) -> None:
        if not self.service.is_connected or self.pc_programmatic_update or self.snapshot is None:
            return
        value = self.pc_arc_factor_spin.value()
        current = self.snapshot.pc_arc_factor
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_pc_arc_factor(value), self._on_snapshot_updated)

    def _on_pressure_comp_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.pc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_pressure_comp_enabled(checked), self._on_snapshot_updated)

    def _on_pressure_comp_factor_finished(self) -> None:
        if not self.service.is_connected or self.pc_programmatic_update or self.snapshot is None:
            return
        value = self.pressure_comp_factor_spin.value()
        current = self.snapshot.pressure_comp_factor
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_pressure_comp_factor(value), self._on_snapshot_updated)

    def _on_sc_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.sc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_sc_enabled(checked), self._on_snapshot_updated)

    def _on_sc_amplitude_finished(self) -> None:
        if not self.service.is_connected or self.sc_programmatic_update or self.snapshot is None:
            return
        value = self.scan_amplitude_spin.value()
        current = self.snapshot.sc_amplitude
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_sc_amplitude(value), self._on_snapshot_updated)

    def _on_sc_offset_finished(self) -> None:
        if not self.service.is_connected or self.sc_programmatic_update or self.snapshot is None:
            return
        value = self.scan_offset_spin.value()
        current = self.snapshot.sc_offset
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_sc_offset(value), self._on_snapshot_updated)

    def _on_sc_output_changed(self) -> None:
        if not self.service.is_connected or self.sc_programmatic_update or self.snapshot is None:
            return
        value = int(self.scan_output_combo.currentData())
        if value == self.snapshot.sc_output_channel:
            return
        self._run_task(lambda: self.service.set_sc_output_channel(value), self._on_snapshot_updated)

    def _on_sc_frequency_finished(self) -> None:
        if not self.service.is_connected or self.sc_programmatic_update or self.snapshot is None:
            return
        value = self.scan_frequency_spin.value()
        current = self.snapshot.sc_frequency
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: self.service.set_sc_frequency(value), self._on_snapshot_updated)

    def _on_sc_shape_changed(self) -> None:
        if not self.service.is_connected or self.sc_programmatic_update or self.snapshot is None:
            return
        value = int(self.scan_shape_combo.currentData())
        if value == self.snapshot.sc_signal_type:
            return
        self._run_task(lambda: self.service.set_sc_signal_type(value), self._on_snapshot_updated)

    def _on_lock_enabled_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.lock_programmatic_update:
            return
        self._run_task(lambda: self.service.set_lock_enabled(checked), self._on_snapshot_updated)

    def _on_lock_hold_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.lock_programmatic_update:
            return
        self._run_task(lambda: self.service.set_lock_hold(checked), self._on_snapshot_updated)

    def _on_lock_input_signal_changed(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = int(self.lock_input_signal_combo.currentData())
        if value == self.snapshot.lock_input_channel:
            return
        self._run_task(lambda: self.service.set_lock_input_channel(value), self._on_snapshot_updated)

    def _on_lock_error_signal_changed(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = int(self.lock_error_signal_combo.currentData())
        if value == self.snapshot.lock_error_channel:
            return
        self._run_task(lambda: self.service.set_lock_error_channel(value), self._on_snapshot_updated)

    def _on_lock_type_changed(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = int(self.lock_type_combo.currentData())
        if value == self.snapshot.lock_type:
            return
        self._run_task(lambda: self.service.set_lock_type(value), self._on_snapshot_updated)

    def _on_lock_pid_selection_changed(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = int(self.lock_pid_selection_combo.currentData())
        if value == self.snapshot.lock_pid_selection:
            return
        self._run_task(lambda: self.service.set_lock_pid_selection(value), self._on_snapshot_updated)

    def _on_lock_falc_selection_changed(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = int(self.lock_falc_selection_combo.currentData())
        if value == self.snapshot.lock_falc_selection:
            return
        self._run_task(lambda: self.service.set_lock_falc_selection(value), self._on_snapshot_updated)

    def _on_lock_without_lockpoint_changed(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        checked = self.lock_without_lockpoint_check.isChecked()
        if checked == self.snapshot.lock_without_lockpoint:
            return
        self._run_task(lambda: self.service.set_lock_without_lockpoint(checked), self._on_snapshot_updated)

    def _on_lock_candidate_top_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_top_enabled:
            return
        self._run_task(lambda: self.service.set_lock_candidate_top_enabled(checked), self._on_snapshot_updated)

    def _on_lock_candidate_bottom_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_bottom_enabled:
            return
        self._run_task(lambda: self.service.set_lock_candidate_bottom_enabled(checked), self._on_snapshot_updated)

    def _on_lock_candidate_positive_edge_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_positive_edge_enabled:
            return
        self._run_task(lambda: self.service.set_lock_candidate_positive_edge_enabled(checked), self._on_snapshot_updated)

    def _on_lock_candidate_negative_edge_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_negative_edge_enabled:
            return
        self._run_task(lambda: self.service.set_lock_candidate_negative_edge_enabled(checked), self._on_snapshot_updated)

    def _on_lock_candidate_edge_level_finished(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = self.lock_candidate_edge_level_spin.value()
        if abs(value - self.snapshot.lock_candidate_edge_level) < 1e-12:
            return
        self._run_task(lambda: self.service.set_lock_candidate_edge_level(value), self._on_snapshot_updated)

    def _on_lock_candidate_peak_noise_tolerance_finished(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = self.lock_candidate_peak_noise_tolerance_spin.value()
        if abs(value - self.snapshot.lock_candidate_peak_noise_tolerance) < 1e-12:
            return
        self._run_task(lambda: self.service.set_lock_candidate_peak_noise_tolerance(value), self._on_snapshot_updated)

    def _on_lock_candidate_edge_min_distance_finished(self) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = int(self.lock_candidate_edge_min_distance_spin.value())
        if value == self.snapshot.lock_candidate_edge_min_distance:
            return
        self._run_task(lambda: self.service.set_lock_candidate_edge_min_distance(value), self._on_snapshot_updated)

    def _on_lock_candidate_top_of_fringe_low_pass_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_top_of_fringe_low_pass:
            return
        self._run_task(
            lambda: self.service.set_lock_candidate_top_of_fringe_low_pass(checked),
            self._on_snapshot_updated,
        )

    def _on_auto_lock_error_signal_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        value = int(self.auto_lock_window.config_panel.error_signal_combo.currentData())
        if value == self.snapshot.lock_error_channel:
            return
        self._run_task(lambda: self.service.set_lock_error_channel(value), self._on_snapshot_updated)

    def _on_auto_lock_falc_selection_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        value = int(self.auto_lock_window.config_panel.falc_selection_combo.currentData())
        if value == self.snapshot.lock_falc_selection:
            return
        self._run_task(lambda: self.service.set_lock_falc_selection(value), self._on_snapshot_updated)

    def _on_auto_lock_falc_path_selection_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = int(self.auto_lock_window.config_panel.falc_path_combo.currentData())
        if value == self.snapshot.falc1.path_selection:
            return
        self._run_task(lambda: self.service.set_falc1_path_selection(value), self._on_snapshot_updated)

    def _on_auto_lock_candidate_top_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_top_enabled:
            return
        self._run_task(lambda: self.service.set_lock_candidate_top_enabled(checked), self._on_snapshot_updated)

    def _on_auto_lock_candidate_bottom_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_bottom_enabled:
            return
        self._run_task(lambda: self.service.set_lock_candidate_bottom_enabled(checked), self._on_snapshot_updated)

    def _on_auto_lock_candidate_positive_edge_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_positive_edge_enabled:
            return
        self._run_task(lambda: self.service.set_lock_candidate_positive_edge_enabled(checked), self._on_snapshot_updated)

    def _on_auto_lock_candidate_negative_edge_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_negative_edge_enabled:
            return
        self._run_task(lambda: self.service.set_lock_candidate_negative_edge_enabled(checked), self._on_snapshot_updated)

    def _on_auto_lock_candidate_edge_level_finished(self) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        value = self.auto_lock_window.config_panel.candidate_edge_level_spin.value()
        if abs(value - self.snapshot.lock_candidate_edge_level) < 1e-12:
            return
        self._run_task(lambda: self.service.set_lock_candidate_edge_level(value), self._on_snapshot_updated)

    def _on_auto_lock_candidate_peak_noise_tolerance_finished(self) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        value = self.auto_lock_window.config_panel.candidate_peak_noise_tolerance_spin.value()
        if abs(value - self.snapshot.lock_candidate_peak_noise_tolerance) < 1e-12:
            return
        self._run_task(lambda: self.service.set_lock_candidate_peak_noise_tolerance(value), self._on_snapshot_updated)

    def _on_auto_lock_candidate_edge_min_distance_finished(self) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        value = int(self.auto_lock_window.config_panel.candidate_edge_min_distance_spin.value())
        if value == self.snapshot.lock_candidate_edge_min_distance:
            return
        self._run_task(lambda: self.service.set_lock_candidate_edge_min_distance(value), self._on_snapshot_updated)

    def _on_auto_lock_candidate_top_of_fringe_low_pass_changed(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        if checked == self.snapshot.lock_candidate_top_of_fringe_low_pass:
            return
        self._run_task(
            lambda: self.service.set_lock_candidate_top_of_fringe_low_pass(checked),
            self._on_snapshot_updated,
        )

    def _on_relock_detection_enabled_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        if checked == self.snapshot.relock_detection_enabled:
            return
        self._run_task(lambda: self.service.set_relock_detection_enabled(checked), self._on_snapshot_updated)

    def _on_relock_input_signal_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        value = int(self.relock_window.lock_detection_panel.input_signal_combo.currentData())
        if value == self.snapshot.relock_input_channel:
            return
        self._run_task(lambda: self.service.set_relock_input_channel(value), self._on_snapshot_updated)

    def _on_relock_level_high_finished(self) -> None:
        if not self.relock_window.validate_window_levels():
            return
        self._run_relock_spin_write(
            "relock_level_high",
            self.relock_window.lock_detection_panel.level_high_spin,
            self.service.set_relock_level_high,
        )

    def _on_relock_level_low_finished(self) -> None:
        if not self.relock_window.validate_window_levels():
            return
        self._run_relock_spin_write(
            "relock_level_low",
            self.relock_window.lock_detection_panel.level_low_spin,
            self.service.set_relock_level_low,
        )

    def _on_relock_hysteresis_finished(self) -> None:
        if not self.relock_window.validate_window_levels():
            return
        self._run_relock_spin_write(
            "relock_level_hysteresis",
            self.relock_window.lock_detection_panel.hysteresis_spin,
            self.service.set_relock_level_hysteresis,
        )

    def _on_relock_delay_finished(self) -> None:
        self._run_relock_spin_write(
            "relock_delay",
            self.relock_window.lock_detection_panel.delay_spin,
            self.service.set_relock_delay,
        )

    def _on_relock_reset_enabled_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        checked = self.relock_window.lock_detection_panel.enable_reset_check.isChecked()
        if checked == self.snapshot.relock_reset_enabled:
            return
        self._run_task(lambda: self.service.set_relock_reset_enabled(checked), self._on_snapshot_updated)

    def _on_relock_enabled_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        if checked == self.snapshot.relock_enabled:
            return
        self._run_task(lambda: self.service.set_relock_enabled(checked), self._on_snapshot_updated)

    def _on_relock_amplitude_finished(self) -> None:
        self._run_relock_spin_write(
            "relock_amplitude",
            self.relock_window.relock_panel.amplitude_spin,
            self.service.set_relock_amplitude,
        )

    def _on_relock_frequency_finished(self) -> None:
        self._run_relock_spin_write(
            "relock_frequency",
            self.relock_window.relock_panel.frequency_spin,
            self.service.set_relock_frequency,
        )

    def _on_relock_output_channel_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        value = int(self.relock_window.relock_panel.output_channel_combo.currentData())
        if value == self.snapshot.relock_output_channel:
            return
        self._run_task(lambda: self.service.set_relock_output_channel(value), self._on_snapshot_updated)

    def _on_stabilization_enabled_toggled(self, checked: bool) -> None:
        snapshot = self._stabilization_snapshot()
        if snapshot is None or checked == snapshot.enabled:
            return
        self._run_task(lambda: self.service.set_stabilization_enabled(checked), self._on_snapshot_updated)

    def _on_stabilization_pd_ext_input_channel_changed(self) -> None:
        snapshot = self._stabilization_snapshot()
        if snapshot is None:
            return
        value = int(self.stabilization_window.power_panel.external_physical_channel_combo.currentData())
        if value == snapshot.pd_ext_input_channel:
            return
        self._run_task(lambda: self.service.set_stabilization_pd_ext_input_channel(value), self._on_snapshot_updated)

    def _on_stabilization_cal_factor_finished(self) -> None:
        self._run_stabilization_spin_write(
            "pd_ext_cal_factor",
            self.stabilization_window.power_panel.cal_factor_spin,
            self.service.set_stabilization_pd_ext_cal_factor,
        )

    def _on_stabilization_cal_offset_finished(self) -> None:
        self._run_stabilization_spin_write(
            "pd_ext_cal_offset",
            self.stabilization_window.power_panel.cal_offset_spin,
            self.service.set_stabilization_pd_ext_cal_offset,
        )

    def _on_stabilization_set_level_finished(self) -> None:
        self._run_stabilization_spin_write(
            "setpoint",
            self.stabilization_window.power_panel.set_level_spin,
            self.service.set_stabilization_setpoint,
        )

    def _on_stabilization_gain_all_finished(self) -> None:
        self._run_stabilization_spin_write(
            "gain_all",
            self.stabilization_window.power_panel.gain_all_spin,
            self.service.set_stabilization_gain_all,
        )

    def _on_stabilization_gain_p_finished(self) -> None:
        self._run_stabilization_spin_write(
            "gain_p",
            self.stabilization_window.power_panel.gain_p_spin,
            self.service.set_stabilization_gain_p,
        )

    def _on_stabilization_gain_i_finished(self) -> None:
        self._run_stabilization_spin_write(
            "gain_i",
            self.stabilization_window.power_panel.gain_i_spin,
            self.service.set_stabilization_gain_i,
        )

    def _on_stabilization_gain_d_finished(self) -> None:
        self._run_stabilization_spin_write(
            "gain_d",
            self.stabilization_window.power_panel.gain_d_spin,
            self.service.set_stabilization_gain_d,
        )

    def _on_stabilization_hold_output_on_unlock_changed(self) -> None:
        snapshot = self._stabilization_snapshot()
        if snapshot is None:
            return
        checked = self.stabilization_window.power_panel.hold_output_check.isChecked()
        if checked == snapshot.hold_output_on_unlock:
            return
        self._run_task(lambda: self.service.set_stabilization_hold_output_on_unlock(checked), self._on_snapshot_updated)

    def _on_stabilization_window_enabled_toggled(self, checked: bool) -> None:
        snapshot = self._stabilization_snapshot()
        if snapshot is None or checked == snapshot.window_enabled:
            return
        self._run_task(lambda: self.service.set_stabilization_window_enabled(checked), self._on_snapshot_updated)

    def _on_stabilization_window_level_finished(self) -> None:
        self._run_stabilization_spin_write(
            "window_level_low",
            self.stabilization_window.detection_panel.level_spin,
            self.service.set_stabilization_window_level_low,
        )

    def _on_stabilization_window_hysteresis_finished(self) -> None:
        self._run_stabilization_spin_write(
            "window_level_hysteresis",
            self.stabilization_window.detection_panel.hysteresis_spin,
            self.service.set_stabilization_window_level_hysteresis,
        )

    def _on_pid1_gain_finished(self) -> None:
        self._run_pid_spin_write("pid1_gain_all", self.pid1_gain_spin, self.service.set_pid1_gain_all)

    def _on_pid1_p_finished(self) -> None:
        self._run_pid_spin_write("pid1_gain_p", self.pid1_p_spin, self.service.set_pid1_gain_p)

    def _on_pid1_i_finished(self) -> None:
        self._run_pid_spin_write("pid1_gain_i", self.pid1_i_spin, self.service.set_pid1_gain_i)

    def _on_pid1_d_finished(self) -> None:
        self._run_pid_spin_write("pid1_gain_d", self.pid1_d_spin, self.service.set_pid1_gain_d)

    def _on_pid1_output_channel_changed(self) -> None:
        self._run_pid_combo_write("pid1_output_channel", self.pid1_output_channel_combo, self.service.set_pid1_output_channel)

    def _on_pid1_sign_changed(self) -> None:
        self._run_pid_check_write("pid1_sign", self.pid1_sign_check, self.service.set_pid1_sign)

    def _on_pid1_i_cutoff_enabled_changed(self) -> None:
        self._run_pid_check_write("pid1_i_cutoff_enabled", self.pid1_use_i_cutoff_check, self.service.set_pid1_i_cutoff_enabled)

    def _on_pid1_i_cutoff_finished(self) -> None:
        self._run_pid_spin_write("pid1_i_cutoff", self.pid1_i_cutoff_spin, self.service.set_pid1_i_cutoff)

    def _on_pid1_limit_enabled_changed(self) -> None:
        self._run_pid_check_write("pid1_limit_enabled", self.pid1_use_limit_check, self.service.set_pid1_limit_enabled)

    def _on_pid1_limit_finished(self) -> None:
        self._run_pid_spin_write("pid1_limit_max", self.pid1_limit_spin, self.service.set_pid1_limit_max)

    def _on_pid1_enabled_changed(self) -> None:
        self._run_pid_check_write("pid1_enabled", self.pid1_enable_check, self.service.set_pid1_enabled)

    def _on_pid2_gain_finished(self) -> None:
        self._run_pid_spin_write("pid2_gain_all", self.pid2_gain_spin, self.service.set_pid2_gain_all)

    def _on_pid2_p_finished(self) -> None:
        self._run_pid_spin_write("pid2_gain_p", self.pid2_p_spin, self.service.set_pid2_gain_p)

    def _on_pid2_i_finished(self) -> None:
        self._run_pid_spin_write("pid2_gain_i", self.pid2_i_spin, self.service.set_pid2_gain_i)

    def _on_pid2_d_finished(self) -> None:
        self._run_pid_spin_write("pid2_gain_d", self.pid2_d_spin, self.service.set_pid2_gain_d)

    def _on_pid2_output_channel_changed(self) -> None:
        self._run_pid_combo_write("pid2_output_channel", self.pid2_output_channel_combo, self.service.set_pid2_output_channel)

    def _on_pid2_sign_changed(self) -> None:
        self._run_pid_check_write("pid2_sign", self.pid2_sign_check, self.service.set_pid2_sign)

    def _on_pid2_limit_enabled_changed(self) -> None:
        self._run_pid_check_write("pid2_limit_enabled", self.pid2_use_limit_check, self.service.set_pid2_limit_enabled)

    def _on_pid2_limit_finished(self) -> None:
        self._run_pid_spin_write("pid2_limit_max", self.pid2_limit_spin, self.service.set_pid2_limit_max)

    def _on_pid2_enabled_changed(self) -> None:
        self._run_pid_check_write("pid2_enabled", self.pid2_enable_check, self.service.set_pid2_enabled)

    def _run_pid_spin_write(self, snapshot_attr: str, spinbox: QDoubleSpinBox, setter) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = spinbox.value()
        current = getattr(self.snapshot, snapshot_attr)
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: setter(value), self._on_snapshot_updated)

    def _run_pid_combo_write(self, snapshot_attr: str, combo: QComboBox, setter) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = int(combo.currentData())
        if value == getattr(self.snapshot, snapshot_attr):
            return
        self._run_task(lambda: setter(value), self._on_snapshot_updated)

    def _run_pid_check_write(self, snapshot_attr: str, check, setter) -> None:
        if not self.service.is_connected or self.lock_programmatic_update or self.snapshot is None:
            return
        value = check.isChecked()
        if value == getattr(self.snapshot, snapshot_attr):
            return
        self._run_task(lambda: setter(value), self._on_snapshot_updated)

    def _run_relock_spin_write(self, snapshot_attr: str, spinbox: QDoubleSpinBox, setter) -> None:
        if not self.service.is_connected or self.snapshot is None:
            return
        value = spinbox.value()
        current = getattr(self.snapshot, snapshot_attr)
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: setter(value), self._on_snapshot_updated)

    def _run_stabilization_spin_write(self, snapshot_attr: str, spinbox: QDoubleSpinBox, setter) -> None:
        snapshot = self._stabilization_snapshot()
        if snapshot is None:
            return
        value = spinbox.value()
        current = getattr(snapshot, snapshot_attr)
        if abs(value - current) < 1e-9:
            return
        self._run_task(lambda: setter(value), self._on_snapshot_updated)

    def _stabilization_snapshot(self):
        if not self.service.is_connected or self.snapshot is None:
            return None
        return self.snapshot.stabilization

    def _on_falc_input_gain_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = int(self.falc_window.input_gain_combo.currentData())
        if value == self.snapshot.falc1.input_gain:
            return
        self._run_task(lambda: self.service.set_falc1_input_gain(value), self._on_snapshot_updated)

    def _on_falc_input_offset_finished(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = self.falc_window.input_offset_spin.value()
        current = self.snapshot.falc1.input_offset
        if abs(value - current) < 1e-12:
            return
        self._run_task(lambda: self.service.set_falc1_input_offset(value), self._on_snapshot_updated)

    def _on_falc_path_selection_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = int(self.falc_window.path_selection_combo.currentData())
        if value == self.snapshot.falc1.path_selection:
            return
        self._run_task(lambda: self.service.set_falc1_path_selection(value), self._on_snapshot_updated)

    def _on_falc_mon_config_changed(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = int(self.falc_window.mon_config_combo.currentData())
        if value == self.snapshot.falc1.mon_config:
            return
        self._run_task(lambda: self.service.set_falc1_mon_config(value), self._on_snapshot_updated)

    def _on_falc_main_enabled_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        if checked == self.snapshot.falc1.main.enabled:
            return
        self._run_task(lambda: self.service.set_falc1_main_enabled(checked), self._on_snapshot_updated)

    def _on_falc_main_gain_finished(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = self.falc_window.main_gain_spin.value()
        current = self.snapshot.falc1.main.gain_all
        if abs(value - current) < 1e-12:
            return
        self._run_task(lambda: self.service.set_falc1_main_gain_all(value), self._on_snapshot_updated)

    def _on_falc_main_use_external_input_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        if checked == self.snapshot.falc1.main.use_external_input:
            return
        self._run_task(lambda: self.service.set_falc1_main_use_external_input(checked), self._on_snapshot_updated)

    def _on_falc_filter_enabled_toggled(self, filter_name: str, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        current = getattr(self.snapshot.falc1.main, f"{filter_name}_enabled")
        if checked == current:
            return
        self._run_task(
            lambda: self.service.set_falc1_main_filter_enabled(filter_name, checked),
            self._on_snapshot_updated,
        )

    def _on_falc_filter_value_changed(self, filter_name: str) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = self.falc_window.current_filter_value(filter_name)
        if value is None:
            QMessageBox.warning(
                self,
                "Warning",
                "FALC preset must be an integer raw device value / FALC 预设值必须为设备整数原始值",
            )
            self.falc_window.render_snapshot(self.snapshot)
            return
        current = getattr(self.snapshot.falc1.main, filter_name)
        if value == current:
            return
        self._run_task(
            lambda: self.service.set_falc1_main_filter_value(filter_name, value),
            self._on_snapshot_updated,
        )

    def _on_falc_unlim_enabled_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        if checked == self.snapshot.falc1.unlim.enabled:
            return
        self._run_task(lambda: self.service.set_falc1_unlim_enabled(checked), self._on_snapshot_updated)

    def _on_falc_unlim_hold_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        if checked == self.snapshot.falc1.unlim.hold:
            return
        self._run_task(lambda: self.service.set_falc1_unlim_hold(checked), self._on_snapshot_updated)

    def _on_falc_unlim_input_offset_finished(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = self.falc_window.unlim_input_offset_spin.value()
        current = self.snapshot.falc1.unlim.input_offset
        if abs(value - current) < 1e-12:
            return
        self._run_task(lambda: self.service.set_falc1_unlim_input_offset(value), self._on_snapshot_updated)

    def _on_falc_unlim_output_range_finished(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = self.falc_window.unlim_output_range_spin.value()
        current = self.snapshot.falc1.unlim.output_range
        if abs(value - current) < 1e-12:
            return
        self._run_task(lambda: self.service.set_falc1_unlim_output_range(value), self._on_snapshot_updated)

    def _on_falc_unlim_slew_rate_finished(self) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        value = int(round(self.falc_window.unlim_slew_rate_spin.value()))
        current = self.snapshot.falc1.unlim.slew_rate
        if value == current:
            return
        self._run_task(lambda: self.service.set_falc1_unlim_slew_rate(value), self._on_snapshot_updated)

    def _on_falc_unlim_sign_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.snapshot is None or self.snapshot.falc1 is None:
            return
        if checked == self.snapshot.falc1.unlim.sign:
            return
        self._run_task(lambda: self.service.set_falc1_unlim_sign(checked), self._on_snapshot_updated)

    def _on_cc_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.cc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_cc_enabled(checked), self._on_snapshot_updated)

    def connect_device(self) -> None:
        mode = self.mode_combo.currentData()
        if mode == "network":
            target = self.host_edit.text().strip()
        else:
            target = str(self.serial_port_combo.currentData() or "").strip()
        if not target:
            QMessageBox.warning(self, "Warning", "Please enter a connection target / 请输入连接目标")
            return
        settings = ConnectionSettings(
            mode=mode,
            target=target,
            baudrate=self.baudrate_spin.value(),
            timeout=self.timeout_spin.value(),
        )
        self._run_task(lambda: self.service.connect(settings), self._on_snapshot_updated)

    def _reset_after_disconnect(self, silent: bool = False) -> None:
        self.refresh_timer.stop()
        self.current_apply_timer.stop()
        self.pending_followup_task = None
        try:
            self.service.disconnect()
        except Exception as exc:  # noqa: BLE001
            if not silent:
                QMessageBox.critical(self, "Error", self.service.format_error(exc))
            return
        self.auto_lock_controller.handle_disconnect()
        self.auto_lock2_controller.handle_disconnect()
        self.snapshot = None
        self.last_device_current_set = None
        self.parameter_table.setRowCount(0)
        self.current_set_programmatic_update = True
        self.current_set_spin.setValue(0.0)
        self.current_set_programmatic_update = False
        self.current_clip_spin.setValue(0.0)
        self.feedforward_factor_spin.setValue(0.0)
        self.arc_factor_spin.setValue(0.0)
        self.temp_set_spin.setValue(0.0)
        self.tc_arc_factor_spin.setValue(0.0)
        self.pc_voltage_set_spin.setValue(0.0)
        self.pc_slew_rate_spin.setValue(0.0)
        self.pc_arc_factor_spin.setValue(0.0)
        self.scan_amplitude_spin.setValue(0.0)
        self.scan_offset_spin.setValue(0.0)
        self.scan_frequency_spin.setValue(0.0)
        self.lock_without_lockpoint_check.blockSignals(True)
        self.lock_without_lockpoint_check.setChecked(False)
        self.lock_without_lockpoint_check.blockSignals(False)
        self.pressure_comp_factor_spin.setValue(0.0)
        self.laser_controller.reset_readbacks()
        self.scan_lock_controller.render_snapshot(self._empty_scan_snapshot())
        self.auto_lock_window.reset_state(self.language)
        self.auto_lock2_window.reset_state(self.language)
        self.falc_window.reset_state(self.language)
        self.relock_window.reset_state(self.language)
        self.stabilization_window.reset_state(self.language)
        self.current_set_dirty = False
        self._update_toggle_button(self.cc_enable_button, False)
        self._update_toggle_button(self.feedforward_enable_button, False)
        self._update_toggle_button(self.arc_enable_button, False)
        self._update_toggle_button(self.tc_enable_button, False)
        self._update_toggle_button(self.tc_arc_enable_button, False)
        self._update_toggle_button(self.pc_enable_button, False)
        self._update_toggle_button(self.pc_slew_rate_enable_button, False)
        self._update_toggle_button(self.pc_arc_enable_button, False)
        self._update_toggle_button(self.sc_enable_button, False)
        self._update_toggle_button(self.lock_enable_button, False)
        self._update_toggle_button(self.lock_hold_button, False)
        self._update_toggle_button(self.pressure_comp_enable_button, False)
        self._set_busy(False)
        if not silent:
            self.connection_loss_notified = False

    def disconnect_device(self) -> None:
        self._reset_after_disconnect(silent=False)

    def refresh_snapshot(self) -> None:
        if not self.service.is_connected or self.busy:
            return
        self._run_task(self.service.read_snapshot, self._on_snapshot_updated, task_kind="poll")

    def _on_snapshot_updated(self, snapshot: DeviceSnapshot) -> None:
        self.snapshot = snapshot
        self._render_snapshot(snapshot)
        if (
            not self.auto_lock_controller.is_running
            and not self.auto_lock2_controller.is_running
            and not self.refresh_timer.isActive()
        ):
            self.refresh_timer.start()

    def _render_snapshot(self, snapshot: DeviceSnapshot) -> None:
        laser_scroll = self._laser_scroll_value()
        scan_lock_scroll = self._scan_lock_scroll_value()
        self.laser_controller.render_snapshot(snapshot)
        self._restore_laser_scroll(laser_scroll)
        self.scan_lock_controller.render_snapshot(snapshot)
        self._restore_scan_lock_scroll(scan_lock_scroll)
        self.auto_lock_window.render_snapshot(snapshot)
        self.auto_lock2_controller.render_snapshot(snapshot)
        self.falc_window.render_snapshot(snapshot)
        self.relock_window.render_snapshot(snapshot)
        self.stabilization_window.render_snapshot(snapshot)

    def _empty_scan_snapshot(self):
        return type(
            "ScanResetSnapshot",
            (),
            {
                "sc_amplitude": 0.0,
                "sc_offset": 0.0,
                "sc_frequency": 0.0,
                "sc_output_channel": SCAN_OUTPUT_OPTIONS[0][1],
                "sc_signal_type": SCAN_SHAPE_OPTIONS[0][1],
                "sc_enabled": False,
                "sc_unit": TEXT[self.language]["voltage_unit"],
                "lock_state": 0,
                "lock_state_txt": TEXT[self.language]["not_available"],
                "lock_enabled": False,
                "lock_hold": False,
                "lock_input_channel": LOCK_INPUT_SIGNAL_OPTIONS[0][1],
                "lock_error_channel": LOCK_ERROR_SIGNAL_OPTIONS[0][1],
                "lock_type": LOCK_TYPE_OPTIONS[0][1],
                "lock_pid_selection": LOCK_PID_SELECTION_OPTIONS[0][1],
                "lock_falc_selection": LOCK_FALC_SELECTION_OPTIONS[0][1],
                "lock_without_lockpoint": False,
                "lock_candidate_top_enabled": False,
                "lock_candidate_bottom_enabled": False,
                "lock_candidate_positive_edge_enabled": False,
                "lock_candidate_negative_edge_enabled": False,
                "lock_candidate_edge_level": 0.0,
                "lock_candidate_peak_noise_tolerance": 0.0,
                "lock_candidate_edge_min_distance": 0,
                "lock_candidate_top_of_fringe_low_pass": False,
                "pid1_enabled": False,
                "pid1_gain_all": 0.0,
                "pid1_gain_p": 0.0,
                "pid1_gain_i": 0.0,
                "pid1_gain_d": 0.0,
                "pid1_output_channel": PID_OUTPUT_CHANNEL_OPTIONS[0][1],
                "pid1_sign": False,
                "pid1_i_cutoff_enabled": False,
                "pid1_i_cutoff": 0.0,
                "pid1_limit_enabled": False,
                "pid1_limit_max": 0.0,
                "pid2_enabled": False,
                "pid2_gain_all": 0.0,
                "pid2_gain_p": 0.0,
                "pid2_gain_i": 0.0,
                "pid2_gain_d": 0.0,
                "pid2_output_channel": PID_OUTPUT_CHANNEL_OPTIONS[0][1],
                "pid2_sign": False,
                "pid2_limit_enabled": False,
                "pid2_limit_max": 0.0,
            },
        )()

    def closeEvent(self, event) -> None:  # noqa: N802
        t = TEXT[self.language]
        confirmed = QMessageBox.question(
            self,
            t["exit_confirm_title"],
            t["exit_confirm_body"],
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirmed != QMessageBox.Yes:
            event.ignore()
            return
        self.refresh_timer.stop()
        self.future_poll_timer.stop()
        self.current_apply_timer.stop()
        for window in (
            self.laser_window,
            self.falc_window,
            self.scan_lock_window,
            self.auto_lock_window,
            self.auto_lock2_window,
            self.relock_window,
            self.stabilization_window,
        ):
            window.request_shutdown()
            window.close()
        self._reset_after_disconnect(silent=True)
        self.executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)


def main() -> int:
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except AttributeError:
        pass
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    fit_window_to_screen(window)
    QMessageBox.information(
        window,
        TEXT["zh"]["safety_title"],
        f"{TEXT['zh']['safety_text']}\n\n{TEXT['en']['safety_text']}",
    )
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
