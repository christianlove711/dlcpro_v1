from __future__ import annotations

import sys
from concurrent.futures import Future, ThreadPoolExecutor

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QApplication,
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
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dlcpro_service import ConnectionSettings, DeviceSnapshot, DlcProService
from ui_text import ARC_SIGNAL_OPTIONS, SCAN_OUTPUT_OPTIONS, SCAN_SHAPE_OPTIONS, TEXT
from controllers import LaserController
from windows.laser_window import LaserWindow, build_laser_page

FAST_CURRENT_ADJUST_CONFIRM_THRESHOLD_MA = 10.0
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
        self.last_device_current_set: float | None = None
        self.cc_precision_step = 0.1
        self.tc_precision_step = 0.001
        self.pc_precision_step = 0.000001
        self.sc_precision_step = 0.01
        self.module_precision_defaults: dict[str, QDoubleSpinBox] = {}
        self.module_precision_selected: dict[str, QDoubleSpinBox] = {}
        self.module_precision_target_buttons: dict[str, list[QPushButton]] = {
            "cc": [],
            "tc": [],
            "pc": [],
            "sc": [],
        }
        self.connection_loss_notified = False
        self.laser_controller = LaserController(self)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(2000)
        self.refresh_timer.timeout.connect(self.refresh_snapshot)

        self.future_poll_timer = QTimer(self)
        self.future_poll_timer.setInterval(50)
        self.future_poll_timer.timeout.connect(self._poll_future)

        self.current_apply_timer = QTimer(self)
        self.current_apply_timer.setSingleShot(True)
        self.current_apply_timer.setInterval(AUTO_APPLY_DEBOUNCE_MS)
        self.current_apply_timer.timeout.connect(self._apply_current_if_needed)

        self._build_ui()
        self._apply_module_precisions()
        self._update_all_precision_buttons()
        self._apply_base_style()
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
        self.language_combo = QComboBox()
        self.language_combo.addItem("中文", "zh")
        self.language_combo.addItem("English", "en")
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        header_layout.addWidget(self.language_label)
        header_layout.addWidget(self.language_combo)
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
        self.scan_lock_button = self._create_nav_button(lambda: self.page_stack.setCurrentIndex(1))
        self.relock_button = self._create_nav_button(lambda: self.page_stack.setCurrentIndex(2))
        self.stabilization_button = self._create_nav_button(lambda: self.page_stack.setCurrentIndex(3))
        for button in (
            self.overview_button,
            self.laser_button,
            self.scan_lock_button,
            self.relock_button,
            self.stabilization_button,
        ):
            self.nav_layout.addWidget(button)
        workspace_layout.addLayout(self.nav_layout)

        self.page_stack = QStackedWidget()
        self.page_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.overview_page = self._build_overview_page()
        self.laser_page = self._build_laser_page()
        self.scan_lock_page = self._build_placeholder_page()
        self.relock_page = self._build_placeholder_page()
        self.stabilization_page = self._build_placeholder_page()

        self.page_stack.addWidget(self.overview_page)
        self.page_stack.addWidget(self.scan_lock_page)
        self.page_stack.addWidget(self.relock_page)
        self.page_stack.addWidget(self.stabilization_page)
        workspace_layout.addWidget(self.page_stack, 1)
        root.addWidget(self.workspace_group, 1)
        root.setStretch(0, 0)
        root.setStretch(1, 0)
        root.setStretch(2, 1)

        self.laser_window = LaserWindow(self.laser_page)

    def _build_connection_group(self) -> QGroupBox:
        box = QGroupBox()
        layout = QGridLayout(box)

        self.mode_label = QLabel()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("", "network")
        self.mode_combo.addItem("", "serial")
        self.mode_combo.currentIndexChanged.connect(
            lambda: self._set_connection_mode(self.mode_combo.currentData())
        )

        self.host_label = QLabel()
        self.host_edit = QLineEdit("169.254.215.1")
        self.serial_port_label = QLabel()
        self.serial_port_combo = QComboBox()
        self.baudrate_label = QLabel()
        self.baudrate_spin = QSpinBox()
        self.baudrate_spin.setRange(1200, 10000000)
        self.baudrate_spin.setValue(115200)
        self.timeout_label = QLabel()
        self.timeout_spin = QSpinBox()
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

    def _create_target_row(self, module: str, spinbox: QDoubleSpinBox) -> QWidget:
        # 面板层只负责创建控件，目标绑定规则仍由主窗口统一管理。
        from windows.laser_window import _create_target_row

        return _create_target_row(self, module, spinbox)

    def _build_placeholder_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        title = QLabel()
        title.setObjectName("PageTitle")
        body = QLabel()
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignCenter)
        body.setObjectName("PlaceholderBody")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(body, alignment=Qt.AlignCenter)
        layout.addStretch(1)
        page._title_label = title
        page._body_label = body
        return page

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
        self.laser_window.raise_()
        self.laser_window.activateWindow()

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
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QTextEdit, QTableWidget {
                background: #4a4a4a;
                border: 1px solid #666;
                border-radius: 6px;
                padding: 6px 8px;
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
        if app is not None:
            app.setStyleSheet(stylesheet)
        else:
            self.setStyleSheet(stylesheet)

    def _apply_texts(self) -> None:
        t = TEXT[self.language]
        self.setWindowTitle(t["window_title"])
        self.language_label.setText(t["language"])
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
        self.scan_lock_button.setText(t["scan_lock"])
        self.relock_button.setText(t["relock"])
        self.stabilization_button.setText(t["stabilization"])
        self.scan_lock_page._title_label.setText(t["scan_lock"])
        self.relock_page._title_label.setText(t["relock"])
        self.stabilization_page._title_label.setText(t["stabilization"])
        self.scan_lock_page._body_label.setText(t["placeholder_body"])
        self.relock_page._body_label.setText(t["placeholder_body"])
        self.stabilization_page._body_label.setText(t["placeholder_body"])

        self.cc_status_label = t["cc_status"]
        self.laser_controller.apply_texts()

        self._populate_arc_signal_options()
        self._populate_tc_arc_signal_options()
        self._populate_pc_arc_signal_options()
        self._populate_sc_output_options()
        self._populate_sc_shape_options()
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
        self.serial_port_combo.addItems(serial_ports)

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

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        t = TEXT[self.language]
        self.status_label.setText(t["busy"] if busy else (t["connected"] if self.service.is_connected else t["disconnected"]))
        for widget in (self.connect_button, self.disconnect_button, self.refresh_button):
            widget.setEnabled(not busy)
        writable = not busy and self.service.is_connected
        for widget in (
            self.current_set_spin,
            self.current_clip_spin,
            self.feedforward_factor_spin,
            self.arc_signal_combo,
            self.arc_factor_spin,
            self.temp_set_spin,
            self.tc_arc_signal_combo,
            self.tc_arc_factor_spin,
            self.pc_voltage_set_spin,
            self.pc_slew_rate_spin,
            self.pc_arc_signal_combo,
            self.pc_arc_factor_spin,
            self.scan_amplitude_spin,
            self.scan_offset_spin,
            self.scan_output_combo,
            self.scan_frequency_spin,
            self.scan_shape_combo,
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
            self.pressure_comp_enable_button,
        ):
            widget.setEnabled(writable)
        for button in (*self.precision_buttons, *self.tc_precision_buttons, *self.pc_precision_buttons, *self.sc_precision_buttons):
            button.setEnabled(not busy)
        for module_buttons in self.module_precision_target_buttons.values():
            for button in module_buttons:
                button.setEnabled(not busy)

    def _run_task(self, fn, on_success, task_kind: str = "action") -> None:
        if self.busy:
            return
        self._set_busy(True)
        self.pending_success_handler = on_success
        self.pending_task_kind = task_kind
        self.pending_future = self.executor.submit(fn)
        self.future_poll_timer.start()

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
        self._set_busy(False)
        if ok:
            self.connection_loss_notified = False
            if on_success is not None:
                on_success(result)
            return
        if isinstance(result, Exception) and self._handle_connection_failure(result, task_kind):
            return
        message = self.service.format_error(result) if isinstance(result, Exception) else str(result)
        QMessageBox.critical(self, "Error", message)

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

    def _active_precision_target(self, module: str) -> QDoubleSpinBox:
        return self.module_precision_selected.get(module, self.module_precision_defaults[module])

    def _apply_step(self, spinbox: QDoubleSpinBox, step: float) -> None:
        spinbox.setSingleStep(step)

    def _apply_module_precisions(self) -> None:
        self.current_set_spin.setSingleStep(self.cc_precision_step)
        self.temp_set_spin.setSingleStep(self.tc_precision_step)
        self.pc_voltage_set_spin.setSingleStep(self.pc_precision_step)
        self.scan_amplitude_spin.setSingleStep(self.sc_precision_step)

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

    def _format_value_with_unit(self, value: float, decimals: int, unit: str) -> str:
        return f"{value:.{decimals}f} {unit}"

    def _unit_only_text(self, unit: str) -> str:
        return unit

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        return super().eventFilter(watched, event)

    def _on_current_set_changed(self) -> None:
        if self.current_set_programmatic_update:
            return
        self.current_set_dirty = True
        if self.service.is_connected:
            self.current_apply_timer.start()

    def _apply_current_if_needed(self) -> None:
        if not self.service.is_connected or not self.current_set_dirty or self.busy:
            return

        value = self.current_set_spin.value()
        current_value = self.last_device_current_set
        if (
            current_value is not None
            and abs(value - current_value) >= FAST_CURRENT_ADJUST_CONFIRM_THRESHOLD_MA
        ):
            t = TEXT[self.language]
            confirmed = QMessageBox.question(
                self,
                t["confirm_title"],
                t["confirm_apply_current"].format(current=current_value, value=value),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirmed != QMessageBox.Yes:
                self.current_set_programmatic_update = True
                self.current_set_spin.blockSignals(True)
                self.current_set_spin.setValue(current_value)
                self.current_set_spin.blockSignals(False)
                self.current_set_programmatic_update = False
                self.current_set_dirty = False
                return

        self.current_set_dirty = False
        self._run_task(lambda: self.service.set_current(value), self._on_snapshot_updated)

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
        self._confirm_and_run(
            TEXT[self.language]["set_temperature"],
            f"{current:.5f} {TEXT[self.language]['temperature_unit']}",
            f"{value:.5f} {TEXT[self.language]['temperature_unit']}",
            lambda: self.service.set_temp_set(value),
        )

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
        self._confirm_and_run(
            TEXT[self.language]["set_voltage"],
            f"{current:.6f} {TEXT[self.language]['voltage_unit']}",
            f"{value:.6f} {TEXT[self.language]['voltage_unit']}",
            lambda: self.service.set_pc_voltage_set(value),
        )

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

    def _on_cc_enable_toggled(self, checked: bool) -> None:
        if not self.service.is_connected or self.cc_programmatic_update:
            return
        self._run_task(lambda: self.service.set_cc_enabled(checked), self._on_snapshot_updated)

    def connect_device(self) -> None:
        mode = self.mode_combo.currentData()
        target = self.host_edit.text().strip() if mode == "network" else self.serial_port_combo.currentText().strip()
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
        try:
            self.service.disconnect()
        except Exception as exc:  # noqa: BLE001
            if not silent:
                QMessageBox.critical(self, "Error", self.service.format_error(exc))
            return
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
        self.pressure_comp_factor_spin.setValue(0.0)
        self.laser_controller.reset_readbacks()
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
        if not self.refresh_timer.isActive():
            self.refresh_timer.start()

    def _render_snapshot(self, snapshot: DeviceSnapshot) -> None:
        self.laser_controller.render_snapshot(snapshot)

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
        self.laser_window.close()
        self._reset_after_disconnect(silent=True)
        self.executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(980, 860)
    window.show()
    QMessageBox.information(
        window,
        TEXT["zh"]["safety_title"],
        f"{TEXT['zh']['safety_text']}\n\n{TEXT['en']['safety_text']}",
    )
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
