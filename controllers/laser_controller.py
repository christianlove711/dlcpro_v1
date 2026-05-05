from __future__ import annotations

from dataclasses import asdict

from PySide6.QtWidgets import QTableWidgetItem

from dlcpro_service import DeviceSnapshot
from ui_text import ARC_SIGNAL_OPTIONS, PARAMETER_LABELS, SCAN_OUTPUT_OPTIONS, SCAN_SHAPE_OPTIONS, TEXT


class LaserController:
    def __init__(self, owner) -> None:
        self.owner = owner

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

        owner.sc_label.setText(t["scan_control"])
        owner.sc_precision_label.setText(t["step_precision"])
        owner.scan_amplitude_label.setText(t["scan_amplitude"])
        owner.scan_offset_label.setText(t["scan_offset"])
        owner.scan_output_label.setText(t["scan_output"])
        owner.scan_frequency_label.setText(t["scan_frequency"])
        owner.scan_shape_label.setText(t["scan_shape"])

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
        self._apply_scan_unit_suffixes(t["voltage_unit"])

        for module_buttons in owner.module_precision_target_buttons.values():
            for button in module_buttons:
                button.setText(t["precision_target"])
        for buttons in (owner.precision_buttons, owner.tc_precision_buttons, owner.pc_precision_buttons, owner.sc_precision_buttons):
            for button in buttons:
                button.setText(t[button._text_key])
        owner._update_all_precision_buttons()
        for module in owner.module_precision_target_buttons:
            owner._sync_precision_target_buttons(module)

        if owner.snapshot is None:
            self.reset_readbacks()
            owner._update_toggle_button(owner.cc_enable_button, False)
            owner._update_toggle_button(owner.feedforward_enable_button, False)
            owner._update_toggle_button(owner.arc_enable_button, False)
            owner._update_toggle_button(owner.tc_enable_button, False)
            owner._update_toggle_button(owner.tc_arc_enable_button, False)
            owner._update_toggle_button(owner.pc_enable_button, False)
            owner._update_toggle_button(owner.pc_slew_rate_enable_button, False)
            owner._update_toggle_button(owner.pc_arc_enable_button, False)
            owner._update_toggle_button(owner.sc_enable_button, False)
            owner._update_toggle_button(owner.pressure_comp_enable_button, False)

    def reset_readbacks(self) -> None:
        owner = self.owner
        t = TEXT[owner.language]
        owner.current_act_value.setText(owner._unit_only_text("mA"))
        owner.temp_act_value.setText(owner._unit_only_text(t["temperature_unit"]))
        owner.pc_voltage_act_value.setText(owner._unit_only_text(t["voltage_unit"]))
        owner.pressure_comp_air_pressure_value.setText(owner._unit_only_text(t["air_pressure_unit"]))
        owner.pressure_comp_voltage_value.setText(owner._unit_only_text(t["voltage_unit"]))

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
            elif isinstance(value, bool):
                value = TEXT[owner.language]["enabled_state"] if value else TEXT[owner.language]["disabled_state"]
            elif isinstance(value, float):
                value = f"{value:.5f}"
            owner.parameter_table.setItem(row, 0, QTableWidgetItem(label))
            owner.parameter_table.setItem(row, 1, QTableWidgetItem(str(value)))

        owner.last_device_current_set = snapshot.current_set
        if not owner.current_set_dirty and not owner.current_set_spin.hasFocus():
            owner.current_set_programmatic_update = True
            owner.current_set_spin.blockSignals(True)
            owner.current_set_spin.setValue(snapshot.current_set)
            owner.current_set_spin.blockSignals(False)
            owner.current_set_programmatic_update = False
        elif abs(owner.current_set_spin.value() - snapshot.current_set) < 0.000005:
            owner.current_set_dirty = False

        owner.cc_programmatic_update = True
        owner.feedforward_programmatic_update = True
        owner.arc_programmatic_update = True
        owner.tc_programmatic_update = True
        owner.pc_programmatic_update = True
        owner.sc_programmatic_update = True

        owner.current_clip_spin.blockSignals(True)
        owner.current_clip_spin.setValue(snapshot.current_clip)
        owner.current_clip_spin.blockSignals(False)
        owner.current_clip_spin.setMaximum(max(snapshot.effective_current_max, owner.current_clip_spin.minimum()))

        owner.current_act_value.setText(owner._format_value_with_unit(snapshot.current_act, 5, "mA"))
        owner.feedforward_factor_spin.blockSignals(True)
        owner.feedforward_factor_spin.setValue(snapshot.feedforward_factor)
        owner.feedforward_factor_spin.blockSignals(False)
        owner.arc_factor_spin.blockSignals(True)
        owner.arc_factor_spin.setValue(snapshot.arc_factor)
        owner.arc_factor_spin.blockSignals(False)
        owner.temp_set_spin.blockSignals(True)
        owner.temp_set_spin.setValue(snapshot.temp_set)
        owner.temp_set_spin.blockSignals(False)
        owner.temp_act_value.setText(
            owner._format_value_with_unit(snapshot.temp_act, 3, TEXT[owner.language]["temperature_unit"])
        )
        owner.tc_arc_factor_spin.blockSignals(True)
        owner.tc_arc_factor_spin.setValue(snapshot.tc_arc_factor)
        owner.tc_arc_factor_spin.blockSignals(False)
        owner.pc_voltage_set_spin.blockSignals(True)
        owner.pc_voltage_set_spin.setValue(snapshot.pc_voltage_set)
        owner.pc_voltage_set_spin.blockSignals(False)
        owner.pc_voltage_act_value.setText(
            owner._format_value_with_unit(snapshot.pc_voltage_act, 6, TEXT[owner.language]["voltage_unit"])
        )
        owner.pc_slew_rate_spin.blockSignals(True)
        owner.pc_slew_rate_spin.setValue(snapshot.pc_slew_rate)
        owner.pc_slew_rate_spin.blockSignals(False)
        owner.pc_arc_factor_spin.blockSignals(True)
        owner.pc_arc_factor_spin.setValue(snapshot.pc_arc_factor)
        owner.pc_arc_factor_spin.blockSignals(False)
        owner.pressure_comp_air_pressure_value.setText(
            owner._format_value_with_unit(snapshot.pressure_comp_air_pressure, 3, TEXT[owner.language]["air_pressure_unit"])
        )
        owner.pressure_comp_factor_spin.blockSignals(True)
        owner.pressure_comp_factor_spin.setValue(snapshot.pressure_comp_factor)
        owner.pressure_comp_factor_spin.blockSignals(False)
        owner.pressure_comp_voltage_value.setText(
            owner._format_value_with_unit(snapshot.pressure_comp_voltage, 3, TEXT[owner.language]["voltage_unit"])
        )
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

        self._sync_combo(owner.arc_signal_combo, snapshot.arc_signal)
        self._sync_combo(owner.tc_arc_signal_combo, snapshot.tc_arc_signal)
        self._sync_combo(owner.pc_arc_signal_combo, snapshot.pc_arc_signal)
        self._sync_combo(owner.scan_output_combo, snapshot.sc_output_channel)
        self._sync_combo(owner.scan_shape_combo, snapshot.sc_signal_type)

        owner._update_toggle_button(owner.cc_enable_button, snapshot.cc_enabled)
        owner._update_toggle_button(owner.feedforward_enable_button, snapshot.feedforward_enabled)
        owner._update_toggle_button(owner.arc_enable_button, snapshot.arc_enabled)
        owner._update_toggle_button(owner.tc_enable_button, snapshot.tc_enabled)
        owner._update_toggle_button(owner.tc_arc_enable_button, snapshot.tc_arc_enabled)
        owner._update_toggle_button(owner.pc_enable_button, snapshot.pc_enabled)
        owner._update_toggle_button(owner.pc_slew_rate_enable_button, snapshot.pc_slew_rate_enabled)
        owner._update_toggle_button(owner.pc_arc_enable_button, snapshot.pc_arc_enabled)
        owner._update_toggle_button(owner.sc_enable_button, snapshot.sc_enabled)
        owner._update_toggle_button(owner.pressure_comp_enable_button, snapshot.pressure_comp_enabled)

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
        owner.sc_programmatic_update = False

    def _sync_combo(self, combo, value: int) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

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

    def _apply_scan_unit_suffixes(self, unit: str) -> None:
        owner = self.owner
        amplitude_unit = TEXT[owner.language]["scan_amplitude_unit"]
        base_unit = unit or TEXT[owner.language]["voltage_unit"]
        if base_unit == TEXT[owner.language]["voltage_unit"]:
            amplitude_unit = TEXT[owner.language]["scan_amplitude_unit"]
        else:
            amplitude_unit = f"{base_unit} pp"
        owner.scan_amplitude_spin.setSuffix(f" {amplitude_unit}")
        owner.scan_offset_spin.setSuffix(f" {base_unit}")
        owner.scan_frequency_spin.setSuffix(" Hz")
