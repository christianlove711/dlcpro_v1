from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from dlcpro_service import AutoLockTelemetry, DeviceSnapshot, LockPointSnapshot
from ui_text import (
    AUTO_LOCK_STRATEGY_OPTIONS,
    FALC_PATH_SELECTION_OPTIONS,
    LOCK_ERROR_SIGNAL_OPTIONS,
    LOCK_FALC_SELECTION_OPTIONS,
    TEXT,
)
from ui_scaling import fit_window_to_screen
from windows.auto_lock_scope_window import AutoLockScopeWindow
from widgets.auto_lock import AutoLockConfigPanel, AutoLockStatusPanel
from windows.base_window import AuxiliaryWindow


class AutoLockWindow(AuxiliaryWindow):
    PRESET_PATH = Path(__file__).resolve().parents[1] / "auto_lock_presets.json"

    def __init__(self, owner, controller) -> None:
        super().__init__()
        self.owner = owner
        self.controller = controller
        self._live_telemetry_active = False
        self._last_candidates: tuple[LockPointSnapshot, ...] = ()
        self._preset_store: dict[str, dict[str, object]] = {}
        self._selected_preset_name: str | None = None
        self._loaded_preset_name: str | None = None
        self._preset_buttons: dict[str, QPushButton] = {}
        self._preset_button_columns = 0
        self.scope_window = AutoLockScopeWindow(owner, controller)

        self.resize(1120, 820)

        central = QWidget(self)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll_area)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.status_hint = QLabel()
        self.status_hint.setObjectName("SubtleHint")
        self.status_hint.setWordWrap(True)
        root.addWidget(self.status_hint)

        self.status_panel = AutoLockStatusPanel()
        self.status_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        root.addWidget(self.status_panel)

        self.config_panel = AutoLockConfigPanel()
        self.config_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        root.addWidget(self.config_panel)

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

        scroll_area.setWidget(content)
        self.setCentralWidget(central)

        self.config_panel.start_button.clicked.connect(controller.start)
        self.config_panel.pre_scan_button.clicked.connect(self._show_pre_scan_help_and_start)
        self.config_panel.stop_button.clicked.connect(controller.stop)
        self.config_panel.clear_log_button.clicked.connect(self.clear_log)
        self.config_panel.preset_scope_button.clicked.connect(self._show_preset_scope_help)
        self.config_panel.preset_new_button.clicked.connect(self.create_new_preset)
        self.config_panel.preset_load_button.clicked.connect(self.load_selected_preset)
        self.config_panel.preset_save_button.clicked.connect(self.save_current_preset)
        self.config_panel.preset_delete_button.clicked.connect(self.delete_selected_preset)
        self.config_panel.error_signal_combo.currentIndexChanged.connect(owner._on_auto_lock_error_signal_changed)
        self.config_panel.falc_selection_combo.currentIndexChanged.connect(owner._on_auto_lock_falc_selection_changed)
        self.config_panel.falc_path_combo.currentIndexChanged.connect(owner._on_auto_lock_falc_path_selection_changed)
        self.config_panel.candidate_top_check.toggled.connect(owner._on_auto_lock_candidate_top_changed)
        self.config_panel.candidate_bottom_check.toggled.connect(owner._on_auto_lock_candidate_bottom_changed)
        self.config_panel.candidate_positive_edge_check.toggled.connect(
            owner._on_auto_lock_candidate_positive_edge_changed
        )
        self.config_panel.candidate_negative_edge_check.toggled.connect(
            owner._on_auto_lock_candidate_negative_edge_changed
        )
        self.config_panel.candidate_edge_level_spin.connect_live_apply(
            owner._on_auto_lock_candidate_edge_level_finished
        )
        self.config_panel.candidate_peak_noise_tolerance_spin.connect_live_apply(
            owner._on_auto_lock_candidate_peak_noise_tolerance_finished
        )
        self.config_panel.candidate_edge_min_distance_spin.connect_live_apply(
            owner._on_auto_lock_candidate_edge_min_distance_finished
        )
        self.config_panel.candidate_top_of_fringe_low_pass_check.toggled.connect(
            owner._on_auto_lock_candidate_top_of_fringe_low_pass_changed
        )
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
        fit_window_to_screen(self.scope_window)
        self.scope_window.raise_()
        self.scope_window.activateWindow()

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(f"{t['window_title']} - {t['auto_lock']}")
        self.status_hint.setText(t["auto_lock_status_hint"])

        self.config_panel.title_label.setText(t["auto_lock_config"])
        self.config_panel.overview_hint_label.setText(t["auto_lock_config_overview_hint"])
        self.config_panel.set_section_titles(t["auto_lock_basic_section"], t["auto_lock_advanced_section"])
        self.config_panel.quick_link_group.setTitle(t["auto_lock_quick_link"])
        self.config_panel.preset_group.setTitle(t["auto_lock_preset_group"])
        self.config_panel.basic_form_group.setTitle(t["auto_lock_basic_section"])
        self.config_panel.candidate_filter_group.setTitle(t["lock_candidate_filter"])
        self.config_panel.runtime_options_group.setTitle(t["auto_lock_advanced_section"])
        self.config_panel.preset_scope_hint_label.setText(t["auto_lock_preset_scope_hint"])
        self.config_panel.preset_button_list_label.setText(t["auto_lock_preset_select"])
        self.config_panel.preset_selected_label.setText(t["auto_lock_preset_selected"])
        self.config_panel.preset_name_label.setText(t["auto_lock_preset_name"])
        self.config_panel.preset_scope_button.setText(t["auto_lock_preset_scope_button"])
        self.config_panel.preset_new_button.setText(t["auto_lock_preset_new"])
        self.config_panel.preset_load_button.setText(t["auto_lock_preset_load"])
        self.config_panel.preset_save_button.setText(t["auto_lock_preset_save"])
        self.config_panel.preset_delete_button.setText(t["auto_lock_preset_delete"])
        self.config_panel.preset_details_label.setText(t["auto_lock_preset_details"])
        self.config_panel.error_signal_label.setText(t["lock_error_input_signal"])
        self.config_panel.falc_selection_label.setText(t["lock_falc_selection"])
        self.config_panel.falc_path_label.setText(t["falc_path_selection"])
        self.config_panel.candidate_top_check.setText(t["lock_candidate_top"])
        self.config_panel.candidate_bottom_check.setText(t["lock_candidate_bottom"])
        self.config_panel.candidate_positive_edge_check.setText(t["lock_candidate_positive_edge"])
        self.config_panel.candidate_negative_edge_check.setText(t["lock_candidate_negative_edge"])
        self.config_panel.candidate_edge_level_label.setText(t["lock_candidate_edge_level"])
        self.config_panel.candidate_peak_noise_tolerance_label.setText(t["lock_candidate_peak_noise_tolerance"])
        self.config_panel.candidate_edge_min_distance_label.setText(t["lock_candidate_edge_min_distance"])
        self.config_panel.candidate_top_of_fringe_low_pass_label.setText(t["lock_candidate_top_of_fringe_low_pass"])
        self.config_panel.strategy_label.setText(t["auto_lock_strategy"])
        self.config_panel.search_interval_label.setText(t["auto_lock_search_interval"])
        self.config_panel.settle_delay_label.setText(t["auto_lock_settle_delay"])
        self.config_panel.lock_timeout_label.setText(t["auto_lock_lock_timeout"])
        self.config_panel.monitor_interval_label.setText(t["auto_lock_monitor_interval"])
        self.config_panel.reacquire_delay_label.setText(t["auto_lock_reacquire_delay"])
        self.config_panel.pre_scan_duration_label.setText(t["auto_lock_pre_scan_duration"])
        self.config_panel.pre_scan_shrink_percent_label.setText(t["auto_lock_pre_scan_shrink_percent"])
        self.config_panel.pre_scan_usage_hint_label.setText(t["auto_lock_pre_scan_usage_hint"])
        self.config_panel.runtime_hint_label.setText(t["auto_lock_runtime_hint"])
        self.config_panel.auto_enable_scan_check.setText(t["auto_lock_auto_enable_scan"])
        self.config_panel.watch_after_lock_check.setText(t["auto_lock_watch_after_lock"])
        self.config_panel.pre_scan_button.setText(t["auto_lock_pre_scan_start"])
        self.config_panel.start_button.setText(t["auto_lock_start"])
        self.config_panel.stop_button.setText(t["auto_lock_stop"])
        self.config_panel.clear_log_button.setText(t["auto_lock_clear_log"])
        self.config_panel.pre_scan_button.setToolTip(t["auto_lock_pre_scan_usage_hint"])
        self.config_panel.preset_scope_button.setToolTip(t["auto_lock_preset_scope_button_hint"])
        self.config_panel.preset_save_button.setToolTip(t["auto_lock_preset_scope_hint"])
        self.config_panel.preset_new_button.setToolTip(t["auto_lock_preset_new_hint"])
        self.config_panel.preset_load_button.setToolTip(t["auto_lock_preset_load_hint"])
        self.config_panel.preset_delete_button.setToolTip(t["auto_lock_preset_delete_hint"])
        self.config_panel.preset_details_container.setToolTip(t["auto_lock_preset_scope_hint"])
        self._refresh_loaded_preset_display()

        for spin in (
            self.config_panel.search_interval_spin,
            self.config_panel.settle_delay_spin,
            self.config_panel.lock_timeout_spin,
            self.config_panel.monitor_interval_spin,
            self.config_panel.reacquire_delay_spin,
            self.config_panel.pre_scan_duration_spin,
            self.config_panel.pre_scan_shrink_percent_spin,
        ):
            spin.setSuffix(" ms")
        self.config_panel.pre_scan_shrink_percent_spin.setSuffix(" %")

        self.status_panel.title_label.setText(t["auto_lock_runtime"])
        self.status_panel.phase_label.setText(t["auto_lock_phase"])
        self.status_panel.lock_state_label.setText(t["auto_lock_lock_state"])
        self.status_panel.lock_enabled_label.setText(t["auto_lock_lock_enabled"])
        self.status_panel.template_progress_label.setText(t["auto_lock_template_progress"])
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
        self._populate_saved_presets()
        self._populate_combo_options(self.config_panel.error_signal_combo, LOCK_ERROR_SIGNAL_OPTIONS, language)
        self._populate_combo_options(self.config_panel.falc_selection_combo, LOCK_FALC_SELECTION_OPTIONS, language)
        self._populate_combo_options(self.config_panel.falc_path_combo, FALC_PATH_SELECTION_OPTIONS, language)
        self._refresh_selected_preset_details()

    def reset_state(self, language: str) -> None:
        self._live_telemetry_active = False
        self._last_candidates = ()
        self.apply_texts(language)
        t = TEXT[language]
        self.status_panel.phase_value.setText(t["auto_lock_phase_idle"])
        self.status_panel.lock_state_value.setText(t["auto_lock_value_waiting"])
        self.status_panel.lock_enabled_value.setText(t["disabled_state"])
        self.status_panel.template_progress_value.setText(t["auto_lock_value_waiting"])
        self.status_panel.candidate_count_value.setText("0")
        self.status_panel.scan_offset_value.setText(f"0.000000 {t['voltage_unit']}")
        self.status_panel.target_value.setText(t["auto_lock_value_none"])
        self.status_panel.tracking_value.setText(t["auto_lock_value_none"])
        self.status_panel.message_value.setText(t["auto_lock_window_stopped"])
        self.scope_mode_value.setText(t["auto_lock_value_waiting"])
        self.scope_status_label.setText(t["auto_lock_scope_click_hint"])
        self._selected_preset_name = None
        self._loaded_preset_name = None
        self.config_panel.preset_name_edit.clear()
        self._render_preset_detail_cards(None, self._collect_preset_payload())
        self.scope_window.reset_state(language)
        self._refresh_loaded_preset_display()
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
        self._sync_combo(self.config_panel.error_signal_combo, snapshot.lock_error_channel)
        self._sync_combo(self.config_panel.falc_selection_combo, snapshot.lock_falc_selection)
        if snapshot.falc1 is not None:
            self._sync_combo(self.config_panel.falc_path_combo, snapshot.falc1.path_selection)
        self._sync_check(self.config_panel.candidate_top_check, snapshot.lock_candidate_top_enabled)
        self._sync_check(self.config_panel.candidate_bottom_check, snapshot.lock_candidate_bottom_enabled)
        self._sync_check(
            self.config_panel.candidate_positive_edge_check,
            snapshot.lock_candidate_positive_edge_enabled,
        )
        self._sync_check(
            self.config_panel.candidate_negative_edge_check,
            snapshot.lock_candidate_negative_edge_enabled,
        )
        self._sync_check(
            self.config_panel.candidate_top_of_fringe_low_pass_check,
            snapshot.lock_candidate_top_of_fringe_low_pass,
        )
        self._set_spin_if_idle(self.config_panel.candidate_edge_level_spin, snapshot.lock_candidate_edge_level)
        self._set_spin_if_idle(
            self.config_panel.candidate_peak_noise_tolerance_spin,
            snapshot.lock_candidate_peak_noise_tolerance,
        )
        self._set_spin_if_idle(
            self.config_panel.candidate_edge_min_distance_spin,
            snapshot.lock_candidate_edge_min_distance,
        )
        self.config_panel.candidate_edge_level_spin.setSuffix(f" {t['voltage_unit']}")
        self.config_panel.candidate_peak_noise_tolerance_spin.setSuffix(f" {t['voltage_unit']}")

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
            self.config_panel.preset_name_edit,
            self.config_panel.error_signal_combo,
            self.config_panel.falc_selection_combo,
            self.config_panel.falc_path_combo,
            self.config_panel.search_interval_spin,
            self.config_panel.settle_delay_spin,
            self.config_panel.lock_timeout_spin,
            self.config_panel.monitor_interval_spin,
            self.config_panel.reacquire_delay_spin,
            self.config_panel.pre_scan_duration_spin,
            self.config_panel.pre_scan_shrink_percent_spin,
            self.config_panel.auto_enable_scan_check,
            self.config_panel.watch_after_lock_check,
        ):
            widget.setEnabled(editable)
        for button in self._preset_buttons.values():
            button.setEnabled(editable)
        self.config_panel.preset_new_button.setEnabled(not running)
        self.config_panel.preset_load_button.setEnabled(not running and self._selected_preset_name is not None)
        self.config_panel.preset_save_button.setEnabled(not running)
        self.config_panel.preset_delete_button.setEnabled(not running and self._selected_preset_name is not None)
        for widget in (
            self.config_panel.candidate_top_check,
            self.config_panel.candidate_bottom_check,
            self.config_panel.candidate_positive_edge_check,
            self.config_panel.candidate_negative_edge_check,
            self.config_panel.candidate_edge_level_spin,
            self.config_panel.candidate_peak_noise_tolerance_spin,
            self.config_panel.candidate_edge_min_distance_spin,
            self.config_panel.candidate_top_of_fringe_low_pass_check,
        ):
            widget.setEnabled(writable and not running)
        self.config_panel.pre_scan_button.setEnabled(not running)
        self.config_panel.start_button.setEnabled(not running)
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

    def set_template_progress(self, current: int | None, total: int, language: str) -> None:
        t = TEXT[language]
        if current is None or total <= 0:
            self.status_panel.template_progress_value.setText(t["auto_lock_value_waiting"])
            return
        self.status_panel.template_progress_value.setText(
            t["auto_lock_template_progress_value"].format(current=current, total=total)
        )

    def _show_pre_scan_help_and_start(self) -> None:
        t = TEXT[self.owner.language]
        result = QMessageBox.question(
            self,
            t["auto_lock_pre_scan_dialog_title"],
            t["auto_lock_pre_scan_dialog_body"].format(
                duration_ms=self.config_panel.pre_scan_duration_spin.value(),
                shrink_percent=self.config_panel.pre_scan_shrink_percent_spin.value(),
            ),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if result != QMessageBox.Yes:
            return
        self.controller.start_pre_scan_sequence()

    def save_current_preset(self) -> None:
        name = self.config_panel.preset_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", TEXT[self.owner.language]["auto_lock_preset_name_required"])
            return
        self._load_preset_store(force=True)
        if self._selected_preset_name is None:
            QMessageBox.warning(
                self,
                "Warning",
                TEXT[self.owner.language]["auto_lock_preset_save_requires_existing"],
            )
            return
        old_name = self._selected_preset_name
        if old_name != name and name in self._preset_store:
            QMessageBox.warning(
                self,
                "Warning",
                TEXT[self.owner.language]["auto_lock_preset_name_exists"].format(name=name),
            )
            return
        if old_name and old_name != name and old_name in self._preset_store:
            self._preset_store.pop(old_name, None)
        if old_name == self._loaded_preset_name:
            self._loaded_preset_name = name
        self._preset_store[name] = self._collect_preset_payload()
        try:
            self.PRESET_PATH.write_text(
                json.dumps(self._preset_store, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            QMessageBox.warning(self, "Warning", TEXT[self.owner.language]["auto_lock_preset_save_failed"])
            return
        self._selected_preset_name = name
        self._populate_saved_presets(selected_name=name)
        self.append_log(TEXT[self.owner.language]["auto_lock_preset_saved"].format(name=name))
        QMessageBox.information(
            self,
            TEXT[self.owner.language]["auto_lock_preset_save_success_title"],
            TEXT[self.owner.language]["auto_lock_preset_saved"].format(name=name),
        )

    def create_new_preset(self) -> None:
        self._load_preset_store(force=True)
        name = self.config_panel.preset_name_edit.text().strip()
        if not name:
            index = 1
            base_name = TEXT[self.owner.language]["auto_lock_preset_default_name"]
            name = f"{base_name} {index}"
            while name in self._preset_store:
                index += 1
                name = f"{base_name} {index}"
            self.config_panel.preset_name_edit.setText(name)
        elif name in self._preset_store:
            QMessageBox.warning(
                self,
                "Warning",
                TEXT[self.owner.language]["auto_lock_preset_name_exists"].format(name=name),
            )
            return
        self._preset_store[name] = self._collect_preset_payload()
        try:
            self.PRESET_PATH.write_text(
                json.dumps(self._preset_store, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            QMessageBox.warning(self, "Warning", TEXT[self.owner.language]["auto_lock_preset_save_failed"])
            return
        self._selected_preset_name = name
        self._populate_saved_presets(selected_name=name)
        self.append_log(TEXT[self.owner.language]["auto_lock_preset_created"].format(name=name))
        self._refresh_preset_button_states()
        self._refresh_selected_preset_details()
        QMessageBox.information(
            self,
            TEXT[self.owner.language]["auto_lock_preset_create_success_title"],
            TEXT[self.owner.language]["auto_lock_preset_created"].format(name=name),
        )

    def delete_selected_preset(self) -> None:
        name = (self._selected_preset_name or "").strip()
        if not name:
            QMessageBox.warning(
                self,
                "Warning",
                TEXT[self.owner.language]["auto_lock_preset_delete_requires_selection"],
            )
            return
        result = QMessageBox.question(
            self,
            TEXT[self.owner.language]["auto_lock_preset_delete_confirm_title"],
            TEXT[self.owner.language]["auto_lock_preset_delete_confirm_body"].format(name=name),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if result != QMessageBox.Yes:
            return
        self._load_preset_store(force=True)
        self._preset_store.pop(name, None)
        try:
            self.PRESET_PATH.write_text(
                json.dumps(self._preset_store, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            QMessageBox.warning(self, "Warning", TEXT[self.owner.language]["auto_lock_preset_save_failed"])
            return
        self._selected_preset_name = None
        if self._loaded_preset_name == name:
            self._loaded_preset_name = None
        self.config_panel.preset_name_edit.clear()
        self._populate_saved_presets(selected_name=None)
        self.append_log(TEXT[self.owner.language]["auto_lock_preset_deleted"].format(name=name))
        QMessageBox.information(
            self,
            TEXT[self.owner.language]["auto_lock_preset_delete_success_title"],
            TEXT[self.owner.language]["auto_lock_preset_deleted"].format(name=name),
        )

    def load_selected_preset(self, name: str | None = None) -> None:
        selected = (name or self._selected_preset_name or "").strip()
        name = selected
        if not name:
            return
        self._load_preset_store(force=True)
        payload = self._preset_store.get(name)
        if not isinstance(payload, dict):
            return
        result = QMessageBox.question(
            self,
            TEXT[self.owner.language]["auto_lock_preset_switch_confirm_title"],
            TEXT[self.owner.language]["auto_lock_preset_switch_confirm_body"].format(name=name),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if result != QMessageBox.Yes:
            return
        self._selected_preset_name = name
        self._apply_preset_payload(payload)
        self.config_panel.preset_name_edit.setText(name)
        if self.owner.service.is_connected and self.owner.pending_future is None:
            queued = self.owner._run_task(
                lambda preset_payload=payload: self.owner.service.apply_auto_lock_preset(preset_payload),
                self.owner._on_snapshot_updated,
            )
            if not queued:
                self.append_log(TEXT[self.owner.language]["auto_lock_preset_apply_busy"].format(name=name))
                return
        self.append_log(TEXT[self.owner.language]["auto_lock_preset_loaded"].format(name=name))
        self._loaded_preset_name = name
        self._refresh_preset_button_states()
        self._refresh_selected_preset_details()
        QMessageBox.information(
            self,
            TEXT[self.owner.language]["auto_lock_preset_load_success_title"],
            TEXT[self.owner.language]["auto_lock_preset_loaded"].format(name=name),
        )

    def _show_preset_scope_help(self) -> None:
        t = TEXT[self.owner.language]
        body = "\n".join(
            (
                t["auto_lock_preset_scope_hint"],
                "",
                t["auto_lock_preset_scope_saved_header"],
                f"- {t['auto_lock_preset_scope_saved_item_links']}",
                f"- {t['auto_lock_preset_scope_saved_item_workflow']}",
                f"- {t['auto_lock_preset_scope_saved_item_candidate']}",
                f"- {t['auto_lock_preset_scope_saved_item_runtime']}",
                "",
                t["auto_lock_preset_scope_not_saved_header"],
                f"- {t['auto_lock_preset_scope_not_saved_item_runtime_status']}",
                f"- {t['auto_lock_preset_scope_not_saved_item_scope']}",
                f"- {t['auto_lock_preset_scope_not_saved_item_candidates']}",
                f"- {t['auto_lock_preset_scope_not_saved_item_target']}",
                f"- {t['auto_lock_preset_scope_not_saved_item_templates']}",
            )
        )
        QMessageBox.information(self, t["auto_lock_preset_scope_title"], body)

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

    def _collect_preset_payload(self) -> dict[str, object]:
        return {
            "strategy": self.config_panel.strategy_combo.currentData(),
            "pre_scan_duration_ms": int(self.config_panel.pre_scan_duration_spin.value()),
            "pre_scan_shrink_percent": int(self.config_panel.pre_scan_shrink_percent_spin.value()),
            "search_interval_ms": int(self.config_panel.search_interval_spin.value()),
            "settle_delay_ms": int(self.config_panel.settle_delay_spin.value()),
            "lock_timeout_ms": int(self.config_panel.lock_timeout_spin.value()),
            "monitor_interval_ms": int(self.config_panel.monitor_interval_spin.value()),
            "reacquire_delay_ms": int(self.config_panel.reacquire_delay_spin.value()),
            "auto_enable_scan": bool(self.config_panel.auto_enable_scan_check.isChecked()),
            "watch_after_lock": bool(self.config_panel.watch_after_lock_check.isChecked()),
            "error_signal": self.config_panel.error_signal_combo.currentData(),
            "falc_selection": self.config_panel.falc_selection_combo.currentData(),
            "falc_path": self.config_panel.falc_path_combo.currentData(),
            "candidate_top": bool(self.config_panel.candidate_top_check.isChecked()),
            "candidate_bottom": bool(self.config_panel.candidate_bottom_check.isChecked()),
            "candidate_positive_edge": bool(self.config_panel.candidate_positive_edge_check.isChecked()),
            "candidate_negative_edge": bool(self.config_panel.candidate_negative_edge_check.isChecked()),
            "candidate_edge_level": float(self.config_panel.candidate_edge_level_spin.value()),
            "candidate_peak_noise_tolerance": float(self.config_panel.candidate_peak_noise_tolerance_spin.value()),
            "candidate_edge_min_distance": int(self.config_panel.candidate_edge_min_distance_spin.value()),
            "candidate_top_of_fringe_low_pass": bool(
                self.config_panel.candidate_top_of_fringe_low_pass_check.isChecked()
            ),
        }

    def _apply_preset_payload(self, payload: dict[str, object]) -> None:
        self._set_combo_by_data(self.config_panel.strategy_combo, payload.get("strategy"))
        self.config_panel.pre_scan_duration_spin.setValue(int(payload.get("pre_scan_duration_ms", 10_000)))
        self.config_panel.pre_scan_shrink_percent_spin.setValue(int(payload.get("pre_scan_shrink_percent", 20)))
        self.config_panel.search_interval_spin.setValue(int(payload.get("search_interval_ms", 400)))
        self.config_panel.settle_delay_spin.setValue(int(payload.get("settle_delay_ms", 250)))
        self.config_panel.lock_timeout_spin.setValue(int(payload.get("lock_timeout_ms", 4_000)))
        self.config_panel.monitor_interval_spin.setValue(int(payload.get("monitor_interval_ms", 500)))
        self.config_panel.reacquire_delay_spin.setValue(int(payload.get("reacquire_delay_ms", 800)))
        self.config_panel.auto_enable_scan_check.setChecked(bool(payload.get("auto_enable_scan", True)))
        self.config_panel.watch_after_lock_check.setChecked(bool(payload.get("watch_after_lock", True)))
        self._set_combo_by_data(self.config_panel.error_signal_combo, payload.get("error_signal"))
        self._set_combo_by_data(self.config_panel.falc_selection_combo, payload.get("falc_selection"))
        self._set_combo_by_data(self.config_panel.falc_path_combo, payload.get("falc_path"))
        self.config_panel.candidate_top_check.setChecked(bool(payload.get("candidate_top", True)))
        self.config_panel.candidate_bottom_check.setChecked(bool(payload.get("candidate_bottom", False)))
        self.config_panel.candidate_positive_edge_check.setChecked(bool(payload.get("candidate_positive_edge", True)))
        self.config_panel.candidate_negative_edge_check.setChecked(bool(payload.get("candidate_negative_edge", False)))
        self.config_panel.candidate_edge_level_spin.setValue(float(payload.get("candidate_edge_level", 0.0)))
        self.config_panel.candidate_peak_noise_tolerance_spin.setValue(
            float(payload.get("candidate_peak_noise_tolerance", 0.0))
        )
        self.config_panel.candidate_edge_min_distance_spin.setValue(
            int(payload.get("candidate_edge_min_distance", 0))
        )
        self.config_panel.candidate_top_of_fringe_low_pass_check.setChecked(
            bool(payload.get("candidate_top_of_fringe_low_pass", False))
        )

    def _load_preset_store(self, force: bool = False) -> None:
        if self._preset_store and not force:
            return
        if not self.PRESET_PATH.exists():
            self._preset_store = {}
            return
        try:
            data = json.loads(self.PRESET_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._preset_store = {}
            return
        self._preset_store = data if isinstance(data, dict) else {}

    def _populate_saved_presets(self, selected_name: str | None = None) -> None:
        self._load_preset_store(force=True)
        current = selected_name if selected_name is not None else self._selected_preset_name
        self._selected_preset_name = current if current in self._preset_store else None
        self._rebuild_preset_buttons()
        self._refresh_selected_preset_details()

    def _rebuild_preset_buttons(self) -> None:
        layout = self.config_panel.preset_button_grid
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._preset_buttons.clear()

        column_count = self._preset_button_column_count()
        self._preset_button_columns = column_count
        for index, name in enumerate(sorted(self._preset_store)):
            button = QPushButton(name)
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, preset_name=name: self._on_preset_button_clicked(preset_name))
            row = index // column_count
            col = index % column_count
            layout.addWidget(button, row, col)
            self._preset_buttons[name] = button
        self._refresh_preset_button_states()

    def _on_preset_button_clicked(self, name: str) -> None:
        current_name = self._selected_preset_name
        if current_name == name:
            self._refresh_preset_button_states()
            return
        self._selected_preset_name = name
        self.config_panel.preset_name_edit.setText(name)
        self._refresh_preset_button_states()
        self._refresh_selected_preset_details()

    def _refresh_preset_button_states(self) -> None:
        for name, button in self._preset_buttons.items():
            checked = name == self._selected_preset_name
            button.blockSignals(True)
            button.setChecked(checked)
            button.blockSignals(False)
        self.config_panel.preset_load_button.setEnabled(self._selected_preset_name is not None)
        self.config_panel.preset_delete_button.setEnabled(self._selected_preset_name is not None)
        self._refresh_loaded_preset_display()

    def _refresh_loaded_preset_display(self) -> None:
        t = TEXT[self.owner.language]
        name = (self._loaded_preset_name or "").strip()
        self.config_panel.preset_selected_value.setText(name or t["auto_lock_preset_selected_none"])

    def _refresh_selected_preset_details(self) -> None:
        name = (self._selected_preset_name or "").strip()
        if not name:
            self._render_preset_detail_cards(None, self._collect_preset_payload())
            return
        self._load_preset_store(force=True)
        payload = self._preset_store.get(name)
        if not isinstance(payload, dict):
            self._render_preset_detail_cards(None, self._collect_preset_payload())
            return
        self._render_preset_detail_cards(name, payload)

    def _build_preset_detail_sections(self, name: str | None, payload: dict[str, object]) -> list[tuple[str, list[str]]]:
        t = TEXT[self.owner.language]
        strategy_text = self._combo_label_for_data(self.config_panel.strategy_combo, payload.get("strategy"))
        error_signal_text = self._combo_label_for_data(self.config_panel.error_signal_combo, payload.get("error_signal"))
        falc_selection_text = self._combo_label_for_data(
            self.config_panel.falc_selection_combo,
            payload.get("falc_selection"),
        )
        falc_path_text = self._combo_label_for_data(self.config_panel.falc_path_combo, payload.get("falc_path"))
        title = f"{t['auto_lock_preset_name']}: {name}" if name else t["auto_lock_preset_scope_current_title"]
        return [
            (
                title,
                [
                    t["auto_lock_preset_scope_hint"],
                ],
            ),
            (
                t["auto_lock_preset_saved_values_header"],
                [
                    f"{t['auto_lock_strategy']}: {strategy_text}",
                    f"{t['auto_lock_pre_scan_duration']}: {int(payload.get('pre_scan_duration_ms', 10000))} ms",
                    f"{t['auto_lock_pre_scan_shrink_percent']}: {int(payload.get('pre_scan_shrink_percent', 20))} %",
                    f"{t['lock_error_input_signal']}: {error_signal_text}",
                    f"{t['lock_falc_selection']}: {falc_selection_text}",
                    f"{t['falc_path_selection']}: {falc_path_text}",
                ],
            ),
            (
                t["auto_lock_basic_section"],
                [
                    f"{t['auto_lock_search_interval']}: {int(payload.get('search_interval_ms', 400))} ms",
                    f"{t['auto_lock_settle_delay']}: {int(payload.get('settle_delay_ms', 250))} ms",
                    f"{t['auto_lock_lock_timeout']}: {int(payload.get('lock_timeout_ms', 4000))} ms",
                    f"{t['auto_lock_monitor_interval']}: {int(payload.get('monitor_interval_ms', 500))} ms",
                    f"{t['auto_lock_reacquire_delay']}: {int(payload.get('reacquire_delay_ms', 800))} ms",
                ],
            ),
            (
                t["lock_candidate_filter"],
                [
                    (
                        f"Top={self._bool_text(bool(payload.get('candidate_top', False)))}  "
                        f"Bottom={self._bool_text(bool(payload.get('candidate_bottom', False)))}"
                    ),
                    (
                        f"+Edge={self._bool_text(bool(payload.get('candidate_positive_edge', False)))}  "
                        f"-Edge={self._bool_text(bool(payload.get('candidate_negative_edge', False)))}"
                    ),
                    f"{t['lock_candidate_edge_level']}={float(payload.get('candidate_edge_level', 0.0)):.6f}",
                    (
                        f"{t['lock_candidate_peak_noise_tolerance']}"
                        f"={float(payload.get('candidate_peak_noise_tolerance', 0.0)):.6f}"
                    ),
                    f"{t['lock_candidate_edge_min_distance']}={int(payload.get('candidate_edge_min_distance', 0))}",
                    (
                        f"{t['lock_candidate_top_of_fringe_low_pass']}"
                        f"={self._bool_text(bool(payload.get('candidate_top_of_fringe_low_pass', False)))}"
                    ),
                ],
            ),
            (
                t["auto_lock_advanced_section"],
                [
                    f"{t['auto_lock_auto_enable_scan']}: {self._bool_text(bool(payload.get('auto_enable_scan', True)))}",
                    f"{t['auto_lock_watch_after_lock']}: {self._bool_text(bool(payload.get('watch_after_lock', True)))}",
                ],
            ),
        ]

    def _render_preset_detail_cards(self, name: str | None, payload: dict[str, object]) -> None:
        layout = self.config_panel.preset_details_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        sections = self._build_preset_detail_sections(name, payload)
        column_count = self._preset_detail_column_count()
        scale = self._ui_scale()
        for index, (title, lines) in enumerate(sections):
            card = QFrame()
            card.setObjectName("LaserPanel")
            card_layout = QVBoxLayout(card)
            card_margin = round(10 * scale)
            card_layout.setContentsMargins(card_margin, card_margin, card_margin, card_margin)
            card_layout.setSpacing(round(6 * scale))

            title_label = QLabel(title)
            title_label.setObjectName("SectionTitle")
            card_layout.addWidget(title_label)

            for line in lines:
                value_label = QLabel(line)
                value_label.setWordWrap(True)
                value_label.setObjectName("SubtleHint")
                card_layout.addWidget(value_label)

            row = index // column_count
            col = index % column_count
            layout.addWidget(card, row, col)

        for col in range(column_count):
            layout.setColumnStretch(col, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._preset_buttons and self._preset_button_columns != self._preset_button_column_count():
            self._rebuild_preset_buttons()
        self._refresh_selected_preset_details()

    def _preset_detail_column_count(self) -> int:
        scale = self._ui_scale()
        side_offset = round(220 * scale)
        available_width = max(self.config_panel.preset_details_container.width(), self.width() - side_offset) / scale
        if available_width >= 1500:
            return 4
        if available_width >= 1120:
            return 3
        if available_width >= 760:
            return 2
        return 1

    def _preset_button_column_count(self) -> int:
        scale = self._ui_scale()
        available_width = max(self.config_panel.preset_button_container.width(), self.width() - round(220 * scale)) / scale
        if available_width >= 900:
            return 4
        if available_width >= 640:
            return 3
        if available_width >= 420:
            return 2
        return 1

    def _ui_scale(self) -> float:
        manager = getattr(self.owner, "scale_manager", None)
        if manager is None:
            return 1.0
        return max(float(manager.scale), 0.01)

    @staticmethod
    def _set_combo_by_data(combo, value) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _populate_combo_options(self, combo, options, language: str) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in options:
            combo.addItem(TEXT[language][text_key], value)
        if current is not None:
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)
        self._fit_combo_popup_width(combo)

    @staticmethod
    def _sync_combo(combo, value: int) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    @staticmethod
    def _sync_check(widget, value: bool) -> None:
        widget.blockSignals(True)
        widget.setChecked(value)
        widget.blockSignals(False)

    @staticmethod
    def _set_spin_if_idle(spinbox, value: float) -> None:
        sync_from_device = getattr(spinbox, "sync_from_device", None)
        if callable(sync_from_device):
            sync_from_device(value)
            return
        if spinbox.hasFocus():
            return
        spinbox.blockSignals(True)
        spinbox.setValue(value)
        spinbox.blockSignals(False)

    @staticmethod
    def _fit_combo_popup_width(combo) -> None:
        metrics = combo.fontMetrics()
        widths = [metrics.horizontalAdvance(combo.itemText(i)) for i in range(combo.count())]
        current_width = metrics.horizontalAdvance(combo.currentText()) if combo.currentText() else 0
        content_width = max(widths + [current_width, 180])
        popup_width = content_width + 56
        combo.view().setMinimumWidth(popup_width)
        combo.setMinimumWidth(min(max(popup_width, 220), 360))

    @staticmethod
    def _combo_label_for_data(combo, value) -> str:
        index = combo.findData(value)
        if index >= 0:
            return combo.itemText(index)
        return str(value)

    def _bool_text(self, value: bool) -> str:
        t = TEXT[self.owner.language]
        return t["enabled_state"] if value else t["disabled_state"]

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
