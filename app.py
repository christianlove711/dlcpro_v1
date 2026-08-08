from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dlcpro_service import (
    ConnectionSettings,
    DeviceSnapshot,
    DlcProService,
    SnapshotRequest,
    SnapshotSection,
)
from device_task_coordinator import DeviceTaskCoordinator
from daq_pc.unified_daq_gui import APP_STYLE as DAQ_APP_STYLE
from daq_pc.unified_daq_gui import MainWindow as DaqMainWindow
from notifications import NotificationService
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
from controllers import (
    AutoLockController,
    FalcController,
    LaserController,
    ScanLockController,
)
from widgets.common_controls import CompactMessageDialog, SafeComboBox, SafeSpinBox
from ui_scaling import (
    SCALE_OPTIONS, UiScaleManager, WindowLayoutManager, schedule_window_fit,
)
from windows import (
    AutoLockWindow,
    FalcProWindow,
    LaserWindow,
    ScanLockWindow,
    build_laser_page,
    build_scan_lock_page,
)

class DeviceParametersDialog(QDialog):
    """Non-modal full device-parameter view backed by the overview table."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.resize(720, 520)
        self.setMinimumSize(520, 360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.table = QTableWidget(0, 2, self)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Close, self)
        self.buttons.rejected.connect(self.close)
        layout.addWidget(self.buttons)

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(t["device_parameters"])
        self.table.setHorizontalHeaderLabels([t["parameter"], t["value"]])
        self.buttons.button(QDialogButtonBox.Close).setText(t["dialog_close"])

    def sync_from(self, source: QTableWidget) -> None:
        self.table.setRowCount(source.rowCount())
        for row in range(source.rowCount()):
            for column in range(source.columnCount()):
                item = source.item(row, column)
                self.table.setItem(
                    row,
                    column,
                    QTableWidgetItem(item.text() if item is not None else ""),
                )


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
        self.task_coordinator = DeviceTaskCoordinator()
        self.language = "zh"
        self.layout_manager = WindowLayoutManager()
        if not self.layout_manager.settings.value(
            "ui/compact_main_window_v1", False, type=bool
        ):
            # Discard only the obsolete oversized main-window geometry once.
            self.layout_manager.settings.remove("windows/main/geometry")
            self.layout_manager.settings.setValue(
                "ui/compact_main_window_v1", True
            )
        self.scale_manager: UiScaleManager | None = None
        self.busy = False
        self.snapshot: DeviceSnapshot | None = None
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
        self.connection_loss_notified = False
        self.notifier = NotificationService(self, lambda: self.language)
        self.auto_lock_controller = AutoLockController(self)
        self.falc_controller = FalcController(self)
        self.laser_controller = LaserController(self)
        self.scan_lock_controller = ScanLockController(self)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(500)
        self.refresh_timer.timeout.connect(self.refresh_snapshot)
        self._refresh_tick = 0

        self.future_poll_timer = QTimer(self)
        self.future_poll_timer.setInterval(50)
        self.future_poll_timer.timeout.connect(self._poll_future)

        self._build_ui()
        self._configure_combo_boxes()
        self._apply_module_precisions()
        self._update_all_precision_buttons()
        self._apply_base_style()
        self._configure_ui_scaling()
        self._apply_texts()
        self._populate_environment_hints()
        self._load_connection_settings()
        self._set_busy(False)

    def _build_ui(self) -> None:
        central = QWidget(self)
        central.setObjectName("appRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("hero")
        header_layout = QHBoxLayout(hero)
        header_layout.setContentsMargins(22, 14, 22, 14)
        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(1)
        self.hero_eyebrow = QLabel("TOPTICA · DLC PRO CONTROL")
        self.hero_eyebrow.setObjectName("heroEyebrow")
        self.hero_title = QLabel()
        self.hero_title.setObjectName("heroTitle")
        self.hero_subtitle = QLabel()
        self.hero_subtitle.setObjectName("heroSubtitle")
        heading_layout.addWidget(self.hero_eyebrow)
        heading_layout.addWidget(self.hero_title)
        heading_layout.addWidget(self.hero_subtitle)
        header_layout.addLayout(heading_layout)
        header_layout.addStretch(1)
        self.language_label = QLabel()
        self.language_label.setObjectName("heroSubtitle")
        self.language_combo = SafeComboBox()
        self.language_combo.addItem("中文", "zh")
        self.language_combo.addItem("English", "en")
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        header_layout.addWidget(self.language_label, 0, Qt.AlignVCenter)
        header_layout.addWidget(self.language_combo, 0, Qt.AlignVCenter)
        self.ui_scale_label = QLabel()
        self.ui_scale_label.setObjectName("heroSubtitle")
        self.ui_scale_combo = SafeComboBox()
        for label, scale in SCALE_OPTIONS:
            self.ui_scale_combo.addItem(label, scale)
        self.ui_scale_combo.currentIndexChanged.connect(self._on_ui_scale_changed)
        header_layout.addWidget(self.ui_scale_label, 0, Qt.AlignVCenter)
        header_layout.addWidget(self.ui_scale_combo, 0, Qt.AlignVCenter)
        self.status_label = QLabel()
        self.status_label.setObjectName("StatusBadge")
        self.status_label.setProperty("preserveSingleLine", True)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        header_layout.addWidget(self.status_label, 0, Qt.AlignVCenter)
        root.addWidget(hero)

        self.connection_group = self._build_connection_group()
        self.connection_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        root.addWidget(self.connection_group)

        self.workspace_group = QGroupBox()
        workspace_layout = QVBoxLayout(self.workspace_group)
        workspace_layout.setContentsMargins(12, 12, 12, 12)
        workspace_layout.setSpacing(12)

        self.nav_layout = QGridLayout()
        self.nav_layout.setSpacing(10)
        self.laser_button = self._create_nav_button(self._open_laser_window)
        self.falc_button = self._create_nav_button(self._open_falc_window)
        self.daq_scan_control_button = self._create_nav_button(
            self._open_daq_scan_control
        )
        self.daq_auto_lock_button = self._create_nav_button(
            self._open_daq_auto_lock
        )
        self.daq_button = self._create_nav_button(self._open_daq_window)
        self.nav_buttons = (
            self.laser_button,
            self.falc_button,
            self.daq_scan_control_button,
            self.daq_auto_lock_button,
            self.daq_button,
        )
        self._nav_columns = 0
        self._reflow_navigation()
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
        self.falc_window = FalcProWindow(self, self.falc_controller)
        self.falc_controller.bind_window(self.falc_window)
        self.scan_lock_page = self._build_scan_lock_page()
        self.scan_lock_window = ScanLockWindow(self.scan_lock_page)
        self.auto_lock_window = AutoLockWindow(self, self.auto_lock_controller)
        self.auto_lock_controller.bind_window(self.auto_lock_window)
        self.daq_window: DaqMainWindow | None = None

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
        self.command_port_label = QLabel()
        self.command_port_spin = SafeSpinBox()
        self.command_port_spin.setRange(0, 65535)
        self.command_port_spin.setValue(1998)
        self.monitoring_port_label = QLabel()
        self.monitoring_port_spin = SafeSpinBox()
        self.monitoring_port_spin.setRange(0, 65535)
        self.monitoring_port_spin.setValue(1999)
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
        self.refresh_button.clicked.connect(self.refresh_full_snapshot)

        self.serial_ports_info = QTextEdit()
        self.serial_ports_info.setReadOnly(True)
        self.network_info = QTextEdit()
        self.network_info.setReadOnly(True)
        for info in (self.network_info, self.serial_ports_info):
            info.setMinimumHeight(105)
            info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.mode_label, 0, 0)
        layout.addWidget(self.mode_combo, 0, 1)
        layout.addWidget(self.host_label, 1, 0)
        layout.addWidget(self.host_edit, 1, 1, 1, 4)
        layout.addWidget(self.command_port_label, 2, 0)
        layout.addWidget(self.command_port_spin, 2, 1)
        layout.addWidget(self.monitoring_port_label, 2, 2)
        layout.addWidget(self.monitoring_port_spin, 2, 3)
        layout.addWidget(self.serial_port_label, 3, 0)
        layout.addWidget(self.serial_port_combo, 3, 1)
        layout.addWidget(self.baudrate_label, 3, 2)
        layout.addWidget(self.baudrate_spin, 3, 3)
        layout.addWidget(self.timeout_label, 4, 0)
        layout.addWidget(self.timeout_spin, 4, 1)
        layout.addWidget(self.connect_button, 4, 2)
        layout.addWidget(self.disconnect_button, 4, 3)
        layout.addWidget(self.refresh_button, 4, 4)
        return box

    def _build_overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        self.parameter_group = QFrame()
        self.parameter_group.setObjectName("OverviewCard")
        self.parameter_group.setMinimumHeight(168)
        self.parameter_group.setMaximumHeight(230)
        self.parameter_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        group_layout = QVBoxLayout(self.parameter_group)
        group_layout.setContentsMargins(18, 16, 18, 16)
        group_layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(2)
        self.overview_title = QLabel()
        self.overview_title.setObjectName("OverviewTitle")
        self.overview_subtitle = QLabel()
        self.overview_subtitle.setObjectName("OverviewSubtitle")
        heading.addWidget(self.overview_title)
        heading.addWidget(self.overview_subtitle)
        header.addLayout(heading, 1)
        self.parameter_details_button = QPushButton()
        self.parameter_details_button.setObjectName("ParameterDetailsButton")
        self.parameter_details_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.parameter_details_button.clicked.connect(self._open_device_parameters)
        header.addWidget(self.parameter_details_button, 0, Qt.AlignVCenter)
        group_layout.addLayout(header)

        self.parameter_table = QTableWidget(0, 2)
        self.parameter_table.setObjectName("ParameterSummaryTable")
        self.parameter_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.parameter_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.parameter_table.horizontalHeader().setStretchLastSection(True)
        self.parameter_table.verticalHeader().setVisible(False)
        self.parameter_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.parameter_table.setSelectionMode(QTableWidget.NoSelection)
        self.parameter_table.setMinimumHeight(0)
        self.parameter_table.cellDoubleClicked.connect(
            lambda _row, _column: self._open_device_parameters()
        )
        group_layout.addWidget(self.parameter_table)
        self.parameter_empty_label = QLabel()
        self.parameter_empty_label.setObjectName("ParameterEmptyState")
        self.parameter_empty_label.setAlignment(Qt.AlignCenter)
        self.parameter_empty_label.setMinimumHeight(62)
        group_layout.addWidget(self.parameter_empty_label, 1)
        self.device_parameters_dialog = DeviceParametersDialog(self)
        self._sync_parameter_overview_state()
        layout.addWidget(self.parameter_group, 0)

        self.runtime_log_group = QGroupBox()
        log_layout = QHBoxLayout(self.runtime_log_group)
        log_layout.setContentsMargins(12, 14, 12, 12)
        log_layout.setSpacing(12)
        log_layout.addWidget(self.network_info, 1)
        log_layout.addWidget(self.serial_ports_info, 1)
        layout.addWidget(self.runtime_log_group, 1)
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

    def _reflow_navigation(self) -> None:
        if not hasattr(self, "nav_buttons"):
            return
        width = max(self.width(), 1)
        desired_columns = 1 if width < 520 else 2 if width < 900 else len(self.nav_buttons)
        columns = min(len(self.nav_buttons), desired_columns)
        if columns == self._nav_columns:
            return
        for button in self.nav_buttons:
            self.nav_layout.removeWidget(button)
        for index, button in enumerate(self.nav_buttons):
            self.nav_layout.addWidget(button, index // columns, index % columns)
        for column in range(columns):
            self.nav_layout.setColumnStretch(column, 1)
        self._nav_columns = columns

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reflow_navigation()

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

    def sync_precision_target_buttons(self, module: str) -> None:
        self._sync_precision_target_buttons(module)

    def _open_laser_window(self) -> None:
        self._show_auxiliary_window(self.laser_window)

    def _open_falc_window(self) -> None:
        self._show_auxiliary_window(self.falc_window)

    def _open_scan_lock_window(self) -> None:
        self._show_auxiliary_window(self.scan_lock_window)

    def _open_auto_lock_window(self) -> None:
        self._show_auxiliary_window(self.auto_lock_window)

    def _ensure_daq_window(self) -> DaqMainWindow:
        if self.daq_window is None:
            self.daq_window = DaqMainWindow(
                snapshot_provider=lambda: self.snapshot,
                dlc_service=self.service,
                snapshot_consumer=self._on_snapshot_updated,
                falc_window_opener=self.show_falc_window,
            )
            self.daq_window.destroyed.connect(
                lambda: setattr(self, "daq_window", None)
            )
            # Entering ADC opens only the acquisition console.  The combined
            # auto-lock/scope workspace is opened explicitly from inside it.
            self.daq_window.auto_lock_workspace.hide()
        return self.daq_window

    def _open_daq_window(self) -> None:
        daq_window = self._ensure_daq_window()
        daq_window.showNormal()
        daq_window.show()
        schedule_window_fit(daq_window)
        daq_window.raise_()
        daq_window.activateWindow()
        self.refresh_visible_snapshot()

    def _open_daq_scan_control(self) -> None:
        self._ensure_daq_window().show_scan_control()
        self.refresh_visible_snapshot()

    def _open_daq_auto_lock(self) -> None:
        self._ensure_daq_window().show_peak_lock()
        self.refresh_visible_snapshot()

    def _open_device_parameters(self) -> None:
        self.device_parameters_dialog.sync_from(self.parameter_table)
        self.device_parameters_dialog.apply_texts(self.language)
        self.layout_manager.prepare_show(self.device_parameters_dialog)
        self.device_parameters_dialog.showNormal()
        self.device_parameters_dialog.show()
        self.device_parameters_dialog.raise_()
        self.device_parameters_dialog.activateWindow()

    def _sync_parameter_overview_state(self) -> None:
        has_parameters = self.parameter_table.rowCount() > 0
        self.parameter_table.setVisible(has_parameters)
        self.parameter_empty_label.setVisible(not has_parameters)

    def _show_auxiliary_window(self, window: QWidget) -> None:
        self.layout_manager.prepare_show(window)
        window.showNormal()
        window.show()
        window.raise_()
        window.activateWindow()
        self.refresh_visible_snapshot()

    def _apply_base_style(self) -> None:
        stylesheet = """
            QWidget {
                background: #2d2d2d;
                color: #f0f0f0;
            }
            QLabel {
                background: transparent;
            }
            QGroupBox {
                border: 1px solid #4e4e4e;
                border-radius: 6px;
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
                border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background: #5e5e5e;
            }
            QPushButton:pressed {
                background: #4a4a4a;
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
                font-weight: 700;
                color: #f5f5f5;
            }
            QLabel#SectionTitle {
                font-weight: 700;
                color: #f2f2f2;
            }
            QFrame#LaserPanel {
                background: #3a3a3a;
                border: 1px solid #5b5b5b;
                border-radius: 6px;
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

            /* Unified light card theme shared with the DAQ secondary UI. */
            QWidget {
                background: #f3f6fa;
                color: #172033;
                font-family: "Microsoft YaHei UI", "Segoe UI";
            }
            QLabel {
                background: transparent;
                color: #25324a;
            }
            QGroupBox {
                border: 1px solid #dce3ed;
                border-radius: 10px;
                background: #ffffff;
                color: #25324a;
            }
            QLineEdit, QComboBox, QTextEdit, QTableWidget,
            QSpinBox, QDoubleSpinBox {
                background: #ffffff;
                border: 1px solid #cfd8e6;
                border-radius: 7px;
                color: #172033;
                selection-background-color: #2f6fcb;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus,
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #4b82cf;
            }
            QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled,
            QSpinBox:disabled, QDoubleSpinBox:disabled {
                background: #f0f2f5;
                color: #8993a4;
                border-color: #e0e5ec;
            }
            QScrollArea, QScrollArea > QWidget > QWidget {
                background: #f3f6fa;
            }
            QTableWidget { gridline-color: #dce3ed; }
            QPushButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                color: #25324a;
            }
            QPushButton:hover {
                background: #f6f8fb;
                border-color: #9eacbf;
            }
            QPushButton:pressed { background: #edf1f6; }
            QPushButton:disabled {
                background: #f0f2f5;
                border-color: #e0e5ec;
                color: #a3adbb;
            }
            QPushButton#PrecisionButton:checked {
                background: #e8f7ef;
                border-color: #75b391;
                color: #137044;
            }
            QPushButton#StepTargetButton {
                background: #ffffff;
                border-color: #cbd5e1;
                color: #25324a;
            }
            QPushButton#StepTargetButton:checked {
                background: #fff7e8;
                border-color: #d8af68;
                color: #8a5a12;
            }
            QPushButton#ParameterHelpButton {
                background: #ffffff;
                border-color: #cbd5e1;
                color: #3563a9;
            }
            QLabel#StatusBadge {
                background: #e8f7ef;
                border: 1px solid #bce6ce;
                color: #137044;
            }
            QFrame#OverviewCard {
                background: #ffffff;
                border: 1px solid #dce3ed;
                border-radius: 10px;
            }
            QLabel#OverviewTitle {
                color: #102f57;
                font-size: 18px;
                font-weight: 700;
            }
            QLabel#OverviewSubtitle { color: #69758a; }
            QLabel#ParameterEmptyState {
                background: #f8fafc;
                border: 1px dashed #cbd5e1;
                border-radius: 8px;
                color: #78869a;
                padding: 10px;
            }
            QTableWidget#ParameterSummaryTable {
                background: #f8fafc;
                border: 1px solid #dce3ed;
                border-radius: 8px;
            }
            QPushButton#ParameterDetailsButton {
                background: #e9f2ff;
                border-color: #bdd5fa;
                color: #195ca8;
                min-width: 96px;
            }
            QLabel#PageTitle {
                color: #102f57;
                font-size: 22px;
            }
            QLabel#SectionTitle { color: #25324a; }
            QFrame#LaserPanel {
                background: #ffffff;
                border: 1px solid #dce3ed;
                border-radius: 10px;
            }
            QLabel#ReadValue {
                background: #f8fafc;
                border: 1px solid #d7dee8;
                color: #172033;
            }
            QLabel#SubtleHint, QLabel#PlaceholderBody { color: #69758a; }
            QFrame#Divider { color: #dce3ed; }
            QPushButton#ToggleButton {
                min-width: 104px;
                max-width: 104px;
                min-height: 36px;
                max-height: 36px;
                padding: 0 10px;
                background: #ffffff;
                border: 1px solid #b9c7da;
                color: #36516f;
            }
            QPushButton#ToggleButton:checked {
                background: #e8f7ef;
                border-color: #75b391;
                color: #137044;
            }
            QPushButton#ToggleButton:disabled {
                background: #eef2f7;
                border-color: #d7dee9;
                color: #8794a8;
            }
            QDialog#CompactMessageDialog {
                background: #ffffff;
            }
            QDialog#CompactMessageDialog QLabel#qt_msgbox_label {
                background: transparent;
                color: #172033;
            }
            QPushButton#PrimaryDialogButton {
                background: #286bc1;
                border-color: #286bc1;
                color: #ffffff;
            }
            """
        # Apply the exact secondary-window palette last so the main console
        # uses the same blue hero, light canvas, cards and status colors.
        stylesheet += DAQ_APP_STYLE
        stylesheet += """
            QMessageBox QLabel {
                background: transparent;
            }
            QMessageBox QPushButton {
                min-width: 64px;
                min-height: 28px;
                padding: 3px 10px;
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
            self.scale_manager = UiScaleManager(app, app.styleSheet(), self.layout_manager.settings)
        self.scale_manager.register_windows(
            (
                self,
                self.laser_window,
                self.falc_window,
                self.scan_lock_window,
                self.auto_lock_window,
                self.auto_lock_window.config_window,
                self.auto_lock_window.waveform_window,
                self.auto_lock_window.log_window,
                self.device_parameters_dialog,
            )
        )
        self.layout_manager.register_windows(
            (
                (self, "main", 920, 680),
                (self.laser_window, "laser", 860, 900),
                (self.falc_window, "falc", 760, 760),
                (self.scan_lock_window, "scan-lock", 980, 900),
                (self.auto_lock_window, "auto-lock", 1080, 680),
                (self.auto_lock_window.config_window, "auto-lock-config", 720, 620),
                (self.auto_lock_window.waveform_window, "auto-lock-waveform", 1040, 700),
                (self.auto_lock_window.log_window, "auto-lock-log", 920, 620),
                (self.device_parameters_dialog, "device-parameters", 720, 520),
            )
        )
        selected = self.scale_manager.selected_scale
        index = next(
            (i for i, (_label, value) in enumerate(SCALE_OPTIONS) if value == selected),
            0,
        )
        self.ui_scale_combo.blockSignals(True)
        self.ui_scale_combo.setCurrentIndex(index)
        self.ui_scale_combo.blockSignals(False)
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
        self.hero_title.setText(t["console_title"])
        self.hero_subtitle.setText(t["console_subtitle"])

        self.connection_group.setTitle(t["connection"])
        self.workspace_group.setTitle(t["workspace"])
        self.runtime_log_group.setTitle(t["runtime_log"])
        self.overview_title.setText(t["device_overview"])
        self.overview_subtitle.setText(t["device_overview_hint"])
        self.parameter_empty_label.setText(t["device_parameters_empty"])

        self.mode_label.setText(t["mode"])
        self.mode_combo.setItemText(0, t["network"])
        self.mode_combo.setItemText(1, t["serial"])
        self.host_label.setText(t["host"])
        self.command_port_label.setText(t["command_port"])
        self.monitoring_port_label.setText(t["monitoring_port"])
        self.serial_port_label.setText(t["serial_port"])
        self.baudrate_label.setText(t["baudrate"])
        self.timeout_label.setText(t["timeout"])
        self.connect_button.setText(t["connect"])
        self.disconnect_button.setText(t["disconnect"])
        self.refresh_button.setText(t["refresh"])
        self.parameter_table.setHorizontalHeaderLabels([t["parameter"], t["value"]])
        self.parameter_details_button.setText(t["view_all_parameters"])
        self.device_parameters_dialog.apply_texts(self.language)

        self.laser_button.setText(t["laser"])
        self.falc_button.setText(t["falc"])
        self.daq_scan_control_button.setText(t["frequency_scan_control"])
        self.daq_auto_lock_button.setText(t["auto_lock"])
        self.daq_button.setText(t["data_acquisition"])
        self.auto_lock_controller.apply_texts()
        self.falc_window.apply_texts(self.language)
        if self.snapshot is None:
            self.auto_lock_window.reset_state(self.language)

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
        # Visual state comes from the shared ToggleButton stylesheet.  Inline
        # dark colors previously overrode the light theme and produced black bars.
        button.setStyleSheet("")
        button.style().unpolish(button)
        button.style().polish(button)
        button.blockSignals(False)

    def update_toggle_button(self, button: QPushButton, enabled: bool) -> None:
        self._update_toggle_button(button, enabled)

    def _set_connection_mode(self, mode: str) -> None:
        is_network = mode == "network"
        self.host_edit.setEnabled(is_network)
        self.command_port_spin.setEnabled(is_network)
        self.monitoring_port_spin.setEnabled(is_network)
        self.serial_port_combo.setEnabled(not is_network)
        self.baudrate_spin.setEnabled(not is_network)

    def _load_connection_settings(self) -> None:
        settings = self.layout_manager.settings
        mode = str(settings.value("dlcpro/mode", "network"))
        mode_index = self.mode_combo.findData(mode)
        self.mode_combo.setCurrentIndex(max(0, mode_index))
        self.host_edit.setText(
            str(settings.value("dlcpro/network_target", "169.254.18.52"))
        )
        self.command_port_spin.setValue(
            int(settings.value("dlcpro/command_line_port", 1998))
        )
        self.monitoring_port_spin.setValue(
            int(settings.value("dlcpro/monitoring_line_port", 1999))
        )
        self.baudrate_spin.setValue(int(settings.value("dlcpro/baudrate", 115200)))
        self.timeout_spin.setValue(int(settings.value("dlcpro/timeout", 5)))
        serial_target = str(settings.value("dlcpro/serial_target", ""))
        if serial_target:
            serial_index = self.serial_port_combo.findData(serial_target)
            if serial_index < 0:
                serial_index = self.serial_port_combo.findText(serial_target)
            if serial_index >= 0:
                self.serial_port_combo.setCurrentIndex(serial_index)
        self._set_connection_mode(str(self.mode_combo.currentData()))

    def _save_connection_settings(self) -> None:
        settings = self.layout_manager.settings
        settings.setValue("dlcpro/mode", self.mode_combo.currentData())
        settings.setValue("dlcpro/network_target", self.host_edit.text().strip())
        settings.setValue("dlcpro/command_line_port", self.command_port_spin.value())
        settings.setValue(
            "dlcpro/monitoring_line_port", self.monitoring_port_spin.value()
        )
        settings.setValue(
            "dlcpro/serial_target", self.serial_port_combo.currentText().strip()
        )
        settings.setValue("dlcpro/baudrate", self.baudrate_spin.value())
        settings.setValue("dlcpro/timeout", self.timeout_spin.value())
        settings.sync()

    def _set_busy(self, busy: bool, freeze_controls: bool = True) -> None:
        laser_scroll = self._laser_scroll_value()
        scan_lock_scroll = self._scan_lock_scroll_value()
        self.busy = busy and freeze_controls
        t = TEXT[self.language]
        if busy and freeze_controls:
            self.status_label.setText(t["busy"])
        else:
            self.status_label.setText(t["connected"] if self.service.is_connected else t["disconnected"])
        auto_lock_running = self.auto_lock_controller.is_running
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

    def _run_task(
        self,
        fn,
        on_success,
        task_kind: str = "action",
        coalesce_key: str | None = None,
    ) -> bool:
        accepted = self.task_coordinator.submit(
            fn,
            lambda ok, result, kind: self._handle_task_done(on_success, ok, result, kind),
            kind=task_kind,
            coalesce_key=coalesce_key,
        )
        if not accepted:
            return False
        if task_kind != "poll":
            self._set_busy(True)
        if not self.future_poll_timer.isActive():
            self.future_poll_timer.start()
        return True

    def submit_device_task(self, fn, on_success=None, *, coalesce_key: str | None = None) -> bool:
        """Public controller entry point for serialized SDK operations."""

        return self._run_task(
            fn,
            on_success or self._on_snapshot_updated,
            coalesce_key=coalesce_key,
        )

    def publish_snapshot(self, snapshot: DeviceSnapshot) -> None:
        self._on_snapshot_updated(snapshot)

    def set_operation_busy(self, busy: bool) -> None:
        self._set_busy(busy)

    def set_background_refresh_enabled(self, enabled: bool) -> None:
        if enabled and self.service.is_connected:
            if not self.refresh_timer.isActive():
                self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    def show_falc_window(self) -> None:
        self._open_falc_window()

    def _poll_future(self) -> None:
        self.task_coordinator.poll_completed()
        if not self.task_coordinator.has_work:
            self.future_poll_timer.stop()

    def _handle_task_done(self, on_success, ok: bool, result: object, task_kind: str) -> None:
        if ok:
            self.connection_loss_notified = False
            if on_success is not None:
                on_success(result)
            self._set_busy(self.task_coordinator.has_user_work)
            return
        if isinstance(result, Exception) and self._handle_connection_failure(result, task_kind):
            return
        if task_kind == "connect":
            # Do not preserve stale readbacks or a green connection badge when
            # the initial device snapshot was rejected after opening transport.
            self._reset_after_disconnect(silent=True)
        self._set_busy(self.task_coordinator.has_user_work)
        if self.auto_lock_controller.is_running:
            self.auto_lock_controller.handle_task_failure(result)
        message = self.service.format_error(result) if isinstance(result, Exception) else str(result)
        self._show_compact_message(TEXT[self.language]["error_title"], message, QStyle.SP_MessageBoxCritical)

    def _handle_connection_failure(self, exc: Exception, task_kind: str) -> bool:
        if task_kind != "poll":
            return False
        self.task_coordinator.stop_polling_and_clear()
        self._reset_after_disconnect(silent=True)
        if self.connection_loss_notified:
            return True
        self.connection_loss_notified = True
        t = TEXT[self.language]
        self._show_compact_message(
            t["connection_lost_title"],
            self.service.format_error(exc),
            QStyle.SP_MessageBoxCritical,
        )
        return True

    def _show_compact_message(
        self, title: str, message: str, icon: QStyle.StandardPixmap
    ) -> None:
        CompactMessageDialog(
            self,
            title,
            message,
            accept_text=TEXT[self.language]["dialog_ok"],
            icon=icon,
        ).exec()

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

    def update_all_precision_buttons(self) -> None:
        self._update_all_precision_buttons()

    def _format_value_with_unit(self, value: float, decimals: int, unit: str) -> str:
        return f"{value:.{decimals}f} {unit}"

    def format_value_with_unit(self, value: float, decimals: int, unit: str) -> str:
        return self._format_value_with_unit(value, decimals, unit)

    def _unit_only_text(self, unit: str) -> str:
        return unit

    def unit_only_text(self, unit: str) -> str:
        return self._unit_only_text(unit)

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


    def connect_device(self) -> None:
        mode = self.mode_combo.currentData()
        if mode == "network":
            target = self.host_edit.text().strip()
        else:
            target = str(self.serial_port_combo.currentData() or "").strip()
        if not target:
            self._show_compact_message(
                TEXT[self.language]["warning_title"],
                "Please enter a connection target / 请输入连接目标",
                QStyle.SP_MessageBoxWarning,
            )
            return
        settings = ConnectionSettings(
            mode=mode,
            target=target,
            baudrate=self.baudrate_spin.value(),
            timeout=self.timeout_spin.value(),
            command_line_port=self.command_port_spin.value(),
            monitoring_line_port=self.monitoring_port_spin.value(),
        )
        self._save_connection_settings()
        self.task_coordinator.resume_polling()
        self._run_task(
            lambda: self.service.connect(settings),
            self._on_snapshot_updated,
            task_kind="connect",
        )

    def _reset_after_disconnect(self, silent: bool = False) -> None:
        self.refresh_timer.stop()
        self.laser_controller.current_apply_timer.stop()
        self.task_coordinator.stop_polling_and_clear()
        try:
            self.service.disconnect()
        except Exception as exc:  # noqa: BLE001
            if not silent:
                self._show_compact_message(
                    TEXT[self.language]["error_title"],
                    self.service.format_error(exc),
                    QStyle.SP_MessageBoxCritical,
                )
            return
        self.auto_lock_controller.handle_disconnect()
        self.snapshot = None
        self.last_device_current_set = None
        self.parameter_table.setRowCount(0)
        self._sync_parameter_overview_state()
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
        self.falc_window.reset_state(self.language)
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
        self._refresh_tick += 1
        if self._refresh_tick % 10 == 0:
            request = SnapshotRequest.full()
        elif self._refresh_tick % 2 == 0:
            request = self._visible_snapshot_request()
        else:
            request = SnapshotRequest.core()
        self._run_task(
            lambda request=request: self.service.read_snapshot(request),
            self._on_snapshot_updated,
            task_kind="poll",
        )

    def refresh_visible_snapshot(self) -> None:
        if not self.service.is_connected or self.busy:
            return
        request = self._visible_snapshot_request()
        self._run_task(
            lambda request=request: self.service.read_snapshot(request),
            self._on_snapshot_updated,
            task_kind="poll",
        )

    def refresh_full_snapshot(self) -> None:
        if not self.service.is_connected or self.busy:
            return
        self._run_task(
            lambda: self.service.read_snapshot(SnapshotRequest.full()),
            self._on_snapshot_updated,
        )

    def _visible_snapshot_request(self) -> SnapshotRequest:
        sections = {SnapshotSection.CORE}
        if self.laser_window.isVisible():
            sections.add(SnapshotSection.LASER)
        if self.scan_lock_window.isVisible():
            sections.add(SnapshotSection.SCAN_LOCK)
        if self.auto_lock_window.isVisible():
            sections.update({SnapshotSection.SCAN_LOCK, SnapshotSection.FALC})
        if self.falc_window.isVisible():
            sections.add(SnapshotSection.FALC)
        if self.daq_window is not None and (
            self.daq_window.isVisible()
            or self.daq_window.scan_control_window.isVisible()
            or self.daq_window.auto_lock_workspace.isVisible()
        ):
            sections.add(SnapshotSection.SCAN_LOCK)
        return SnapshotRequest(frozenset(sections))

    def _on_snapshot_updated(self, snapshot: DeviceSnapshot) -> None:
        self.snapshot = snapshot
        self._render_snapshot(snapshot)
        if (
            not self.auto_lock_controller.is_running
            and not self.refresh_timer.isActive()
        ):
            self.refresh_timer.start()

    def _render_snapshot(self, snapshot: DeviceSnapshot) -> None:
        scroll_positions = self._capture_scroll_positions()
        self.laser_controller.render_snapshot(snapshot)
        self.scan_lock_controller.render_snapshot(snapshot)
        self.auto_lock_controller.render_snapshot(snapshot)
        self.falc_window.render_snapshot(snapshot)
        self._sync_parameter_overview_state()
        if self.device_parameters_dialog.isVisible():
            self.device_parameters_dialog.sync_from(self.parameter_table)
        self._restore_scroll_positions(scroll_positions)

    def _capture_scroll_positions(self) -> list[tuple[QScrollArea, int, int]]:
        positions: list[tuple[QScrollArea, int, int]] = []
        seen: set[QScrollArea] = set()
        for root in (
            self,
            self.laser_window,
            self.falc_window,
            self.scan_lock_window,
            self.auto_lock_window,
        ):
            for scroll in root.findChildren(QScrollArea):
                if scroll in seen:
                    continue
                seen.add(scroll)
                positions.append(
                    (
                        scroll,
                        scroll.horizontalScrollBar().value(),
                        scroll.verticalScrollBar().value(),
                    )
                )
        return positions

    @staticmethod
    def _restore_scroll_positions(positions: list[tuple[QScrollArea, int, int]]) -> None:
        for scroll, horizontal, vertical in positions:
            scroll.horizontalScrollBar().setValue(horizontal)
            scroll.verticalScrollBar().setValue(vertical)

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
        confirmed = CompactMessageDialog(
            self,
            t["exit_confirm_title"],
            t["exit_confirm_body"],
            accept_text=t["dialog_confirm"],
            reject_text=t["dialog_cancel"],
            icon=QStyle.SP_MessageBoxQuestion,
        ).exec()
        if confirmed != QDialog.Accepted:
            event.ignore()
            return
        self.layout_manager.save_all()
        self.refresh_timer.stop()
        self.future_poll_timer.stop()
        self.laser_controller.shutdown()
        for window in (
            self.laser_window,
            self.falc_window,
            self.scan_lock_window,
            self.auto_lock_window,
        ):
            window.request_shutdown()
            window.close()
        if self.daq_window is not None:
            self.daq_window.close()
        self._reset_after_disconnect(silent=True)
        self.task_coordinator.shutdown()
        super().closeEvent(event)


def create_safety_notice(parent: QWidget) -> CompactMessageDialog:
    """Build a compact, word-wrapped safety notice without clipping text."""
    t = TEXT[parent.language]
    return CompactMessageDialog(
        parent,
        t["safety_title"],
        t["safety_text"],
        accept_text=t["dialog_ok"],
        icon=QStyle.SP_MessageBoxInformation,
    )


def main() -> int:
    open_daq_on_start = "--open-adc" in sys.argv
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except AttributeError:
        pass
    app = QApplication(sys.argv)
    window = MainWindow()
    window.layout_manager.prepare_show(window)
    window.showNormal()
    window.show()
    create_safety_notice(window).exec()
    if open_daq_on_start:
        window._open_daq_window()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
