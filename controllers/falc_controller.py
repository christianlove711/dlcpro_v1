from __future__ import annotations

class FalcController:
    def __init__(self, app) -> None:
        self.app = app
        self.window = None

    def bind_window(self, window) -> None:
        self.window = window

    def _snapshot(self):
        snapshot = self.app.snapshot
        if not self.app.service.is_connected or snapshot is None:
            return None
        return snapshot.falc1

    def _submit(self, fn) -> None:
        self.app.submit_device_task(fn)

    def _on_falc_input_gain_changed(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = int(self.window.input_gain_combo.currentData())
        if value != snapshot.input_gain:
            self._submit(lambda: self.app.service.set_falc1_input_gain(value))

    def _on_falc_input_offset_finished(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = self.window.input_offset_spin.value()
        if abs(value - snapshot.input_offset) >= 1e-12:
            self._submit(lambda: self.app.service.set_falc1_input_offset(value))

    def _on_falc_path_selection_changed(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = int(self.window.path_selection_combo.currentData())
        if value != snapshot.path_selection:
            self._submit(lambda: self.app.service.set_falc1_path_selection(value))

    def _on_falc_mon_config_changed(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = int(self.window.mon_config_combo.currentData())
        if value != snapshot.mon_config:
            self._submit(lambda: self.app.service.set_falc1_mon_config(value))

    def _on_falc_main_enabled_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.main.enabled:
            self._submit(lambda: self.app.service.set_falc1_main_enabled(checked))

    def _on_falc_main_gain_finished(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = self.window.main_gain_spin.value()
        if abs(value - snapshot.main.gain_all) >= 1e-12:
            self._submit(lambda: self.app.service.set_falc1_main_gain_all(value))

    def _on_falc_main_use_external_input_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.main.use_external_input:
            self._submit(lambda: self.app.service.set_falc1_main_use_external_input(checked))

    def _on_falc_filter_enabled_toggled(self, filter_name: str, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        if checked != getattr(snapshot.main, f"{filter_name}_enabled"):
            self._submit(lambda: self.app.service.set_falc1_main_filter_enabled(filter_name, checked))

    def _on_falc_filter_value_changed(self, filter_name: str) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = self.window.current_filter_value(filter_name)
        if value is None:
            self.app.notifier.warning("falc_raw_value_required")
            self.window.render_snapshot(self.app.snapshot)
            return
        if value != getattr(snapshot.main, filter_name):
            self._submit(lambda: self.app.service.set_falc1_main_filter_value(filter_name, value))

    def _on_falc_unlim_enabled_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.unlim.enabled:
            self._submit(lambda: self.app.service.set_falc1_unlim_enabled(checked))

    def _on_falc_unlim_hold_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.unlim.hold:
            self._submit(lambda: self.app.service.set_falc1_unlim_hold(checked))

    def _on_falc_unlim_input_offset_finished(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = self.window.unlim_input_offset_spin.value()
        if abs(value - snapshot.unlim.input_offset) >= 1e-12:
            self._submit(lambda: self.app.service.set_falc1_unlim_input_offset(value))

    def _on_falc_unlim_output_range_finished(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = self.window.unlim_output_range_spin.value()
        if abs(value - snapshot.unlim.output_range) >= 1e-12:
            self._submit(lambda: self.app.service.set_falc1_unlim_output_range(value))

    def _on_falc_unlim_slew_rate_finished(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = int(round(self.window.unlim_slew_rate_spin.value()))
        if value != snapshot.unlim.slew_rate:
            self._submit(lambda: self.app.service.set_falc1_unlim_slew_rate(value))

    def _on_falc_unlim_sign_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.unlim.sign:
            self._submit(lambda: self.app.service.set_falc1_unlim_sign(checked))
