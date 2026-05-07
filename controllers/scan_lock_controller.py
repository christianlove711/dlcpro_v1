from __future__ import annotations

from ui_text import LOCK_INPUT_SIGNAL_OPTIONS, LOCK_PID_SELECTION_OPTIONS, LOCK_TYPE_OPTIONS, PID_OUTPUT_CHANNEL_OPTIONS, TEXT


class ScanLockController:
    def __init__(self, owner) -> None:
        self.owner = owner

    def apply_texts(self) -> None:
        owner = self.owner
        t = TEXT[owner.language]

        owner.scan_lock_group.setTitle(t["scan_lock"])
        owner.scan_lock_page_title.setText(t["scan_lock"])
        owner.scan_lock_window.setWindowTitle(f"{t['window_title']} - {t['scan_lock']}")

        owner.sc_label.setText(t["scan_control"])
        owner.scan_amplitude_label.setText(t["scan_amplitude"])
        owner.scan_offset_label.setText(t["scan_offset"])
        owner.scan_output_label.setText(t["scan_output"])
        owner.scan_frequency_label.setText(t["scan_frequency"])
        owner.scan_shape_label.setText(t["scan_shape"])
        owner.lock_settings_label.setText(t["lock_settings"])
        owner.lock_input_signal_label.setText(t["lock_input_signal"])
        owner.lock_type_label.setText(t["lock_type"])
        owner.lock_pid_selection_label.setText(t["pid_selection"])
        owner.lock_without_lockpoint_label.setText(t["lock_without_lockpoint"])
        self._apply_scan_unit_suffixes(t["voltage_unit"])
        self._populate_combo(owner.lock_input_signal_combo, LOCK_INPUT_SIGNAL_OPTIONS)
        self._populate_combo(owner.lock_type_combo, LOCK_TYPE_OPTIONS)
        self._populate_combo(owner.lock_pid_selection_combo, LOCK_PID_SELECTION_OPTIONS)
        self._populate_combo(owner.pid1_output_channel_combo, PID_OUTPUT_CHANNEL_OPTIONS)
        self._populate_combo(owner.pid2_output_channel_combo, PID_OUTPUT_CHANNEL_OPTIONS)
        owner.pid1_title_label.setText(t["pid1_section"])
        owner.pid2_title_label.setText(t["pid2_section"])
        self._apply_pid_texts("pid1")
        self._apply_pid_texts("pid2")

        if owner.snapshot is None:
            owner._update_toggle_button(owner.sc_enable_button, False)
            owner._update_toggle_button(owner.lock_enable_button, False)
            owner._update_toggle_button(owner.lock_hold_button, False)
            owner.lock_without_lockpoint_check.blockSignals(True)
            owner.lock_without_lockpoint_check.setChecked(False)
            owner.lock_without_lockpoint_check.blockSignals(False)
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
        owner._update_toggle_button(owner.sc_enable_button, snapshot.sc_enabled)
        self._sync_combo(owner.lock_input_signal_combo, snapshot.lock_input_channel)
        self._sync_combo(owner.lock_type_combo, snapshot.lock_type)
        self._sync_combo(owner.lock_pid_selection_combo, snapshot.lock_pid_selection)
        owner._update_toggle_button(owner.lock_enable_button, snapshot.lock_enabled)
        owner._update_toggle_button(owner.lock_hold_button, snapshot.lock_hold)
        owner.lock_without_lockpoint_check.blockSignals(True)
        owner.lock_without_lockpoint_check.setChecked(snapshot.lock_without_lockpoint)
        owner.lock_without_lockpoint_check.blockSignals(False)
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

        getattr(owner, f"{pid_name}_gain_spin").blockSignals(True)
        getattr(owner, f"{pid_name}_gain_spin").setValue(getattr(snapshot, f"{pid_name}_gain_all"))
        getattr(owner, f"{pid_name}_gain_spin").blockSignals(False)
        getattr(owner, f"{pid_name}_p_spin").blockSignals(True)
        getattr(owner, f"{pid_name}_p_spin").setValue(getattr(snapshot, f"{pid_name}_gain_p"))
        getattr(owner, f"{pid_name}_p_spin").blockSignals(False)
        getattr(owner, f"{pid_name}_i_spin").blockSignals(True)
        getattr(owner, f"{pid_name}_i_spin").setValue(getattr(snapshot, f"{pid_name}_gain_i"))
        getattr(owner, f"{pid_name}_i_spin").blockSignals(False)
        getattr(owner, f"{pid_name}_d_spin").blockSignals(True)
        getattr(owner, f"{pid_name}_d_spin").setValue(getattr(snapshot, f"{pid_name}_gain_d"))
        getattr(owner, f"{pid_name}_d_spin").blockSignals(False)
        getattr(owner, f"{pid_name}_limit_spin").blockSignals(True)
        getattr(owner, f"{pid_name}_limit_spin").setValue(getattr(snapshot, f"{pid_name}_limit_max"))
        getattr(owner, f"{pid_name}_limit_spin").blockSignals(False)
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
            owner.pid1_i_cutoff_spin.blockSignals(True)
            owner.pid1_i_cutoff_spin.setValue(snapshot.pid1_i_cutoff)
            owner.pid1_i_cutoff_spin.blockSignals(False)

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

    @staticmethod
    def _pid_unit_kind(output_channel: int) -> str:
        if output_channel == 51:
            return "current"
        return "voltage"

    @staticmethod
    def _set_spin_if_idle(spinbox, value: float) -> None:
        if spinbox.hasFocus():
            return
        spinbox.blockSignals(True)
        spinbox.setValue(value)
        spinbox.blockSignals(False)
