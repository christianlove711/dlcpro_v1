from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from dlcpro_service import DeviceSnapshot
from ui_text import STABILIZATION_OUTPUT_CHANNEL_OPTIONS, STABILIZATION_PHYSICAL_CHANNEL_OPTIONS, TEXT
from widgets.stabilization import PowerStabilizationPanel, StabilizationDetectionPanel
from windows.base_window import AuxiliaryWindow, set_scrollable_central_widget


class StabilizationWindow(AuxiliaryWindow):
    def __init__(self, owner) -> None:
        super().__init__()
        self.owner = owner
        self.resize(920, 860)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.status_hint = QLabel()
        self.status_hint.setObjectName("SubtleHint")
        self.status_hint.setWordWrap(True)
        root.addWidget(self.status_hint)

        self.power_panel = PowerStabilizationPanel(owner)
        self.power_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        root.addWidget(self.power_panel)

        detection_row = QHBoxLayout()
        detection_row.setContentsMargins(0, 0, 0, 0)
        detection_row.setSpacing(14)
        self.detection_panel = StabilizationDetectionPanel(owner)
        self.detection_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        detection_row.addWidget(self.detection_panel, 1)
        detection_row.addStretch(1)
        root.addLayout(detection_row)

        root.addStretch(1)
        self.scroll_area = set_scrollable_central_widget(self, central)

        self._configure_combo(self.power_panel.input_signal_combo)
        self._configure_combo(self.power_panel.external_physical_channel_combo)
        self._configure_combo(self.power_panel.output_signal_combo)

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(f"{t['window_title']} - {t['stabilization']}")
        self.status_hint.setText(t["stabilization_status_hint"])

        power = self.power_panel
        power.title_label.setText(t["stabilization_power_group"])
        power.mapping_hint_label.setText(t["stabilization_input_signal_unverified"])
        power.input_signal_label.setText(t["stabilization_input_signal"])
        power.external_physical_channel_label.setText(t["stabilization_external_physical_channel"])
        power.photo_diode_value_label.setText(t["stabilization_photo_diode_value"])
        power.cal_factor_label.setText(t["stabilization_cal_factor"])
        power.cal_offset_label.setText(t["stabilization_cal_offset"])
        power.set_level_label.setText(t["stabilization_set_level"])
        power.actual_level_label.setText(t["stabilization_actual_level"])
        power.output_signal_label.setText(t["stabilization_output_signal"])
        power.gain_label.setText(t["stabilization_gain"])
        power.hold_output_label.setText(t["stabilization_hold_output_on_unlock"])
        power.enable_button.setText(t["enable"])

        detection = self.detection_panel
        detection.title_label.setText(t["stabilization_detection"])
        detection.level_label.setText(t["stabilization_level"])
        detection.hysteresis_label.setText(t["hysteresis"])
        detection.enable_button.setText(t["enable"])

        power.photo_diode_value_edit.setPlaceholderText(f"0.000000 {t['voltage_unit']}")
        power.actual_level_edit.setPlaceholderText("0.000000 mW")
        power.set_level_spin.setSuffix(" mW")
        detection.level_spin.setSuffix(" mW")
        detection.hysteresis_spin.setSuffix(" mW")
        power.gain_p_spin.setSuffix(" mA/mW")
        power.gain_i_spin.setSuffix(" mA/mW/ms")
        power.gain_d_spin.setSuffix(" mA/mW*us")

        self._populate_pd_ext_channel_options(language)
        self._populate_output_channel_options(language)
        if self.owner.snapshot is None:
            self.reset_state(language)

    def render_snapshot(self, snapshot: DeviceSnapshot | None) -> None:
        if snapshot is None or snapshot.stabilization is None:
            self.reset_state(self.owner.language)
            return

        t = TEXT[self.owner.language]
        self.status_hint.setText(t["stabilization_status_hint"])
        power = self.power_panel
        detection = self.detection_panel
        data = snapshot.stabilization

        self._update_toggle_button(power.enable_button, data.enabled)
        self._update_toggle_button(detection.enable_button, data.window_enabled)
        self._sync_single_value_combo(
            power.input_signal_combo,
            data.input_channel,
            f"{t['stabilization_input_channel_raw']} {data.input_channel}",
        )
        self._sync_combo(power.external_physical_channel_combo, data.pd_ext_input_channel)
        self._sync_single_value_combo(
            power.output_signal_combo,
            data.output_channel,
            self._output_label(self.owner.language, data.output_channel),
        )
        self._set_spin_if_idle(power.cal_factor_spin, data.pd_ext_cal_factor)
        self._set_spin_if_idle(power.cal_offset_spin, data.pd_ext_cal_offset)
        self._set_spin_if_idle(power.set_level_spin, data.setpoint)
        self._set_spin_if_idle(power.gain_all_spin, data.gain_all)
        self._set_spin_if_idle(power.gain_p_spin, data.gain_p)
        self._set_spin_if_idle(power.gain_i_spin, data.gain_i)
        self._set_spin_if_idle(power.gain_d_spin, data.gain_d)
        self._set_spin_if_idle(detection.level_spin, data.window_level_low)
        self._set_spin_if_idle(detection.hysteresis_spin, data.window_level_hysteresis)

        power.photo_diode_value_edit.setText(f"{data.pd_ext_photodiode:.6f} {t['voltage_unit']}")
        power.actual_level_edit.setText(f"{data.actual_level:.6f} mW")
        power.hold_output_check.blockSignals(True)
        power.hold_output_check.setChecked(data.hold_output_on_unlock)
        power.hold_output_check.blockSignals(False)

    def reset_state(self, language: str) -> None:
        t = TEXT[language]
        power = self.power_panel
        detection = self.detection_panel

        self.status_hint.setText(t["stabilization_unavailable"])
        self._update_toggle_button(power.enable_button, False)
        self._update_toggle_button(detection.enable_button, False)
        self._sync_single_value_combo(power.input_signal_combo, -1, "External Power")
        self._sync_combo(power.external_physical_channel_combo, STABILIZATION_PHYSICAL_CHANNEL_OPTIONS[0][1])
        self._sync_single_value_combo(power.output_signal_combo, STABILIZATION_OUTPUT_CHANNEL_OPTIONS[0][1], self._output_label(language, 51))
        power.photo_diode_value_edit.setText(f"0.000000 {t['voltage_unit']}")
        power.actual_level_edit.setText("0.000000 mW")
        for spin in (
            power.cal_factor_spin,
            power.cal_offset_spin,
            power.set_level_spin,
            power.gain_all_spin,
            power.gain_p_spin,
            power.gain_i_spin,
            power.gain_d_spin,
            detection.level_spin,
            detection.hysteresis_spin,
        ):
            spin.blockSignals(True)
            spin.setValue(0.0)
            spin.blockSignals(False)
        power.hold_output_check.blockSignals(True)
        power.hold_output_check.setChecked(False)
        power.hold_output_check.blockSignals(False)

    def set_writable(self, writable: bool, previewable: bool) -> None:
        self.power_panel.input_signal_combo.setEnabled(previewable)
        self.power_panel.output_signal_combo.setEnabled(previewable)
        self.power_panel.external_physical_channel_combo.setEnabled(previewable)
        for widget in (
            self.power_panel.enable_button,
            self.power_panel.cal_factor_spin,
            self.power_panel.cal_offset_spin,
            self.power_panel.set_level_spin,
            self.power_panel.gain_all_spin,
            self.power_panel.gain_p_spin,
            self.power_panel.gain_i_spin,
            self.power_panel.gain_d_spin,
            self.power_panel.hold_output_check,
            self.detection_panel.enable_button,
            self.detection_panel.level_spin,
            self.detection_panel.hysteresis_spin,
        ):
            widget.setEnabled(writable)

    def _populate_pd_ext_channel_options(self, language: str) -> None:
        combo = self.power_panel.external_physical_channel_combo
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in STABILIZATION_PHYSICAL_CHANNEL_OPTIONS:
            combo.addItem(TEXT[language][text_key], value)
        combo.blockSignals(False)
        self._restore_combo_value(combo, current, STABILIZATION_PHYSICAL_CHANNEL_OPTIONS[0][1])

    def _populate_output_channel_options(self, language: str) -> None:
        combo = self.power_panel.output_signal_combo
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in STABILIZATION_OUTPUT_CHANNEL_OPTIONS:
            combo.addItem(TEXT[language][text_key], value)
        combo.blockSignals(False)
        self._restore_combo_value(combo, current, STABILIZATION_OUTPUT_CHANNEL_OPTIONS[0][1])

    @staticmethod
    def _configure_combo(combo: QComboBox) -> None:
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.setMinimumWidth(220)

    def _restore_combo_value(self, combo: QComboBox, current, fallback: int) -> None:
        target = fallback if current is None else current
        index = combo.findData(target)
        if index < 0:
            index = combo.findData(fallback)
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

    @staticmethod
    def _sync_combo(combo: QComboBox, value: int) -> None:
        if combo.view().isVisible() or combo.hasFocus():
            return
        index = combo.findData(value)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _sync_single_value_combo(self, combo: QComboBox, value: int, label: str) -> None:
        if combo.view().isVisible() or combo.hasFocus():
            return
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(label, value)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def _update_toggle_button(self, button, enabled: bool) -> None:
        self.owner._update_toggle_button(button, enabled)

    @staticmethod
    def _output_label(language: str, output_channel: int) -> str:
        if output_channel == 51:
            return TEXT[language]["pid_output_cc_current"]
        return f"{TEXT[language]['stabilization_output_channel_raw']} {output_channel}"
