from __future__ import annotations

from ui_text import LOCK_INPUT_SIGNAL_OPTIONS, LOCK_PID_SELECTION_OPTIONS, LOCK_TYPE_OPTIONS, TEXT


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

        if owner.snapshot is None:
            owner._update_toggle_button(owner.sc_enable_button, False)
            owner._update_toggle_button(owner.lock_enable_button, False)
            owner._update_toggle_button(owner.lock_hold_button, False)
            owner.lock_without_lockpoint_check.blockSignals(True)
            owner.lock_without_lockpoint_check.setChecked(False)
            owner.lock_without_lockpoint_check.blockSignals(False)

    def render_snapshot(self, snapshot) -> None:
        owner = self.owner
        owner.sc_programmatic_update = True
        owner.lock_programmatic_update = True

        self._apply_scan_unit_suffixes(snapshot.sc_unit)
        owner.scan_amplitude_spin.blockSignals(True)
        owner.scan_amplitude_spin.setValue(snapshot.sc_amplitude)
        owner.scan_amplitude_spin.blockSignals(False)
        owner.scan_offset_spin.blockSignals(True)
        owner.scan_offset_spin.setValue(snapshot.sc_offset)
        owner.scan_offset_spin.blockSignals(False)
        owner.scan_frequency_spin.blockSignals(True)
        owner.scan_frequency_spin.setValue(snapshot.sc_frequency)
        owner.scan_frequency_spin.blockSignals(False)

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

        owner.sc_programmatic_update = False
        owner.lock_programmatic_update = False

    @staticmethod
    def _sync_combo(combo, value: int) -> None:
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
