from __future__ import annotations

import sys
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
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
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dlcpro_service import ConnectionSettings, DeviceSnapshot, DlcProService
from ui_text import ARC_SIGNAL_OPTIONS, PARAMETER_LABELS, TEXT

FAST_CURRENT_ADJUST_CONFIRM_THRESHOLD_MA = 10.0
AUTO_APPLY_DEBOUNCE_MS = 150


class AuxiliaryWindow(QMainWindow):
    def closeEvent(self, event) -> None:  # noqa: N802
        self.hide()
        event.ignore()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.service = DlcProService()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dlcpro")
        self.language = "zh"
        self.busy = False
        self.snapshot: DeviceSnapshot | None = None
        self.pending_future: Future | None = None
        self.pending_success_handler = None
        self.current_set_dirty = False
        self.current_set_programmatic_update = False
        self.cc_programmatic_update = False
        self.feedforward_programmatic_update = False
        self.arc_programmatic_update = False
        self.tc_programmatic_update = False
        self.last_device_current_set: float | None = None

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

        self.laser_window = AuxiliaryWindow()
        self.laser_window.resize(760, 720)
        self.laser_window.setCentralWidget(self.laser_page)

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
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        self.laser_group = QGroupBox()
        group_layout = QVBoxLayout(self.laser_group)
        group_layout.setContentsMargins(12, 12, 12, 12)
        group_layout.setSpacing(12)

        self.laser_page_title = QLabel()
        self.laser_page_title.setObjectName("PageTitle")
        group_layout.addWidget(self.laser_page_title)

        panel = QFrame()
        panel.setObjectName("LaserPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(16)

        cc_header = QHBoxLayout()
        self.cc_label = QLabel()
        self.cc_label.setObjectName("SectionTitle")
        cc_header.addWidget(self.cc_label)
        cc_header.addStretch(1)
        self.cc_enable_button = self._create_toggle_button(self._on_cc_enable_toggled)
        cc_header.addWidget(self.cc_enable_button)
        panel_layout.addLayout(cc_header)

        top_form = QFormLayout()
        top_form.setLabelAlignment(Qt.AlignLeft)
        top_form.setFormAlignment(Qt.AlignTop)
        top_form.setHorizontalSpacing(18)
        top_form.setVerticalSpacing(14)

        self.precision_label = QLabel()
        self.precision_combo = QComboBox()
        self.precision_combo.addItem("", 100.0)
        self.precision_combo.addItem("", 10.0)
        self.precision_combo.addItem("", 1.0)
        self.precision_combo.addItem("", 0.1)
        self.precision_combo.addItem("", 0.01)
        self.precision_combo.addItem("", 0.001)
        self.precision_combo.addItem("", 0.0001)
        self.precision_combo.addItem("", 0.00001)
        self.precision_combo.setCurrentIndex(3)
        self.precision_combo.currentIndexChanged.connect(self._update_precision)

        self.current_set_label = QLabel()
        self.current_set_spin = QDoubleSpinBox()
        self.current_set_spin.setRange(-1000000.0, 1000000.0)
        self.current_set_spin.setDecimals(5)
        self.current_set_spin.setSingleStep(0.1)
        self.current_set_spin.setKeyboardTracking(False)
        self.current_set_spin.valueChanged.connect(self._on_current_set_changed)

        self.current_act_label = QLabel()
        self.current_act_value = QLabel("-")
        self.current_act_value.setObjectName("ReadValue")

        self.current_clip_label = QLabel()
        self.current_clip_spin = QDoubleSpinBox()
        self.current_clip_spin.setRange(-1000000.0, 1000000.0)
        self.current_clip_spin.setDecimals(5)
        self.current_clip_spin.setKeyboardTracking(False)
        self.current_clip_spin.editingFinished.connect(self._on_current_clip_finished)

        top_form.addRow(self.precision_label, self.precision_combo)
        top_form.addRow(self.current_set_label, self.current_set_spin)
        top_form.addRow(self.current_act_label, self.current_act_value)
        top_form.addRow(self.current_clip_label, self.current_clip_spin)
        panel_layout.addLayout(top_form)

        self.current_meta_hint = QLabel()
        self.current_meta_hint.setObjectName("SubtleHint")
        panel_layout.addWidget(self.current_meta_hint)

        divider_1 = QFrame()
        divider_1.setFrameShape(QFrame.HLine)
        divider_1.setObjectName("Divider")
        panel_layout.addWidget(divider_1)

        ff_header = QHBoxLayout()
        self.feedforward_label = QLabel()
        ff_header.addWidget(self.feedforward_label)
        ff_header.addStretch(1)
        self.feedforward_enable_button = self._create_toggle_button(self._on_feedforward_enable_toggled)
        ff_header.addWidget(self.feedforward_enable_button)
        panel_layout.addLayout(ff_header)

        ff_form = QFormLayout()
        self.feedforward_factor_label = QLabel()
        self.feedforward_factor_spin = QDoubleSpinBox()
        self.feedforward_factor_spin.setRange(-1000000.0, 1000000.0)
        self.feedforward_factor_spin.setDecimals(5)
        self.feedforward_factor_spin.setKeyboardTracking(False)
        self.feedforward_factor_spin.editingFinished.connect(self._on_feedforward_factor_finished)
        ff_form.addRow(self.feedforward_factor_label, self.feedforward_factor_spin)
        panel_layout.addLayout(ff_form)

        divider_2 = QFrame()
        divider_2.setFrameShape(QFrame.HLine)
        divider_2.setObjectName("Divider")
        panel_layout.addWidget(divider_2)

        arc_header = QHBoxLayout()
        self.arc_label = QLabel()
        arc_header.addWidget(self.arc_label)
        arc_header.addStretch(1)
        self.arc_enable_button = self._create_toggle_button(self._on_arc_enable_toggled)
        arc_header.addWidget(self.arc_enable_button)
        panel_layout.addLayout(arc_header)

        arc_form = QFormLayout()
        self.arc_signal_label = QLabel()
        self.arc_signal_combo = QComboBox()
        self.arc_signal_combo.currentIndexChanged.connect(self._on_arc_signal_changed)
        self.arc_factor_label = QLabel()
        self.arc_factor_spin = QDoubleSpinBox()
        self.arc_factor_spin.setRange(-1000000.0, 1000000.0)
        self.arc_factor_spin.setDecimals(5)
        self.arc_factor_spin.setKeyboardTracking(False)
        self.arc_factor_spin.editingFinished.connect(self._on_arc_factor_finished)
        arc_form.addRow(self.arc_signal_label, self.arc_signal_combo)
        arc_form.addRow(self.arc_factor_label, self.arc_factor_spin)
        panel_layout.addLayout(arc_form)

        self.auto_apply_hint_label = QLabel()
        self.auto_apply_hint_label.setObjectName("SubtleHint")
        panel_layout.addWidget(self.auto_apply_hint_label, alignment=Qt.AlignRight)

        tc_panel = QFrame()
        tc_panel.setObjectName("LaserPanel")
        tc_panel_layout = QVBoxLayout(tc_panel)
        tc_panel_layout.setContentsMargins(18, 18, 18, 18)
        tc_panel_layout.setSpacing(16)

        tc_header = QHBoxLayout()
        self.tc_label = QLabel()
        self.tc_label.setObjectName("SectionTitle")
        tc_header.addWidget(self.tc_label)
        tc_header.addStretch(1)
        self.tc_enable_button = self._create_toggle_button(self._on_tc_enable_toggled)
        tc_header.addWidget(self.tc_enable_button)
        tc_panel_layout.addLayout(tc_header)

        tc_form = QFormLayout()
        tc_form.setLabelAlignment(Qt.AlignLeft)
        tc_form.setFormAlignment(Qt.AlignTop)
        tc_form.setHorizontalSpacing(18)
        tc_form.setVerticalSpacing(14)

        self.temp_set_label = QLabel()
        self.temp_set_spin = QDoubleSpinBox()
        self.temp_set_spin.setRange(-1000000.0, 1000000.0)
        self.temp_set_spin.setDecimals(5)
        self.temp_set_spin.setKeyboardTracking(False)
        self.temp_set_spin.editingFinished.connect(self._on_temp_set_finished)

        self.temp_act_label = QLabel()
        self.temp_act_value = QLabel("-")
        self.temp_act_value.setObjectName("ReadValue")

        tc_form.addRow(self.temp_set_label, self.temp_set_spin)
        tc_form.addRow(self.temp_act_label, self.temp_act_value)
        tc_panel_layout.addLayout(tc_form)

        divider_3 = QFrame()
        divider_3.setFrameShape(QFrame.HLine)
        divider_3.setObjectName("Divider")
        tc_panel_layout.addWidget(divider_3)

        tc_arc_header = QHBoxLayout()
        self.tc_arc_label = QLabel()
        tc_arc_header.addWidget(self.tc_arc_label)
        tc_arc_header.addStretch(1)
        self.tc_arc_enable_button = self._create_toggle_button(self._on_tc_arc_enable_toggled)
        tc_arc_header.addWidget(self.tc_arc_enable_button)
        tc_panel_layout.addLayout(tc_arc_header)

        tc_arc_form = QFormLayout()
        self.tc_arc_signal_label = QLabel()
        self.tc_arc_signal_combo = QComboBox()
        self.tc_arc_signal_combo.currentIndexChanged.connect(self._on_tc_arc_signal_changed)
        self.tc_arc_factor_label = QLabel()
        self.tc_arc_factor_spin = QDoubleSpinBox()
        self.tc_arc_factor_spin.setRange(-1000000.0, 1000000.0)
        self.tc_arc_factor_spin.setDecimals(5)
        self.tc_arc_factor_spin.setKeyboardTracking(False)
        self.tc_arc_factor_spin.editingFinished.connect(self._on_tc_arc_factor_finished)
        tc_arc_form.addRow(self.tc_arc_signal_label, self.tc_arc_signal_combo)
        tc_arc_form.addRow(self.tc_arc_factor_label, self.tc_arc_factor_spin)
        tc_panel_layout.addLayout(tc_arc_form)

        group_layout.addWidget(panel)
        group_layout.addWidget(tc_panel)
        group_layout.addStretch(1)
        layout.addWidget(self.laser_group)
        return page

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

    def _create_toggle_button(self, slot) -> QPushButton:
        button = QPushButton()
        button.setCheckable(True)
        button.setMinimumWidth(124)
        button.clicked.connect(slot)
        return button

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
        self.laser_group.setTitle(t["laser"])
        self.parameter_group.setTitle(t["device_parameters"])
        self.overview_title.setText(t["device_overview"])
        self.laser_page_title.setText(t["laser_page_subtitle"])
        self.laser_window.setWindowTitle(f"{t['window_title']} - {t['laser']}")

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

        self.cc_label.setText(t["laser_page_title"])
        self.precision_label.setText(t["step_precision"])
        self.current_set_label.setText(t["current_set"])
        self.current_act_label.setText(t["current_act"])
        self.current_clip_label.setText(t["maximum_current"])
        self.feedforward_label.setText(t["feedforward"])
        self.feedforward_factor_label.setText(t["feedforward_factor"])
        self.arc_label.setText(t["arc"])
        self.arc_signal_label.setText(t["arc_signal_input"])
        self.arc_factor_label.setText(t["arc_factor"])
        self.tc_label.setText(t["temperature_control"])
        self.temp_set_label.setText(t["set_temperature"])
        self.temp_act_label.setText(t["actual_temperature"])
        self.tc_arc_label.setText(t["arc"])
        self.tc_arc_signal_label.setText(t["arc_signal_input"])
        self.tc_arc_factor_label.setText(t["arc_factor"])
        self.current_meta_hint.setText(
            f"{t['current_clip_tuning']} / {t['current_clip_limit']} / {t['effective_current_max']}"
        )
        self.cc_status_label = t["cc_status"]
        self.auto_apply_hint_label.setText(t["auto_apply_hint"])

        self.precision_combo.setItemText(0, t["step_100"])
        self.precision_combo.setItemText(1, t["step_10"])
        self.precision_combo.setItemText(2, t["step_1_int"])
        self.precision_combo.setItemText(3, t["step_1"])
        self.precision_combo.setItemText(4, t["step_2"])
        self.precision_combo.setItemText(5, t["step_3"])
        self.precision_combo.setItemText(6, t["step_4"])
        self.precision_combo.setItemText(7, t["step_5"])

        self._populate_arc_signal_options()
        self._populate_tc_arc_signal_options()
        if self.snapshot is not None:
            self._render_snapshot(self.snapshot)
        else:
            self._update_toggle_button(self.cc_enable_button, False)
            self._update_toggle_button(self.feedforward_enable_button, False)
            self._update_toggle_button(self.arc_enable_button, False)
            self._update_toggle_button(self.tc_enable_button, False)
            self._update_toggle_button(self.tc_arc_enable_button, False)

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
            self.cc_enable_button,
            self.feedforward_enable_button,
            self.arc_enable_button,
            self.tc_enable_button,
            self.tc_arc_enable_button,
            self.precision_combo,
        ):
            widget.setEnabled(writable)

    def _run_task(self, fn, on_success) -> None:
        if self.busy:
            return
        self._set_busy(True)
        self.pending_success_handler = on_success
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

        try:
            result = future.result()
        except Exception as exc:  # noqa: BLE001
            self._handle_task_done(on_success, False, exc)
            return

        self._handle_task_done(on_success, True, result)

    def _handle_task_done(self, on_success, ok: bool, result: object) -> None:
        self._set_busy(False)
        if ok:
            if on_success is not None:
                on_success(result)
            return
        message = self.service.format_error(result) if isinstance(result, Exception) else str(result)
        QMessageBox.critical(self, "Error", message)

    def _on_language_changed(self) -> None:
        self.language = self.language_combo.currentData()
        self._apply_texts()

    def _update_precision(self) -> None:
        step = float(self.precision_combo.currentData())
        decimals = {
            100.0: 0,
            10.0: 0,
            1.0: 0,
            0.1: 1,
            0.01: 2,
            0.001: 3,
            0.0001: 4,
            0.00001: 5,
        }[step]
        self.current_set_spin.setDecimals(decimals)
        self.current_set_spin.setSingleStep(step)

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

    def disconnect_device(self) -> None:
        self.refresh_timer.stop()
        self.current_apply_timer.stop()
        try:
            self.service.disconnect()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", self.service.format_error(exc))
            return
        self.snapshot = None
        self.last_device_current_set = None
        self.parameter_table.setRowCount(0)
        self.current_set_programmatic_update = True
        self.current_set_spin.setValue(0.0)
        self.current_set_programmatic_update = False
        self.current_act_value.setText("-")
        self.current_clip_spin.setValue(0.0)
        self.feedforward_factor_spin.setValue(0.0)
        self.arc_factor_spin.setValue(0.0)
        self.temp_set_spin.setValue(0.0)
        self.temp_act_value.setText("-")
        self.tc_arc_factor_spin.setValue(0.0)
        self.current_set_dirty = False
        self._update_toggle_button(self.cc_enable_button, False)
        self._update_toggle_button(self.feedforward_enable_button, False)
        self._update_toggle_button(self.arc_enable_button, False)
        self._update_toggle_button(self.tc_enable_button, False)
        self._update_toggle_button(self.tc_arc_enable_button, False)
        self._set_busy(False)

    def refresh_snapshot(self) -> None:
        if not self.service.is_connected or self.busy:
            return
        self._run_task(self.service.read_snapshot, self._on_snapshot_updated)

    def _on_snapshot_updated(self, snapshot: DeviceSnapshot) -> None:
        self.snapshot = snapshot
        self._render_snapshot(snapshot)
        if not self.refresh_timer.isActive():
            self.refresh_timer.start()

    def _render_snapshot(self, snapshot: DeviceSnapshot) -> None:
        values = asdict(snapshot)
        display_order = [
            "system_label",
            "serial_number",
            "fw_ver",
            "system_type",
            "system_model",
            "uptime_txt",
            "emission",
            "interlock_open",
            "cc_enabled",
            "cc_emission",
            "current_set",
            "current_act",
            "current_clip",
            "current_clip_tuning",
            "current_clip_limit",
            "effective_current_max",
            "feedforward_enabled",
            "feedforward_factor",
            "arc_enabled",
            "arc_signal",
            "arc_factor",
            "tc_enabled",
            "temp_set",
            "temp_act",
            "tc_arc_enabled",
            "tc_arc_signal",
            "tc_arc_factor",
            "use_current_clip_tuning",
            "cc_status_txt",
            "latest_message",
        ]
        self.parameter_table.setRowCount(len(display_order))
        for row, key in enumerate(display_order):
            label = PARAMETER_LABELS.get(key, {"zh": key, "en": key})[self.language]
            value = values[key]
            if key in {"arc_signal", "tc_arc_signal"}:
                value = self._arc_signal_name(int(value))
            elif isinstance(value, bool):
                value = TEXT[self.language]["enabled_state"] if value else TEXT[self.language]["disabled_state"]
            elif isinstance(value, float):
                value = f"{value:.5f}"
            self.parameter_table.setItem(row, 0, QTableWidgetItem(label))
            self.parameter_table.setItem(row, 1, QTableWidgetItem(str(value)))

        self.last_device_current_set = snapshot.current_set
        if not self.current_set_dirty and not self.current_set_spin.hasFocus():
            self.current_set_programmatic_update = True
            self.current_set_spin.blockSignals(True)
            self.current_set_spin.setValue(snapshot.current_set)
            self.current_set_spin.blockSignals(False)
            self.current_set_programmatic_update = False
        elif abs(self.current_set_spin.value() - snapshot.current_set) < 0.000005:
            self.current_set_dirty = False

        self.cc_programmatic_update = True
        self.feedforward_programmatic_update = True
        self.arc_programmatic_update = True
        self.tc_programmatic_update = True

        self.current_clip_spin.blockSignals(True)
        self.current_clip_spin.setValue(snapshot.current_clip)
        self.current_clip_spin.blockSignals(False)
        self.current_clip_spin.setMaximum(max(snapshot.effective_current_max, self.current_clip_spin.minimum()))

        self.current_act_value.setText(f"{snapshot.current_act:.5f} mA")
        self.feedforward_factor_spin.blockSignals(True)
        self.feedforward_factor_spin.setValue(snapshot.feedforward_factor)
        self.feedforward_factor_spin.blockSignals(False)
        self.arc_factor_spin.blockSignals(True)
        self.arc_factor_spin.setValue(snapshot.arc_factor)
        self.arc_factor_spin.blockSignals(False)
        self.temp_set_spin.blockSignals(True)
        self.temp_set_spin.setValue(snapshot.temp_set)
        self.temp_set_spin.blockSignals(False)
        self.temp_act_value.setText(f"{snapshot.temp_act:.5f} {TEXT[self.language]['temperature_unit']}")
        self.tc_arc_factor_spin.blockSignals(True)
        self.tc_arc_factor_spin.setValue(snapshot.tc_arc_factor)
        self.tc_arc_factor_spin.blockSignals(False)

        index = self.arc_signal_combo.findData(snapshot.arc_signal)
        if index >= 0:
            self.arc_signal_combo.blockSignals(True)
            self.arc_signal_combo.setCurrentIndex(index)
            self.arc_signal_combo.blockSignals(False)
        index = self.tc_arc_signal_combo.findData(snapshot.tc_arc_signal)
        if index >= 0:
            self.tc_arc_signal_combo.blockSignals(True)
            self.tc_arc_signal_combo.setCurrentIndex(index)
            self.tc_arc_signal_combo.blockSignals(False)

        self._update_toggle_button(self.cc_enable_button, snapshot.cc_enabled)
        self._update_toggle_button(self.feedforward_enable_button, snapshot.feedforward_enabled)
        self._update_toggle_button(self.arc_enable_button, snapshot.arc_enabled)
        self._update_toggle_button(self.tc_enable_button, snapshot.tc_enabled)
        self._update_toggle_button(self.tc_arc_enable_button, snapshot.tc_arc_enabled)

        self.current_meta_hint.setText(
            f"{TEXT[self.language]['current_clip_tuning']}: {snapshot.current_clip_tuning:.5f} mA   |   "
            f"{TEXT[self.language]['current_clip_limit']}: {snapshot.current_clip_limit:.5f} mA   |   "
            f"{TEXT[self.language]['effective_current_max']}: {snapshot.effective_current_max:.5f} mA"
        )

        self.cc_programmatic_update = False
        self.feedforward_programmatic_update = False
        self.arc_programmatic_update = False
        self.tc_programmatic_update = False

    def _arc_signal_name(self, value: int) -> str:
        for key, signal in ARC_SIGNAL_OPTIONS:
            if signal == value:
                return TEXT[self.language][key]
        return str(value)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.refresh_timer.stop()
        self.future_poll_timer.stop()
        self.current_apply_timer.stop()
        self.laser_window.close()
        self.service.disconnect()
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
