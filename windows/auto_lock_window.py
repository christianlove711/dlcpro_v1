from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dlcpro_service import AutoLockTelemetry, DeviceSnapshot, LockPointSnapshot
from ui_text import AUTO_LOCK_STRATEGY_OPTIONS, TEXT
from windows.auto_lock_scope_window import AutoLockScopeWindow
from widgets.auto_lock import AutoLockConfigPanel, AutoLockStatusPanel
from windows.base_window import AuxiliaryWindow


class AutoLockWindow(AuxiliaryWindow):
    def __init__(self, owner, controller) -> None:
        super().__init__()
        self.owner = owner
        self.controller = controller
        self._live_telemetry_active = False
        self._last_candidates: tuple[LockPointSnapshot, ...] = ()
        self.scope_window = AutoLockScopeWindow(owner, controller)

        self.resize(1120, 820)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.status_hint = QLabel()
        self.status_hint.setObjectName("SubtleHint")
        self.status_hint.setWordWrap(True)
        root.addWidget(self.status_hint)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        self.config_panel = AutoLockConfigPanel()
        self.config_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_row.addWidget(self.config_panel, 3)

        self.status_panel = AutoLockStatusPanel()
        self.status_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_row.addWidget(self.status_panel, 2)
        root.addLayout(top_row)

        self.scope_group = QGroupBox()
        scope_layout = QVBoxLayout(self.scope_group)
        scope_layout.setContentsMargins(12, 12, 12, 12)
        scope_layout.setSpacing(10)

        self.scope_hint_label = QLabel()
        self.scope_hint_label.setObjectName("SubtleHint")
        self.scope_hint_label.setWordWrap(True)
        scope_layout.addWidget(self.scope_hint_label)

        scope_summary_row = QHBoxLayout()
        scope_summary_row.setSpacing(12)
        self.scope_mode_label = QLabel()
        self.scope_mode_value = QLabel()
        self.scope_mode_value.setObjectName("ReadValue")
        self.scope_window_button = QPushButton()
        self.scope_window_button.setObjectName("ScopeOpenButton")
        scope_summary_row.addWidget(self.scope_mode_label)
        scope_summary_row.addWidget(self.scope_mode_value, 1)
        scope_summary_row.addWidget(self.scope_window_button)
        scope_layout.addLayout(scope_summary_row)

        self.scope_status_label = QLabel()
        self.scope_status_label.setObjectName("SubtleHint")
        self.scope_status_label.setWordWrap(True)
        scope_layout.addWidget(self.scope_status_label)
        root.addWidget(self.scope_group)

        lower_row = QHBoxLayout()
        lower_row.setSpacing(14)

        self.candidate_group = QGroupBox()
        candidate_layout = QVBoxLayout(self.candidate_group)
        candidate_layout.setContentsMargins(12, 12, 12, 12)
        candidate_layout.setSpacing(10)
        self.candidate_table = QTableWidget(0, 3)
        self.candidate_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.candidate_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.candidate_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.candidate_table.verticalHeader().setVisible(False)
        self.candidate_table.horizontalHeader().setStretchLastSection(True)
        self.candidate_table.setAlternatingRowColors(False)
        candidate_layout.addWidget(self.candidate_table)
        lower_row.addWidget(self.candidate_group, 2)

        self.log_group = QGroupBox()
        log_layout = QVBoxLayout(self.log_group)
        log_layout.setContentsMargins(12, 12, 12, 12)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(170)
        log_layout.addWidget(self.log_edit)
        lower_row.addWidget(self.log_group, 2)
        root.addLayout(lower_row, 1)

        self.setCentralWidget(central)

        self.config_panel.start_button.clicked.connect(controller.start)
        self.config_panel.stop_button.clicked.connect(controller.stop)
        self.config_panel.clear_log_button.clicked.connect(self.clear_log)
        self.scope_window_button.clicked.connect(self.open_scope_window)
        self.candidate_table.cellClicked.connect(controller.on_candidate_row_clicked)

        self.reset_state(owner.language)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.controller.on_window_visibility_changed(True)

    def hideEvent(self, event) -> None:  # noqa: N802
        self.controller.on_window_visibility_changed(False)
        super().hideEvent(event)

    def request_shutdown(self) -> None:
        self.scope_window.request_shutdown()
        self.scope_window.close()
        super().request_shutdown()

    def open_scope_window(self) -> None:
        if self.scope_window.isHidden():
            self.scope_window.move(self.x() + 100, self.y() + 80)
        self.scope_window.showNormal()
        self.scope_window.show()
        self.scope_window.raise_()
        self.scope_window.activateWindow()

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(f"{t['window_title']} - {t['auto_lock']}")
        self.status_hint.setText(t["auto_lock_status_hint"])

        self.config_panel.title_label.setText(t["auto_lock_config"])
        self.config_panel.strategy_label.setText(t["auto_lock_strategy"])
        self.config_panel.search_interval_label.setText(t["auto_lock_search_interval"])
        self.config_panel.settle_delay_label.setText(t["auto_lock_settle_delay"])
        self.config_panel.lock_timeout_label.setText(t["auto_lock_lock_timeout"])
        self.config_panel.monitor_interval_label.setText(t["auto_lock_monitor_interval"])
        self.config_panel.reacquire_delay_label.setText(t["auto_lock_reacquire_delay"])
        self.config_panel.auto_enable_scan_check.setText(t["auto_lock_auto_enable_scan"])
        self.config_panel.watch_after_lock_check.setText(t["auto_lock_watch_after_lock"])
        self.config_panel.start_button.setText(t["auto_lock_start"])
        self.config_panel.stop_button.setText(t["auto_lock_stop"])
        self.config_panel.clear_log_button.setText(t["auto_lock_clear_log"])

        for spin in (
            self.config_panel.search_interval_spin,
            self.config_panel.settle_delay_spin,
            self.config_panel.lock_timeout_spin,
            self.config_panel.monitor_interval_spin,
            self.config_panel.reacquire_delay_spin,
        ):
            spin.setSuffix(" ms")

        self.status_panel.title_label.setText(t["auto_lock_runtime"])
        self.status_panel.phase_label.setText(t["auto_lock_phase"])
        self.status_panel.lock_state_label.setText(t["auto_lock_lock_state"])
        self.status_panel.lock_enabled_label.setText(t["auto_lock_lock_enabled"])
        self.status_panel.candidate_count_label.setText(t["auto_lock_candidate_count"])
        self.status_panel.scan_offset_label.setText(t["auto_lock_scan_offset"])
        self.status_panel.target_label.setText(t["auto_lock_target"])
        self.status_panel.tracking_label.setText(t["auto_lock_tracking"])
        self.status_panel.message_label.setText(t["auto_lock_message"])

        self.scope_group.setTitle(t["auto_lock_scope"])
        self.scope_hint_label.setText(t["auto_lock_scope_status_hint"])
        self.scope_mode_label.setText(t["auto_lock_scope_mode"])
        self.scope_window_button.setText(t["auto_lock_scope_open_window"])
        self.scope_window.apply_texts(language)

        self.candidate_group.setTitle(t["auto_lock_candidates"])
        self.log_group.setTitle(t["auto_lock_log"])
        self.candidate_table.setHorizontalHeaderLabels(
            [t["auto_lock_table_index"], t["auto_lock_table_x"], t["auto_lock_table_y"]]
        )
        self._populate_strategy_options(language)

    def reset_state(self, language: str) -> None:
        self._live_telemetry_active = False
        self._last_candidates = ()
        self.apply_texts(language)
        t = TEXT[language]
        self.status_panel.phase_value.setText(t["auto_lock_phase_idle"])
        self.status_panel.lock_state_value.setText(t["auto_lock_value_waiting"])
        self.status_panel.lock_enabled_value.setText(t["disabled_state"])
        self.status_panel.candidate_count_value.setText("0")
        self.status_panel.scan_offset_value.setText(f"0.000000 {t['voltage_unit']}")
        self.status_panel.target_value.setText(t["auto_lock_value_none"])
        self.status_panel.tracking_value.setText(t["auto_lock_value_none"])
        self.status_panel.message_value.setText(t["auto_lock_window_stopped"])
        self.scope_mode_value.setText(t["auto_lock_value_waiting"])
        self.scope_status_label.setText(t["auto_lock_scope_click_hint"])
        self.scope_window.reset_state(language)
        self.candidate_table.setRowCount(0)

    def render_snapshot(self, snapshot: DeviceSnapshot | None) -> None:
        if snapshot is None:
            self.reset_state(self.owner.language)
            return
        if self._live_telemetry_active:
            return
        t = TEXT[self.owner.language]
        self.status_panel.lock_enabled_value.setText(
            t["enabled_state"] if snapshot.lock_enabled else t["disabled_state"]
        )
        self.status_panel.scan_offset_value.setText(f"{snapshot.sc_offset:.6f} {snapshot.sc_unit}")

    def render_telemetry(self, telemetry: AutoLockTelemetry, language: str) -> None:
        self._live_telemetry_active = True
        self._last_candidates = telemetry.candidates
        t = TEXT[language]
        self.status_panel.lock_enabled_value.setText(
            t["enabled_state"] if telemetry.lock_enabled else t["disabled_state"]
        )
        self.status_panel.lock_state_value.setText(self._lock_state_text(language, telemetry.lock_state))
        self.status_panel.candidate_count_value.setText(str(len(telemetry.candidates)))
        self.status_panel.scan_offset_value.setText(f"{telemetry.sc_offset:.6f} {telemetry.sc_unit}")
        self.status_panel.target_value.setText(self._format_point(telemetry.selected, t))
        self.status_panel.tracking_value.setText(self._format_point(telemetry.tracking, t))
        self._render_candidates(telemetry.candidates)
        self._render_scope_summary(telemetry, t)
        self.scope_window.render_telemetry(telemetry, language, self.controller.target_for_display())

    def set_phase(self, language: str, phase_key: str) -> None:
        self.status_panel.phase_value.setText(TEXT[language][phase_key])

    def set_status_message(self, text: str) -> None:
        self.status_panel.message_value.setText(text)

    def set_target_point(self, point: LockPointSnapshot | None, language: str) -> None:
        t = TEXT[language]
        self.status_panel.target_value.setText(self._format_point(point, t))
        self._select_candidate_row(point)
        self.scope_window.set_target_point(point, language)

    def set_scope_status_message(self, text: str) -> None:
        self.scope_status_label.setText(text)
        self.scope_window.set_scope_status_message(text)

    def set_writable(self, writable: bool, previewable: bool, running: bool) -> None:
        editable = previewable and not running
        for widget in (
            self.config_panel.strategy_combo,
            self.config_panel.search_interval_spin,
            self.config_panel.settle_delay_spin,
            self.config_panel.lock_timeout_spin,
            self.config_panel.monitor_interval_spin,
            self.config_panel.reacquire_delay_spin,
            self.config_panel.auto_enable_scan_check,
            self.config_panel.watch_after_lock_check,
        ):
            widget.setEnabled(editable)
        self.config_panel.start_button.setEnabled(writable and not running)
        self.config_panel.stop_button.setEnabled(running)
        self.config_panel.clear_log_button.setEnabled(True)
        self.scope_window_button.setEnabled(True)
        self.scope_window.set_writable(writable, running)

    def append_log(self, text: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_edit.append(f"[{timestamp}] {text}")

    def clear_log(self) -> None:
        self.log_edit.clear()

    def mark_live_telemetry_stopped(self) -> None:
        self._live_telemetry_active = False

    def _populate_strategy_options(self, language: str) -> None:
        combo = self.config_panel.strategy_combo
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in AUTO_LOCK_STRATEGY_OPTIONS:
            combo.addItem(TEXT[language][text_key], value)
        combo.blockSignals(False)
        target = "nearest_center" if current is None else current
        index = combo.findData(target)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _render_candidates(self, candidates: tuple[LockPointSnapshot, ...]) -> None:
        self.candidate_table.setRowCount(len(candidates))
        for row, point in enumerate(candidates):
            self.candidate_table.setItem(row, 0, self._create_table_item(str(row + 1)))
            self.candidate_table.setItem(row, 1, self._create_table_item(f"{point.x:.6f}"))
            self.candidate_table.setItem(row, 2, self._create_table_item(f"{point.y:.6f}"))

    def _render_scope_summary(self, telemetry: AutoLockTelemetry, text_map: dict[str, str]) -> None:
        if telemetry.scope is not None:
            self.scope_mode_value.setText(self._scope_mode_text(text_map, telemetry.scope.variant))
            status_text = text_map["auto_lock_scope_click_hint"]
            if telemetry.scope_error:
                status_text = f"{text_map['auto_lock_scope_error_prefix']}{telemetry.scope_error}"
            self.scope_status_label.setText(status_text)
            return

        self.scope_mode_value.setText(text_map["auto_lock_value_waiting"])
        if telemetry.scope_error:
            self.scope_status_label.setText(f"{text_map['auto_lock_scope_error_prefix']}{telemetry.scope_error}")
            return
        self.scope_status_label.setText(text_map["auto_lock_scope_click_hint"])

    def _select_candidate_row(self, point: LockPointSnapshot | None) -> None:
        self.candidate_table.clearSelection()
        if point is None:
            return
        for row, candidate in enumerate(self._last_candidates):
            if abs(candidate.x - point.x) < 1e-9 and abs(candidate.y - point.y) < 1e-9:
                self.candidate_table.selectRow(row)
                return

    @staticmethod
    def _create_table_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    @classmethod
    def _format_point(cls, point: LockPointSnapshot | None, text_map: dict[str, str]) -> str:
        if point is None:
            return text_map["auto_lock_value_none"]
        return f"{point.x:.6f} / {point.y:.6f}"

    @staticmethod
    def _lock_state_text(language: str, state: int | None) -> str:
        t = TEXT[language]
        if state is None:
            return t["auto_lock_value_waiting"]
        if state == 3:
            return f"{t['auto_lock_state_selected']} (3)"
        if state == 5:
            return f"{t['auto_lock_state_locked']} (5)"
        return t["auto_lock_state_unknown"].format(value=state)

    @staticmethod
    def _scope_mode_text(text_map: dict[str, str], variant: int) -> str:
        if variant == 0:
            return text_map["auto_lock_scope_mode_xy"]
        if variant == 1:
            return text_map["auto_lock_scope_mode_time"]
        if variant == 2:
            return text_map["auto_lock_scope_mode_frequency"]
        return str(variant)
