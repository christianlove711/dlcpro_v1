from __future__ import annotations


class RelockController:
    def __init__(self, app) -> None:
        self.app = app
        self.window = None

    def bind_window(self, window) -> None:
        self.window = window

    def _snapshot(self):
        if not self.app.service.is_connected:
            return None
        return self.app.snapshot

    def _submit(self, fn) -> None:
        self.app.submit_device_task(fn)

    def _on_relock_detection_enabled_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.relock_detection_enabled:
            self._submit(lambda: self.app.service.set_relock_detection_enabled(checked))

    def _on_relock_input_signal_changed(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = int(self.window.lock_detection_panel.input_signal_combo.currentData())
        if value != snapshot.relock_input_channel:
            self._submit(lambda: self.app.service.set_relock_input_channel(value))

    def _on_relock_level_high_finished(self) -> None:
        if self.window.validate_window_levels():
            self._write_spin("relock_level_high", self.window.lock_detection_panel.level_high_spin, self.app.service.set_relock_level_high)

    def _on_relock_level_low_finished(self) -> None:
        if self.window.validate_window_levels():
            self._write_spin("relock_level_low", self.window.lock_detection_panel.level_low_spin, self.app.service.set_relock_level_low)

    def _on_relock_hysteresis_finished(self) -> None:
        if self.window.validate_window_levels():
            self._write_spin("relock_level_hysteresis", self.window.lock_detection_panel.hysteresis_spin, self.app.service.set_relock_level_hysteresis)

    def _on_relock_delay_finished(self) -> None:
        self._write_spin("relock_delay", self.window.lock_detection_panel.delay_spin, self.app.service.set_relock_delay)

    def _on_relock_reset_enabled_changed(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        checked = self.window.lock_detection_panel.enable_reset_check.isChecked()
        if checked != snapshot.relock_reset_enabled:
            self._submit(lambda: self.app.service.set_relock_reset_enabled(checked))

    def _on_relock_enabled_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.relock_enabled:
            self._submit(lambda: self.app.service.set_relock_enabled(checked))

    def _on_relock_amplitude_finished(self) -> None:
        self._write_spin("relock_amplitude", self.window.relock_panel.amplitude_spin, self.app.service.set_relock_amplitude)

    def _on_relock_frequency_finished(self) -> None:
        self._write_spin("relock_frequency", self.window.relock_panel.frequency_spin, self.app.service.set_relock_frequency)

    def _on_relock_output_channel_changed(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = int(self.window.relock_panel.output_channel_combo.currentData())
        if value != snapshot.relock_output_channel:
            self._submit(lambda: self.app.service.set_relock_output_channel(value))

    def _write_spin(self, attr: str, spinbox, setter) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = spinbox.value()
        if abs(value - getattr(snapshot, attr)) >= 1e-9:
            self._submit(lambda: setter(value))
