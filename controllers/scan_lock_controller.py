from __future__ import annotations

from ui_text import (
    LOCK_ERROR_SIGNAL_OPTIONS,
    LOCK_FALC_SELECTION_OPTIONS,
    LOCK_INPUT_SIGNAL_OPTIONS,
    LOCK_PID_SELECTION_OPTIONS,
    LOCK_TYPE_OPTIONS,
    PID_OUTPUT_CHANNEL_OPTIONS,
    TEXT,
)


class ScanLockController:
    def __init__(self, owner) -> None:
        self.owner = owner

    def _snapshot(self):
        if not self.owner.service.is_connected:
            return None
        return self.owner.snapshot

    def _submit(self, fn) -> bool:
        return self.owner.submit_device_task(fn)

    def _toggle(self, guard_attr: str, snapshot_attr: str, setter, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is None or getattr(self.owner, guard_attr) or checked == getattr(snapshot, snapshot_attr):
            return
        self._submit(lambda: setter(checked))

    def _spin(self, guard_attr: str, snapshot_attr: str, widget, setter, tolerance: float = 1e-9) -> None:
        snapshot = self._snapshot()
        if snapshot is None or getattr(self.owner, guard_attr):
            return
        value = widget.value()
        if abs(value - getattr(snapshot, snapshot_attr)) < tolerance:
            return
        self._submit(lambda: setter(value))

    def _combo(self, guard_attr: str, snapshot_attr: str, combo, setter) -> None:
        snapshot = self._snapshot()
        if snapshot is None or getattr(self.owner, guard_attr):
            return
        value = int(combo.currentData())
        if value == getattr(snapshot, snapshot_attr):
            return
        self._submit(lambda: setter(value))

    def _check(self, snapshot_attr: str, checkbox, setter) -> None:
        snapshot = self._snapshot()
        if snapshot is None or self.owner.lock_programmatic_update:
            return
        checked = checkbox.isChecked()
        if checked == getattr(snapshot, snapshot_attr):
            return
        self._submit(lambda: setter(checked))

    def _on_sc_enable_toggled(self, checked: bool) -> None:
        self._toggle("sc_programmatic_update", "sc_enabled", self.owner.service.set_sc_enabled, checked)

    def _on_sc_amplitude_finished(self) -> None:
        self._spin(
            "sc_programmatic_update",
            "sc_amplitude",
            self.owner.scan_amplitude_spin,
            self.owner.service.set_sc_amplitude,
        )

    def _on_sc_offset_finished(self) -> None:
        self._spin(
            "sc_programmatic_update",
            "sc_offset",
            self.owner.scan_offset_spin,
            self.owner.service.set_sc_offset,
        )

    def _on_sc_output_changed(self) -> None:
        self._combo(
            "sc_programmatic_update",
            "sc_output_channel",
            self.owner.scan_output_combo,
            self.owner.service.set_sc_output_channel,
        )

    def _on_sc_frequency_finished(self) -> None:
        self._spin(
            "sc_programmatic_update",
            "sc_frequency",
            self.owner.scan_frequency_spin,
            self.owner.service.set_sc_frequency,
        )

    def _on_sc_shape_changed(self) -> None:
        self._combo(
            "sc_programmatic_update",
            "sc_signal_type",
            self.owner.scan_shape_combo,
            self.owner.service.set_sc_signal_type,
        )

    def _on_lock_enabled_toggled(self, checked: bool) -> None:
        self._toggle("lock_programmatic_update", "lock_enabled", self.owner.service.set_lock_enabled, checked)

    def _on_lock_hold_toggled(self, checked: bool) -> None:
        self._toggle("lock_programmatic_update", "lock_hold", self.owner.service.set_lock_hold, checked)

    def _on_lock_input_signal_changed(self) -> None:
        self._combo(
            "lock_programmatic_update",
            "lock_input_channel",
            self.owner.lock_input_signal_combo,
            self.owner.service.set_lock_input_channel,
        )

    def _on_lock_error_signal_changed(self) -> None:
        self._combo(
            "lock_programmatic_update",
            "lock_error_channel",
            self.owner.lock_error_signal_combo,
            self.owner.service.set_lock_error_channel,
        )

    def _on_lock_type_changed(self) -> None:
        self._combo(
            "lock_programmatic_update",
            "lock_type",
            self.owner.lock_type_combo,
            self.owner.service.set_lock_type,
        )

    def _on_lock_pid_selection_changed(self) -> None:
        self._combo(
            "lock_programmatic_update",
            "lock_pid_selection",
            self.owner.lock_pid_selection_combo,
            self.owner.service.set_lock_pid_selection,
        )

    def _on_lock_falc_selection_changed(self) -> None:
        self._combo(
            "lock_programmatic_update",
            "lock_falc_selection",
            self.owner.lock_falc_selection_combo,
            self.owner.service.set_lock_falc_selection,
        )

    def _on_lock_without_lockpoint_changed(self) -> None:
        self._check(
            "lock_without_lockpoint",
            self.owner.lock_without_lockpoint_check,
            self.owner.service.set_lock_without_lockpoint,
        )

    def _on_lock_candidate_top_changed(self, checked: bool) -> None:
        self._toggle(
            "lock_programmatic_update",
            "lock_candidate_top_enabled",
            self.owner.service.set_lock_candidate_top_enabled,
            checked,
        )

    def _on_lock_candidate_bottom_changed(self, checked: bool) -> None:
        self._toggle(
            "lock_programmatic_update",
            "lock_candidate_bottom_enabled",
            self.owner.service.set_lock_candidate_bottom_enabled,
            checked,
        )

    def _on_lock_candidate_positive_edge_changed(self, checked: bool) -> None:
        self._toggle(
            "lock_programmatic_update",
            "lock_candidate_positive_edge_enabled",
            self.owner.service.set_lock_candidate_positive_edge_enabled,
            checked,
        )

    def _on_lock_candidate_negative_edge_changed(self, checked: bool) -> None:
        self._toggle(
            "lock_programmatic_update",
            "lock_candidate_negative_edge_enabled",
            self.owner.service.set_lock_candidate_negative_edge_enabled,
            checked,
        )

    def _on_lock_candidate_edge_level_finished(self) -> None:
        self._spin(
            "lock_programmatic_update",
            "lock_candidate_edge_level",
            self.owner.lock_candidate_edge_level_spin,
            self.owner.service.set_lock_candidate_edge_level,
            tolerance=1e-12,
        )

    def _on_lock_candidate_peak_noise_tolerance_finished(self) -> None:
        self._spin(
            "lock_programmatic_update",
            "lock_candidate_peak_noise_tolerance",
            self.owner.lock_candidate_peak_noise_tolerance_spin,
            self.owner.service.set_lock_candidate_peak_noise_tolerance,
            tolerance=1e-12,
        )

    def _on_lock_candidate_edge_min_distance_finished(self) -> None:
        self._spin(
            "lock_programmatic_update",
            "lock_candidate_edge_min_distance",
            self.owner.lock_candidate_edge_min_distance_spin,
            self.owner.service.set_lock_candidate_edge_min_distance,
            tolerance=0.5,
        )

    def _on_lock_candidate_top_of_fringe_low_pass_changed(self, checked: bool) -> None:
        self._toggle(
            "lock_programmatic_update",
            "lock_candidate_top_of_fringe_low_pass",
            self.owner.service.set_lock_candidate_top_of_fringe_low_pass,
            checked,
        )

    def _on_pid1_gain_finished(self) -> None:
        self._pid_spin("pid1_gain_all", self.owner.pid1_gain_spin, self.owner.service.set_pid1_gain_all)

    def _on_pid1_p_finished(self) -> None:
        self._pid_spin("pid1_gain_p", self.owner.pid1_p_spin, self.owner.service.set_pid1_gain_p)

    def _on_pid1_i_finished(self) -> None:
        self._pid_spin("pid1_gain_i", self.owner.pid1_i_spin, self.owner.service.set_pid1_gain_i)

    def _on_pid1_d_finished(self) -> None:
        self._pid_spin("pid1_gain_d", self.owner.pid1_d_spin, self.owner.service.set_pid1_gain_d)

    def _on_pid1_output_channel_changed(self) -> None:
        self._pid_combo("pid1_output_channel", self.owner.pid1_output_channel_combo, self.owner.service.set_pid1_output_channel)

    def _on_pid1_sign_changed(self) -> None:
        self._pid_check("pid1_sign", self.owner.pid1_sign_check, self.owner.service.set_pid1_sign)

    def _on_pid1_i_cutoff_enabled_changed(self) -> None:
        self._pid_check(
            "pid1_i_cutoff_enabled",
            self.owner.pid1_use_i_cutoff_check,
            self.owner.service.set_pid1_i_cutoff_enabled,
        )

    def _on_pid1_i_cutoff_finished(self) -> None:
        self._pid_spin("pid1_i_cutoff", self.owner.pid1_i_cutoff_spin, self.owner.service.set_pid1_i_cutoff)

    def _on_pid1_limit_enabled_changed(self) -> None:
        self._pid_check("pid1_limit_enabled", self.owner.pid1_use_limit_check, self.owner.service.set_pid1_limit_enabled)

    def _on_pid1_limit_finished(self) -> None:
        self._pid_spin("pid1_limit_max", self.owner.pid1_limit_spin, self.owner.service.set_pid1_limit_max)

    def _on_pid1_enabled_changed(self) -> None:
        self._pid_check("pid1_enabled", self.owner.pid1_enable_check, self.owner.service.set_pid1_enabled)

    def _on_pid2_gain_finished(self) -> None:
        self._pid_spin("pid2_gain_all", self.owner.pid2_gain_spin, self.owner.service.set_pid2_gain_all)

    def _on_pid2_p_finished(self) -> None:
        self._pid_spin("pid2_gain_p", self.owner.pid2_p_spin, self.owner.service.set_pid2_gain_p)

    def _on_pid2_i_finished(self) -> None:
        self._pid_spin("pid2_gain_i", self.owner.pid2_i_spin, self.owner.service.set_pid2_gain_i)

    def _on_pid2_d_finished(self) -> None:
        self._pid_spin("pid2_gain_d", self.owner.pid2_d_spin, self.owner.service.set_pid2_gain_d)

    def _on_pid2_output_channel_changed(self) -> None:
        self._pid_combo("pid2_output_channel", self.owner.pid2_output_channel_combo, self.owner.service.set_pid2_output_channel)

    def _on_pid2_sign_changed(self) -> None:
        self._pid_check("pid2_sign", self.owner.pid2_sign_check, self.owner.service.set_pid2_sign)

    def _on_pid2_limit_enabled_changed(self) -> None:
        self._pid_check("pid2_limit_enabled", self.owner.pid2_use_limit_check, self.owner.service.set_pid2_limit_enabled)

    def _on_pid2_limit_finished(self) -> None:
        self._pid_spin("pid2_limit_max", self.owner.pid2_limit_spin, self.owner.service.set_pid2_limit_max)

    def _on_pid2_enabled_changed(self) -> None:
        self._pid_check("pid2_enabled", self.owner.pid2_enable_check, self.owner.service.set_pid2_enabled)

    def _pid_spin(self, snapshot_attr: str, spinbox, setter) -> None:
        self._spin("lock_programmatic_update", snapshot_attr, spinbox, setter)

    def _pid_combo(self, snapshot_attr: str, combo, setter) -> None:
        self._combo("lock_programmatic_update", snapshot_attr, combo, setter)

    def _pid_check(self, snapshot_attr: str, checkbox, setter) -> None:
        self._check(snapshot_attr, checkbox, setter)

    def apply_texts(self) -> None:
        owner = self.owner
        t = TEXT[owner.language]

        owner.scan_lock_group.setTitle(t["scan_lock"])
        owner.scan_lock_page_title.setText(t["scan_lock"])
        owner.scan_lock_window.setWindowTitle(f"{t['window_title']} - {t['scan_lock']}")

        owner.sc_label.setText(t["scan_control"])
        owner.sc_precision_label.setText(t["step_precision"])
        owner.scan_amplitude_label.setText(t["scan_amplitude"])
        owner.scan_offset_label.setText(t["scan_offset"])
        owner.scan_output_label.setText(t["scan_output"])
        owner.scan_frequency_label.setText(t["scan_frequency"])
        owner.scan_shape_label.setText(t["scan_shape"])
        owner.lock_settings_label.setText(t["lock_settings"])
        owner.lock_input_signal_label.setText(t["lock_input_signal"])
        owner.lock_error_signal_label.setText(t["lock_error_input_signal"])
        owner.lock_type_label.setText(t["lock_type"])
        owner.lock_pid_selection_label.setText(t["pid_selection"])
        owner.lock_falc_selection_label.setText(t["lock_falc_selection"])
        owner.lock_without_lockpoint_label.setText(t["lock_without_lockpoint"])
        owner.lock_status_label.setText(t["lock_status"])
        owner.lock_candidate_filter_group.setTitle(t["lock_candidate_filter"])
        owner.lock_candidate_top_check.setText(t["lock_candidate_top"])
        owner.lock_candidate_bottom_check.setText(t["lock_candidate_bottom"])
        owner.lock_candidate_positive_edge_check.setText(t["lock_candidate_positive_edge"])
        owner.lock_candidate_negative_edge_check.setText(t["lock_candidate_negative_edge"])
        owner.lock_candidate_edge_level_label.setText(t["lock_candidate_edge_level"])
        owner.lock_candidate_peak_noise_tolerance_label.setText(t["lock_candidate_peak_noise_tolerance"])
        owner.lock_candidate_edge_min_distance_label.setText(t["lock_candidate_edge_min_distance"])
        owner.lock_candidate_top_of_fringe_low_pass_label.setText(t["lock_candidate_top_of_fringe_low_pass"])
        self._apply_scan_unit_suffixes(t["voltage_unit"])
        self._populate_combo(owner.lock_input_signal_combo, LOCK_INPUT_SIGNAL_OPTIONS)
        self._populate_combo(owner.lock_error_signal_combo, LOCK_ERROR_SIGNAL_OPTIONS)
        self._populate_combo(owner.lock_type_combo, LOCK_TYPE_OPTIONS)
        self._populate_combo(owner.lock_pid_selection_combo, LOCK_PID_SELECTION_OPTIONS)
        self._populate_combo(owner.lock_falc_selection_combo, LOCK_FALC_SELECTION_OPTIONS)
        self._populate_combo(owner.pid1_output_channel_combo, PID_OUTPUT_CHANNEL_OPTIONS)
        self._populate_combo(owner.pid2_output_channel_combo, PID_OUTPUT_CHANNEL_OPTIONS)
        owner.pid1_title_label.setText(t["pid1_section"])
        owner.pid2_title_label.setText(t["pid2_section"])
        for button in owner.sc_precision_buttons:
            button.setText(t[button._text_key])
        if hasattr(owner, "pid_precision_label"):
            owner.pid_precision_label.setText(t["step_precision"])
        if hasattr(owner, "pid_precision_buttons"):
            for button in owner.pid_precision_buttons:
                button.setText(t[button._text_key])
        for module in ("sc", "pid"):
            for button in owner.module_precision_target_buttons.get(module, []):
                button.setText(t["precision_target"])
        self._apply_pid_texts("pid1")
        self._apply_pid_texts("pid2")

        if owner.snapshot is None:
            owner.update_toggle_button(owner.sc_enable_button, False)
            owner.update_toggle_button(owner.lock_enable_button, False)
            owner.update_toggle_button(owner.lock_hold_button, False)
            owner.lock_without_lockpoint_check.blockSignals(True)
            owner.lock_without_lockpoint_check.setChecked(False)
            owner.lock_without_lockpoint_check.blockSignals(False)
            owner.lock_status_value.setText(t["not_available"])
            self._reset_lock_candidate_controls()
            self._reset_pid_controls()

    def render_snapshot(self, snapshot) -> None:
        owner = self.owner
        owner.sc_programmatic_update = True
        owner.lock_programmatic_update = True

        self._apply_scan_unit_suffixes(snapshot.sc_unit)
        self._set_spin_if_idle(owner.scan_amplitude_spin, snapshot.sc_amplitude)
        self._set_spin_if_idle(owner.scan_offset_spin, snapshot.sc_offset)
        self._set_spin_if_idle(owner.scan_frequency_spin, snapshot.sc_frequency)

        self._sync_combo(owner.scan_output_combo, snapshot.sc_output_channel)
        self._sync_combo(owner.scan_shape_combo, snapshot.sc_signal_type)
        owner.update_toggle_button(owner.sc_enable_button, snapshot.sc_enabled)
        self._sync_combo(owner.lock_input_signal_combo, snapshot.lock_input_channel)
        self._sync_combo(owner.lock_error_signal_combo, snapshot.lock_error_channel)
        self._sync_combo(owner.lock_type_combo, snapshot.lock_type)
        self._sync_combo(owner.lock_pid_selection_combo, snapshot.lock_pid_selection)
        self._sync_combo(owner.lock_falc_selection_combo, snapshot.lock_falc_selection)
        owner.update_toggle_button(owner.lock_enable_button, snapshot.lock_enabled)
        owner.update_toggle_button(owner.lock_hold_button, snapshot.lock_hold)
        owner.lock_without_lockpoint_check.blockSignals(True)
        owner.lock_without_lockpoint_check.setChecked(snapshot.lock_without_lockpoint)
        owner.lock_without_lockpoint_check.blockSignals(False)
        owner.lock_status_value.setText(snapshot.lock_state_txt or TEXT[owner.language]["not_available"])
        self._render_lock_candidate_controls(snapshot)
        self._render_pid("pid1", snapshot)
        self._render_pid("pid2", snapshot)

        owner.sc_programmatic_update = False
        owner.lock_programmatic_update = False

    @staticmethod
    def _sync_combo(combo, value: int) -> None:
        if combo.view().isVisible() or combo.hasFocus():
            return
        index = combo.findData(value)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _apply_scan_unit_suffixes(self, unit: str) -> None:
        owner = self.owner
        amplitude_unit = TEXT[owner.language]["scan_amplitude_unit"]
        base_unit = unit or TEXT[owner.language]["voltage_unit"]
        if base_unit != TEXT[owner.language]["voltage_unit"]:
            amplitude_unit = f"{base_unit} pp"
        owner.scan_amplitude_spin.setSuffix(f" {amplitude_unit}")
        owner.scan_offset_spin.setSuffix(f" {base_unit}")
        owner.scan_frequency_spin.setSuffix(" Hz")

    def _populate_combo(self, combo, options) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in options:
            combo.addItem(TEXT[self.owner.language][text_key], value)
        if current is not None:
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _apply_pid_texts(self, pid_name: str) -> None:
        owner = self.owner
        t = TEXT[owner.language]
        getattr(owner, f"{pid_name}_gain_label").setText(t["pid_gain"])
        getattr(owner, f"{pid_name}_p_label").setText(t["pid_p"])
        getattr(owner, f"{pid_name}_i_label").setText(t["pid_i"])
        getattr(owner, f"{pid_name}_d_label").setText(t["pid_d"])
        getattr(owner, f"{pid_name}_output_channel_label").setText(t["pid_output_channel"])
        getattr(owner, f"{pid_name}_sign_label").setText(t["pid_sign_positive"])
        getattr(owner, f"{pid_name}_use_i_cutoff_label").setText(t["pid_use_i_cutoff"])
        getattr(owner, f"{pid_name}_use_limit_label").setText(t["pid_use_limit"])
        getattr(owner, f"{pid_name}_enable_label").setText(t["pid_enable"])

    def _render_pid(self, pid_name: str, snapshot) -> None:
        owner = self.owner
        unit_kind = self._pid_unit_kind(getattr(snapshot, f"{pid_name}_output_channel"))

        self._set_spin_if_idle(getattr(owner, f"{pid_name}_gain_spin"), getattr(snapshot, f"{pid_name}_gain_all"))
        self._set_spin_if_idle(getattr(owner, f"{pid_name}_p_spin"), getattr(snapshot, f"{pid_name}_gain_p"))
        self._set_spin_if_idle(getattr(owner, f"{pid_name}_i_spin"), getattr(snapshot, f"{pid_name}_gain_i"))
        self._set_spin_if_idle(getattr(owner, f"{pid_name}_d_spin"), getattr(snapshot, f"{pid_name}_gain_d"))
        self._set_spin_if_idle(getattr(owner, f"{pid_name}_limit_spin"), getattr(snapshot, f"{pid_name}_limit_max"))
        self._sync_combo(getattr(owner, f"{pid_name}_output_channel_combo"), getattr(snapshot, f"{pid_name}_output_channel"))
        getattr(owner, f"{pid_name}_sign_check").blockSignals(True)
        getattr(owner, f"{pid_name}_sign_check").setChecked(getattr(snapshot, f"{pid_name}_sign"))
        getattr(owner, f"{pid_name}_sign_check").blockSignals(False)
        getattr(owner, f"{pid_name}_use_limit_check").blockSignals(True)
        getattr(owner, f"{pid_name}_use_limit_check").setChecked(getattr(snapshot, f"{pid_name}_limit_enabled"))
        getattr(owner, f"{pid_name}_use_limit_check").blockSignals(False)
        getattr(owner, f"{pid_name}_enable_check").blockSignals(True)
        getattr(owner, f"{pid_name}_enable_check").setChecked(getattr(snapshot, f"{pid_name}_enabled"))
        getattr(owner, f"{pid_name}_enable_check").blockSignals(False)

        if pid_name == "pid1":
            owner.pid1_use_i_cutoff_check.blockSignals(True)
            owner.pid1_use_i_cutoff_check.setChecked(snapshot.pid1_i_cutoff_enabled)
            owner.pid1_use_i_cutoff_check.blockSignals(False)
            self._set_spin_if_idle(owner.pid1_i_cutoff_spin, snapshot.pid1_i_cutoff)

        getattr(owner, f"{pid_name}_gain_spin").setSuffix(f" {TEXT[owner.language]['pid_gain_unit_none']}")
        getattr(owner, f"{pid_name}_p_spin").setSuffix(f" {TEXT[owner.language][f'pid_p_unit_{unit_kind}']}")
        getattr(owner, f"{pid_name}_i_spin").setSuffix(f" {TEXT[owner.language][f'pid_i_unit_{unit_kind}']}")
        getattr(owner, f"{pid_name}_d_spin").setSuffix(f" {TEXT[owner.language][f'pid_d_unit_{unit_kind}']}")
        getattr(owner, f"{pid_name}_limit_spin").setSuffix(f" {TEXT[owner.language][f'pid_limit_unit_{unit_kind}']}")
        if pid_name == "pid1":
            owner.pid1_i_cutoff_spin.setSuffix(" Hz")

    def _reset_pid_controls(self) -> None:
        owner = self.owner
        for pid_name in ("pid1", "pid2"):
            for suffix_name in ("gain_spin", "p_spin", "i_spin", "d_spin", "limit_spin"):
                spin = getattr(owner, f"{pid_name}_{suffix_name}")
                spin.blockSignals(True)
                spin.setValue(0.0)
                spin.blockSignals(False)
            getattr(owner, f"{pid_name}_sign_check").blockSignals(True)
            getattr(owner, f"{pid_name}_sign_check").setChecked(False)
            getattr(owner, f"{pid_name}_sign_check").blockSignals(False)
            getattr(owner, f"{pid_name}_use_limit_check").blockSignals(True)
            getattr(owner, f"{pid_name}_use_limit_check").setChecked(False)
            getattr(owner, f"{pid_name}_use_limit_check").blockSignals(False)
            getattr(owner, f"{pid_name}_enable_check").blockSignals(True)
            getattr(owner, f"{pid_name}_enable_check").setChecked(False)
            getattr(owner, f"{pid_name}_enable_check").blockSignals(False)
        owner.pid1_use_i_cutoff_check.blockSignals(True)
        owner.pid1_use_i_cutoff_check.setChecked(False)
        owner.pid1_use_i_cutoff_check.blockSignals(False)
        owner.pid1_i_cutoff_spin.blockSignals(True)
        owner.pid1_i_cutoff_spin.setValue(0.0)
        owner.pid1_i_cutoff_spin.blockSignals(False)

    def _render_lock_candidate_controls(self, snapshot) -> None:
        owner = self.owner
        for widget_name, value in (
            ("lock_candidate_top_check", snapshot.lock_candidate_top_enabled),
            ("lock_candidate_bottom_check", snapshot.lock_candidate_bottom_enabled),
            ("lock_candidate_positive_edge_check", snapshot.lock_candidate_positive_edge_enabled),
            ("lock_candidate_negative_edge_check", snapshot.lock_candidate_negative_edge_enabled),
            ("lock_candidate_top_of_fringe_low_pass_check", snapshot.lock_candidate_top_of_fringe_low_pass),
        ):
            widget = getattr(owner, widget_name)
            widget.blockSignals(True)
            widget.setChecked(value)
            widget.blockSignals(False)
        self._set_spin_if_idle(owner.lock_candidate_edge_level_spin, snapshot.lock_candidate_edge_level)
        self._set_spin_if_idle(
            owner.lock_candidate_peak_noise_tolerance_spin,
            snapshot.lock_candidate_peak_noise_tolerance,
        )
        self._set_spin_if_idle(owner.lock_candidate_edge_min_distance_spin, snapshot.lock_candidate_edge_min_distance)
        owner.lock_candidate_edge_level_spin.setSuffix(f" {TEXT[owner.language]['voltage_unit']}")
        owner.lock_candidate_peak_noise_tolerance_spin.setSuffix(f" {TEXT[owner.language]['voltage_unit']}")

    def _reset_lock_candidate_controls(self) -> None:
        owner = self.owner
        for widget_name in (
            "lock_candidate_top_check",
            "lock_candidate_bottom_check",
            "lock_candidate_positive_edge_check",
            "lock_candidate_negative_edge_check",
            "lock_candidate_top_of_fringe_low_pass_check",
        ):
            widget = getattr(owner, widget_name)
            widget.blockSignals(True)
            widget.setChecked(False)
            widget.blockSignals(False)
        owner.lock_candidate_edge_level_spin.blockSignals(True)
        owner.lock_candidate_edge_level_spin.setValue(0.0)
        owner.lock_candidate_edge_level_spin.blockSignals(False)
        owner.lock_candidate_peak_noise_tolerance_spin.blockSignals(True)
        owner.lock_candidate_peak_noise_tolerance_spin.setValue(0.0)
        owner.lock_candidate_peak_noise_tolerance_spin.blockSignals(False)
        owner.lock_candidate_edge_min_distance_spin.blockSignals(True)
        owner.lock_candidate_edge_min_distance_spin.setValue(0)
        owner.lock_candidate_edge_min_distance_spin.blockSignals(False)

    @staticmethod
    def _pid_unit_kind(output_channel: int) -> str:
        if output_channel == 51:
            return "current"
        return "voltage"

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
