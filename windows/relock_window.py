from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QSizePolicy, QVBoxLayout, QWidget

from dlcpro_service import DeviceSnapshot
from ui_text import LOCK_INPUT_SIGNAL_OPTIONS, RELOCK_OUTPUT_CHANNEL_OPTIONS, TEXT
from widgets.relock import LockDetectionPanel, RelockPanel
from windows.base_window import AuxiliaryWindow


class RelockWindow(AuxiliaryWindow):
    def __init__(self, owner) -> None:
        super().__init__()
        self.owner = owner
        self.resize(1180, 480)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.status_hint = QLabel()
        self.status_hint.setObjectName("SubtleHint")
        self.status_hint.setWordWrap(True)
        root.addWidget(self.status_hint)

        panels = QHBoxLayout()
        panels.setSpacing(14)

        self.lock_detection_panel = LockDetectionPanel(owner)
        self.lock_detection_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        panels.addWidget(self.lock_detection_panel, 3)

        self.relock_panel = RelockPanel(owner)
        self.relock_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        panels.addWidget(self.relock_panel, 2)
        panels.addStretch(1)

        root.addLayout(panels)
        root.addStretch(1)
        self.setCentralWidget(central)

        self._configure_combo(self.lock_detection_panel.input_signal_combo)
        self._configure_combo(self.relock_panel.output_channel_combo)

    def apply_texts(self, language: str) -> None:
        t = TEXT[language]
        self.setWindowTitle(f"{t['window_title']} - {t['relock']}")
        self.status_hint.setText(t["relock_status_hint"])

        left = self.lock_detection_panel
        right = self.relock_panel

        left.title_label.setText(t["lock_detection"])
        left.input_signal_label.setText(t["input_signal"])
        left.level_high_label.setText(t["level_high"])
        left.level_low_label.setText(t["level_low"])
        left.hysteresis_label.setText(t["hysteresis"])
        left.delay_label.setText(t["delay"])
        left.out_of_lock_action_label.setText(t["out_of_lock_action"])
        left.enable_reset_label.setText(t["enable_reset"])

        right.title_label.setText(t["relock"])
        right.amplitude_label.setText(t["relock_amplitude"])
        right.frequency_label.setText(t["relock_frequency"])
        right.output_channel_label.setText(t["relock_output_channel"])

        left.level_high_spin.setSuffix(f" {t['voltage_unit']}")
        left.level_low_spin.setSuffix(f" {t['voltage_unit']}")
        left.hysteresis_spin.setSuffix(f" {t['voltage_unit']}")
        left.delay_spin.setSuffix(" ms")
        right.amplitude_spin.setSuffix(f" {t['voltage_unit']}")
        right.frequency_spin.setSuffix(" Hz")

        self._populate_input_signal_options(language)
        self._populate_output_channel_options(language)

    def render_snapshot(self, snapshot: DeviceSnapshot | None) -> None:
        if snapshot is None:
            self.reset_state(self.owner.language)
            return

        left = self.lock_detection_panel
        right = self.relock_panel

        self._update_toggle_button(left.enable_button, snapshot.relock_detection_enabled)
        self._sync_combo(left.input_signal_combo, snapshot.relock_input_channel)
        self._set_spin_if_idle(left.level_high_spin, snapshot.relock_level_high)
        self._set_spin_if_idle(left.level_low_spin, snapshot.relock_level_low)
        self._set_spin_if_idle(left.hysteresis_spin, snapshot.relock_level_hysteresis)
        self._set_spin_if_idle(left.delay_spin, snapshot.relock_delay)
        left.enable_reset_check.blockSignals(True)
        left.enable_reset_check.setChecked(snapshot.relock_reset_enabled)
        left.enable_reset_check.blockSignals(False)

        self._update_toggle_button(right.enable_button, snapshot.relock_enabled)
        self._set_spin_if_idle(right.amplitude_spin, snapshot.relock_amplitude)
        self._set_spin_if_idle(right.frequency_spin, snapshot.relock_frequency)
        self._sync_combo(right.output_channel_combo, snapshot.relock_output_channel)

    def reset_state(self, language: str) -> None:
        self.apply_texts(language)
        left = self.lock_detection_panel
        right = self.relock_panel

        self._update_toggle_button(left.enable_button, False)
        self._update_toggle_button(right.enable_button, False)
        self._sync_combo(left.input_signal_combo, LOCK_INPUT_SIGNAL_OPTIONS[0][1])
        self._sync_combo(right.output_channel_combo, RELOCK_OUTPUT_CHANNEL_OPTIONS[1][1])

        for spin in (
            left.level_high_spin,
            left.level_low_spin,
            left.hysteresis_spin,
            left.delay_spin,
            right.amplitude_spin,
            right.frequency_spin,
        ):
            spin.blockSignals(True)
            spin.setValue(0.0)
            spin.blockSignals(False)

        left.enable_reset_check.blockSignals(True)
        left.enable_reset_check.setChecked(False)
        left.enable_reset_check.blockSignals(False)

    def set_writable(self, writable: bool, previewable: bool) -> None:
        left = self.lock_detection_panel
        right = self.relock_panel

        left.input_signal_combo.setEnabled(previewable)
        right.output_channel_combo.setEnabled(previewable)

        for widget in (
            left.enable_button,
            left.level_high_spin,
            left.level_low_spin,
            left.hysteresis_spin,
            left.delay_spin,
            left.enable_reset_check,
            right.enable_button,
            right.amplitude_spin,
            right.frequency_spin,
        ):
            widget.setEnabled(writable)

    def validate_window_levels(self) -> bool:
        left = self.lock_detection_panel
        level_high = left.level_high_spin.value()
        level_low = left.level_low_spin.value()
        hysteresis = left.hysteresis_spin.value()
        if level_high + 1e-12 >= level_low + 2.0 * hysteresis:
            return True
        QMessageBox.warning(
            self,
            "Warning",
            TEXT[self.owner.language]["relock_window_rule_warning"],
        )
        if self.owner.snapshot is not None:
            self.render_snapshot(self.owner.snapshot)
        return False

    def _populate_input_signal_options(self, language: str) -> None:
        combo = self.lock_detection_panel.input_signal_combo
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in LOCK_INPUT_SIGNAL_OPTIONS:
            combo.addItem(TEXT[language][text_key], value)
        combo.blockSignals(False)
        self._restore_combo_value(combo, current, LOCK_INPUT_SIGNAL_OPTIONS[0][1])

    def _populate_output_channel_options(self, language: str) -> None:
        combo = self.relock_panel.output_channel_combo
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for text_key, value in RELOCK_OUTPUT_CHANNEL_OPTIONS:
            combo.addItem(TEXT[language][text_key], value)
        combo.blockSignals(False)
        self._restore_combo_value(combo, current, RELOCK_OUTPUT_CHANNEL_OPTIONS[1][1])

    def _restore_combo_value(self, combo: QComboBox, current, fallback: int) -> None:
        target = fallback if current is None else current
        index = combo.findData(target)
        if index < 0:
            index = combo.findData(fallback)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)
        self._fit_combo_popup_width(combo)

    def _configure_combo(self, combo: QComboBox) -> None:
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._fit_combo_popup_width(combo)

    def _fit_combo_popup_width(self, combo: QComboBox) -> None:
        metrics = combo.fontMetrics()
        widths = [metrics.horizontalAdvance(combo.itemText(i)) for i in range(combo.count())]
        current_width = metrics.horizontalAdvance(combo.currentText()) if combo.currentText() else 0
        content_width = max(widths + [current_width, 120])
        target_width = content_width + 48
        combo.view().setMinimumWidth(target_width)
        combo.setMinimumWidth(min(target_width, 260))

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
    def _sync_combo(combo, value: int) -> None:
        if combo.view().isVisible() or combo.hasFocus():
            return
        index = combo.findData(value)
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _update_toggle_button(self, button, enabled: bool) -> None:
        self.owner._update_toggle_button(button, enabled)
