from __future__ import annotations

from dataclasses import asdict

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QTableWidgetItem

from dlcpro_service import DeviceSnapshot
from ui_text import ARC_SIGNAL_OPTIONS, PARAMETER_LABELS, PID_OUTPUT_CHANNEL_OPTIONS, SCAN_OUTPUT_OPTIONS, SCAN_SHAPE_OPTIONS, TEXT


class LaserController:
    def __init__(self, owner) -> None:
        self.owner = owner
        self.current_apply_timer = QTimer(owner)
        self.current_apply_timer.setSingleShot(True)
        self.current_apply_timer.setInterval(150)
        self.current_apply_timer.timeout.connect(self._apply_current_if_needed)

    def shutdown(self) -> None:
        self.current_apply_timer.stop()

    def _snapshot(self):
        if not self.owner.service.is_connected:
            return None
        return self.owner.snapshot

    def _submit(self, fn, *, coalesce_key: str | None = None) -> bool:
        return self.owner.submit_device_task(fn, coalesce_key=coalesce_key)

    def _toggle(self, guard_attr: str, snapshot_attr: str, setter, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is None or getattr(self.owner, guard_attr) or checked == getattr(snapshot, snapshot_attr):
            return
        self._submit(lambda: setter(checked))

    def _spin(self, guard_attr: str, snapshot_attr: str, widget, setter) -> None:
        snapshot = self._snapshot()
        if snapshot is None or getattr(self.owner, guard_attr):
            return
        value = widget.value()
        if abs(value - getattr(snapshot, snapshot_attr)) < 1e-9:
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

    def _on_current_set_changed(self) -> None:
        owner = self.owner
        if owner.current_set_programmatic_update:
            return
        owner.current_set_dirty = True
        if owner.service.is_connected:
            self.current_apply_timer.start()

    def _on_current_set_step_applied(self) -> None:
        owner = self.owner
        if owner.current_set_programmatic_update:
            return
        owner.current_set_dirty = True
        self.current_apply_timer.stop()
        if not owner.service.is_connected:
            return
        if owner.busy or owner.task_coordinator.has_user_work:
            self.current_apply_timer.start(20)
            return
        self._apply_current_if_needed()

    def _apply_current_if_needed(self) -> None:
        owner = self.owner
        if not owner.service.is_connected or not owner.current_set_dirty:
            return
        if owner.busy or owner.task_coordinator.has_user_work:
            self.current_apply_timer.start(20)
            return
        value = owner.current_set_spin.value()
        owner.current_set_dirty = False
        if not self._submit(lambda: owner.service.set_current(value), coalesce_key="current_set"):
            owner.current_set_dirty = True
            self.current_apply_timer.start()

    def _on_current_clip_finished(self) -> None:
        owner = self.owner
        snapshot = self._snapshot()
        if snapshot is None or owner.cc_programmatic_update:
            return
        value = owner.current_clip_spin.value()
        if abs(value - snapshot.current_clip) < 1e-9:
            return
        if owner.notifier.confirm_parameter_write(
            TEXT[owner.language]["maximum_current"],
            f"{snapshot.current_clip:.5f}",
            f"{value:.5f}",
        ):
            self._submit(lambda: owner.service.set_current_clip(value))

    def _on_cc_enable_toggled(self, checked: bool) -> None:
        self._toggle("cc_programmatic_update", "cc_enabled", self.owner.service.set_cc_enabled, checked)

    def _on_feedforward_enable_toggled(self, checked: bool) -> None:
        self._toggle(
            "feedforward_programmatic_update",
            "feedforward_enabled",
            self.owner.service.set_feedforward_enabled,
            checked,
        )

    def _on_feedforward_factor_finished(self) -> None:
        self._spin(
            "feedforward_programmatic_update",
            "feedforward_factor",
            self.owner.feedforward_factor_spin,
            self.owner.service.set_feedforward_factor,
        )

    def _on_arc_enable_toggled(self, checked: bool) -> None:
        self._toggle("arc_programmatic_update", "arc_enabled", self.owner.service.set_arc_enabled, checked)

    def _on_arc_signal_changed(self) -> None:
        self._combo("arc_programmatic_update", "arc_signal", self.owner.arc_signal_combo, self.owner.service.set_arc_signal)

    def _on_arc_factor_finished(self) -> None:
        self._spin("arc_programmatic_update", "arc_factor", self.owner.arc_factor_spin, self.owner.service.set_arc_factor)

    def _on_tc_enable_toggled(self, checked: bool) -> None:
        self._toggle("tc_programmatic_update", "tc_enabled", self.owner.service.set_tc_enabled, checked)

    def _on_temp_set_finished(self) -> None:
        self._spin("tc_programmatic_update", "temp_set", self.owner.temp_set_spin, self.owner.service.set_temp_set)

    def _on_tc_arc_enable_toggled(self, checked: bool) -> None:
        self._toggle("tc_programmatic_update", "tc_arc_enabled", self.owner.service.set_tc_arc_enabled, checked)

    def _on_tc_arc_signal_changed(self) -> None:
        self._combo(
            "tc_programmatic_update",
            "tc_arc_signal",
            self.owner.tc_arc_signal_combo,
            self.owner.service.set_tc_arc_signal,
        )

    def _on_tc_arc_factor_finished(self) -> None:
        self._spin(
            "tc_programmatic_update",
            "tc_arc_factor",
            self.owner.tc_arc_factor_spin,
            self.owner.service.set_tc_arc_factor,
        )

    def _on_pc_enable_toggled(self, checked: bool) -> None:
        self._toggle("pc_programmatic_update", "pc_enabled", self.owner.service.set_pc_enabled, checked)

    def _on_pc_voltage_set_finished(self) -> None:
        self._spin(
            "pc_programmatic_update",
            "pc_voltage_set",
            self.owner.pc_voltage_set_spin,
            self.owner.service.set_pc_voltage_set,
        )

    def _on_pc_slew_rate_enable_toggled(self, checked: bool) -> None:
        self._toggle(
            "pc_programmatic_update",
            "pc_slew_rate_enabled",
            self.owner.service.set_pc_slew_rate_enabled,
            checked,
        )

    def _on_pc_slew_rate_finished(self) -> None:
        self._spin(
            "pc_programmatic_update",
            "pc_slew_rate",
            self.owner.pc_slew_rate_spin,
            self.owner.service.set_pc_slew_rate,
        )

    def _on_pc_arc_enable_toggled(self, checked: bool) -> None:
        self._toggle("pc_programmatic_update", "pc_arc_enabled", self.owner.service.set_pc_arc_enabled, checked)

    def _on_pc_arc_signal_changed(self) -> None:
        self._combo(
            "pc_programmatic_update",
            "pc_arc_signal",
            self.owner.pc_arc_signal_combo,
            self.owner.service.set_pc_arc_signal,
        )

    def _on_pc_arc_factor_finished(self) -> None:
        self._spin(
            "pc_programmatic_update",
            "pc_arc_factor",
            self.owner.pc_arc_factor_spin,
            self.owner.service.set_pc_arc_factor,
        )

    def _on_pressure_comp_enable_toggled(self, checked: bool) -> None:
        self._toggle(
            "pc_programmatic_update",
            "pressure_comp_enabled",
            self.owner.service.set_pressure_comp_enabled,
            checked,
        )

    def _on_pressure_comp_factor_finished(self) -> None:
        self._spin(
            "pc_programmatic_update",
            "pressure_comp_factor",
            self.owner.pressure_comp_factor_spin,
            self.owner.service.set_pressure_comp_factor,
        )

    def apply_texts(self) -> None:
        owner = self.owner
        t = TEXT[owner.language]

        owner.laser_group.setTitle(t["laser"])
        owner.laser_page_title.setText(t["laser_page_subtitle"])
        owner.laser_window.setWindowTitle(f"{t['window_title']} - {t['laser']}")

        owner.cc_label.setText(t["laser_page_title"])
        owner.precision_label.setText(t["step_precision"])
        owner.current_set_label.setText(t["current_set"])
        owner.current_act_label.setText(t["current_act"])
        owner.current_clip_label.setText(t["maximum_current"])
        owner.feedforward_label.setText(t["feedforward"])
        owner.feedforward_factor_label.setText(t["feedforward_factor"])
        owner.arc_label.setText(t["arc"])
        owner.arc_signal_label.setText(t["arc_signal_input"])
        owner.arc_factor_label.setText(t["arc_factor"])

        owner.tc_label.setText(t["temperature_control"])
        owner.tc_precision_label.setText(t["step_precision"])
        owner.temp_set_label.setText(t["set_temperature"])
        owner.temp_act_label.setText(t["actual_temperature"])
        owner.tc_arc_label.setText(t["arc"])
        owner.tc_arc_signal_label.setText(t["arc_signal_input"])
        owner.tc_arc_factor_label.setText(t["arc_factor"])

        owner.pc_label.setText(t["piezo_control"])
        owner.pc_precision_label.setText(t["step_precision"])
        owner.pc_voltage_set_label.setText(t["set_voltage"])
        owner.pc_voltage_act_label.setText(t["actual_voltage"])
        owner.pc_slew_rate_enable_label.setText(t["slew_rate_enable"])
        owner.pc_slew_rate_label.setText(t["slew_rate"])
        owner.pc_arc_label.setText(t["arc"])
        owner.pc_arc_signal_label.setText(t["arc_signal_input"])
        owner.pc_arc_factor_label.setText(t["arc_factor"])
        owner.pressure_comp_label.setText(t["pressure_compensation"])
        owner.pressure_comp_enable_label.setText(t["enabled_label"])
        owner.pressure_comp_air_pressure_label.setText(t["air_pressure"])
        owner.pressure_comp_factor_label.setText(t["pressure_comp_factor"])
        owner.pressure_comp_voltage_label.setText(t["compensation_voltage"])

        owner.current_meta_hint.setText(
            f"{t['current_clip_tuning']} / {t['current_clip_limit']} / {t['effective_current_max']}"
        )
        owner.auto_apply_hint_label.setText(t["auto_apply_hint"])

        owner.current_set_spin.setSuffix(" mA")
        owner.current_clip_spin.setSuffix(" mA")
        owner.feedforward_factor_spin.setSuffix(f" {t['feedforward_factor_unit']}")
        owner.arc_factor_spin.setSuffix(f" {t['arc_factor_unit']}")
        owner.temp_set_spin.setSuffix(f" {t['temperature_unit']}")
        owner.tc_arc_factor_spin.setSuffix(f" {t['tc_arc_factor_unit']}")
        owner.pc_voltage_set_spin.setSuffix(f" {t['voltage_unit']}")
        owner.pc_slew_rate_spin.setSuffix(f" {t['slew_rate_unit']}")
        owner.pc_arc_factor_spin.setSuffix(f" {t['pc_arc_factor_unit']}")
        owner.pressure_comp_factor_spin.setSuffix(f" {t['pressure_comp_factor_unit']}")
        for module_buttons in owner.module_precision_target_buttons.values():
            for button in module_buttons:
                button.setText(t["precision_target"])
        for buttons in (owner.precision_buttons, owner.tc_precision_buttons, owner.pc_precision_buttons):
            for button in buttons:
                button.setText(t[button._text_key])
        owner.update_all_precision_buttons()
        for module in owner.module_precision_target_buttons:
            owner.sync_precision_target_buttons(module)

        if owner.snapshot is None:
            self.reset_readbacks()
            owner.update_toggle_button(owner.cc_enable_button, False)
            owner.update_toggle_button(owner.feedforward_enable_button, False)
            owner.update_toggle_button(owner.arc_enable_button, False)
            owner.update_toggle_button(owner.tc_enable_button, False)
            owner.update_toggle_button(owner.tc_arc_enable_button, False)
            owner.update_toggle_button(owner.pc_enable_button, False)
            owner.update_toggle_button(owner.pc_slew_rate_enable_button, False)
            owner.update_toggle_button(owner.pc_arc_enable_button, False)
            owner.update_toggle_button(owner.pressure_comp_enable_button, False)

    def reset_readbacks(self) -> None:
        owner = self.owner
        t = TEXT[owner.language]
        owner.current_act_value.setText(owner.unit_only_text("mA"))
        owner.temp_act_value.setText(owner.unit_only_text(t["temperature_unit"]))
        owner.pc_voltage_act_value.setText(owner.unit_only_text(t["voltage_unit"]))
        owner.pressure_comp_air_pressure_value.setText(owner.unit_only_text(t["air_pressure_unit"]))
        owner.pressure_comp_voltage_value.setText(owner.unit_only_text(t["voltage_unit"]))

    def render_snapshot(self, snapshot: DeviceSnapshot) -> None:
        owner = self.owner
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
            "pc_enabled",
            "pc_voltage_set",
            "pc_voltage_act",
            "pc_slew_rate_enabled",
            "pc_slew_rate",
            "pc_arc_enabled",
            "pc_arc_signal",
            "pc_arc_factor",
            "sc_enabled",
            "sc_amplitude",
            "sc_offset",
            "sc_output_channel",
            "sc_frequency",
            "sc_signal_type",
            "sc_unit",
            "lock_enabled",
            "lock_hold",
            "lock_input_channel",
            "lock_type",
            "lock_pid_selection",
            "lock_without_lockpoint",
            "pid1_enabled",
            "pid1_gain_all",
            "pid1_gain_p",
            "pid1_gain_i",
            "pid1_gain_d",
            "pid1_output_channel",
            "pid1_sign",
            "pid1_i_cutoff_enabled",
            "pid1_i_cutoff",
            "pid1_limit_enabled",
            "pid1_limit_max",
            "pid2_enabled",
            "pid2_gain_all",
            "pid2_gain_p",
            "pid2_gain_i",
            "pid2_gain_d",
            "pid2_output_channel",
            "pid2_sign",
            "pid2_limit_enabled",
            "pid2_limit_max",
            "pressure_comp_enabled",
            "pressure_comp_air_pressure",
            "pressure_comp_factor",
            "pressure_comp_voltage",
            "use_current_clip_tuning",
            "cc_status_txt",
            "latest_message",
        ]
        owner.parameter_table.setRowCount(len(display_order))
        for row, key in enumerate(display_order):
            label = PARAMETER_LABELS.get(key, {"zh": key, "en": key})[owner.language]
            value = values[key]
            if key in {"arc_signal", "tc_arc_signal", "pc_arc_signal"}:
                value = self.arc_signal_name(int(value))
            elif key == "sc_output_channel":
                value = self.scan_output_name(int(value))
            elif key == "sc_signal_type":
                value = self.scan_shape_name(int(value))
            elif key == "lock_input_channel":
                value = self.scan_lock_input_name(int(value))
            elif key == "lock_type":
                value = self.scan_lock_type_name(int(value))
            elif key == "lock_pid_selection":
                value = self.scan_lock_pid_name(int(value))
            elif key in {"pid1_output_channel", "pid2_output_channel"}:
                value = self.pid_output_name(int(value))
            elif isinstance(value, bool):
                value = TEXT[owner.language]["enabled_state"] if value else TEXT[owner.language]["disabled_state"]
            elif isinstance(value, float):
                value = f"{value:.5f}"
            owner.parameter_table.setItem(row, 0, QTableWidgetItem(label))
            owner.parameter_table.setItem(row, 1, QTableWidgetItem(str(value)))

        owner.last_device_current_set = snapshot.current_set
        sync_current = getattr(owner.current_set_spin, "sync_from_device", None)
        if abs(owner.current_set_spin.value() - snapshot.current_set) < 0.000005:
            owner.current_set_dirty = False
            if callable(sync_current):
                sync_current(snapshot.current_set)
        elif not owner.current_set_dirty and not owner.current_set_spin.hasFocus():
            owner.current_set_programmatic_update = True
            owner.current_set_spin.blockSignals(True)
            owner.current_set_spin.setValue(snapshot.current_set)
            owner.current_set_spin.blockSignals(False)
            owner.current_set_programmatic_update = False

        owner.cc_programmatic_update = True
        owner.feedforward_programmatic_update = True
        owner.arc_programmatic_update = True
        owner.tc_programmatic_update = True
        owner.pc_programmatic_update = True
        self._set_spin_if_idle(owner.current_clip_spin, snapshot.current_clip)
        owner.current_clip_spin.setMaximum(max(snapshot.current_clip_writable_limit, owner.current_clip_spin.minimum()))

        owner.current_act_value.setText(owner.format_value_with_unit(snapshot.current_act, 5, "mA"))
        self._set_spin_if_idle(owner.feedforward_factor_spin, snapshot.feedforward_factor)
        self._set_spin_if_idle(owner.arc_factor_spin, snapshot.arc_factor)
        self._set_spin_if_idle(owner.temp_set_spin, snapshot.temp_set)
        owner.temp_act_value.setText(
            owner.format_value_with_unit(snapshot.temp_act, 3, TEXT[owner.language]["temperature_unit"])
        )
        self._set_spin_if_idle(owner.tc_arc_factor_spin, snapshot.tc_arc_factor)
        self._set_spin_if_idle(owner.pc_voltage_set_spin, snapshot.pc_voltage_set)
        owner.pc_voltage_act_value.setText(
            owner.format_value_with_unit(snapshot.pc_voltage_act, 6, TEXT[owner.language]["voltage_unit"])
        )
        self._set_spin_if_idle(owner.pc_slew_rate_spin, snapshot.pc_slew_rate)
        self._set_spin_if_idle(owner.pc_arc_factor_spin, snapshot.pc_arc_factor)
        owner.pressure_comp_air_pressure_value.setText(
            owner.format_value_with_unit(snapshot.pressure_comp_air_pressure, 3, TEXT[owner.language]["air_pressure_unit"])
        )
        self._set_spin_if_idle(owner.pressure_comp_factor_spin, snapshot.pressure_comp_factor)
        owner.pressure_comp_voltage_value.setText(
            owner.format_value_with_unit(snapshot.pressure_comp_voltage, 3, TEXT[owner.language]["voltage_unit"])
        )
        self._sync_combo(owner.arc_signal_combo, snapshot.arc_signal)
        self._sync_combo(owner.tc_arc_signal_combo, snapshot.tc_arc_signal)
        self._sync_combo(owner.pc_arc_signal_combo, snapshot.pc_arc_signal)

        owner.update_toggle_button(owner.cc_enable_button, snapshot.cc_enabled)
        owner.update_toggle_button(owner.feedforward_enable_button, snapshot.feedforward_enabled)
        owner.update_toggle_button(owner.arc_enable_button, snapshot.arc_enabled)
        owner.update_toggle_button(owner.tc_enable_button, snapshot.tc_enabled)
        owner.update_toggle_button(owner.tc_arc_enable_button, snapshot.tc_arc_enabled)
        owner.update_toggle_button(owner.pc_enable_button, snapshot.pc_enabled)
        owner.update_toggle_button(owner.pc_slew_rate_enable_button, snapshot.pc_slew_rate_enabled)
        owner.update_toggle_button(owner.pc_arc_enable_button, snapshot.pc_arc_enabled)
        owner.update_toggle_button(owner.pressure_comp_enable_button, snapshot.pressure_comp_enabled)

        owner.current_meta_hint.setText(
            f"{TEXT[owner.language]['current_clip_tuning']}: {snapshot.current_clip_tuning:.5f} mA   |   "
            f"{TEXT[owner.language]['current_clip_limit']}: {snapshot.current_clip_limit:.5f} mA   |   "
            f"{TEXT[owner.language]['effective_current_max']}: {snapshot.effective_current_max:.5f} mA"
        )

        owner.cc_programmatic_update = False
        owner.feedforward_programmatic_update = False
        owner.arc_programmatic_update = False
        owner.tc_programmatic_update = False
        owner.pc_programmatic_update = False
    def _sync_combo(self, combo, value: int) -> None:
        if combo.view().isVisible() or combo.hasFocus():
            return
        index = combo.findData(value)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

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

    def arc_signal_name(self, value: int) -> str:
        for key, signal in ARC_SIGNAL_OPTIONS:
            if signal == value:
                return TEXT[self.owner.language][key]
        return str(value)

    def scan_output_name(self, value: int) -> str:
        for key, option in SCAN_OUTPUT_OPTIONS:
            if option == value:
                return TEXT[self.owner.language][key]
        return str(value)

    def scan_shape_name(self, value: int) -> str:
        for key, option in SCAN_SHAPE_OPTIONS:
            if option == value:
                return TEXT[self.owner.language][key]
        return str(value)

    def scan_lock_input_name(self, value: int) -> str:
        from ui_text import LOCK_INPUT_SIGNAL_OPTIONS

        for key, option in LOCK_INPUT_SIGNAL_OPTIONS:
            if option == value:
                return TEXT[self.owner.language][key]
        return str(value)

    def scan_lock_type_name(self, value: int) -> str:
        from ui_text import LOCK_TYPE_OPTIONS

        for key, option in LOCK_TYPE_OPTIONS:
            if option == value:
                return TEXT[self.owner.language][key]
        return str(value)

    def scan_lock_pid_name(self, value: int) -> str:
        from ui_text import LOCK_PID_SELECTION_OPTIONS

        for key, option in LOCK_PID_SELECTION_OPTIONS:
            if option == value:
                return TEXT[self.owner.language][key]
        return str(value)

    def pid_output_name(self, value: int) -> str:
        for key, option in PID_OUTPUT_CHANNEL_OPTIONS:
            if option == value:
                return TEXT[self.owner.language][key]
        return str(value)
