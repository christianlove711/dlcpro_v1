from __future__ import annotations


class StabilizationController:
    def __init__(self, app) -> None:
        self.app = app
        self.window = None

    def bind_window(self, window) -> None:
        self.window = window

    def _snapshot(self):
        if not self.app.service.is_connected or self.app.snapshot is None:
            return None
        return self.app.snapshot.stabilization

    def _submit(self, fn) -> None:
        self.app.submit_device_task(fn)

    def _on_stabilization_enabled_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.enabled:
            self._submit(lambda: self.app.service.set_stabilization_enabled(checked))

    def _on_stabilization_pd_ext_input_channel_changed(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = int(self.window.power_panel.external_physical_channel_combo.currentData())
        if value != snapshot.pd_ext_input_channel:
            self._submit(lambda: self.app.service.set_stabilization_pd_ext_input_channel(value))

    def _on_stabilization_cal_factor_finished(self) -> None:
        self._write_spin("pd_ext_cal_factor", self.window.power_panel.cal_factor_spin, self.app.service.set_stabilization_pd_ext_cal_factor)

    def _on_stabilization_cal_offset_finished(self) -> None:
        self._write_spin("pd_ext_cal_offset", self.window.power_panel.cal_offset_spin, self.app.service.set_stabilization_pd_ext_cal_offset)

    def _on_stabilization_set_level_finished(self) -> None:
        self._write_spin("setpoint", self.window.power_panel.set_level_spin, self.app.service.set_stabilization_setpoint)

    def _on_stabilization_gain_all_finished(self) -> None:
        self._write_spin("gain_all", self.window.power_panel.gain_all_spin, self.app.service.set_stabilization_gain_all)

    def _on_stabilization_gain_p_finished(self) -> None:
        self._write_spin("gain_p", self.window.power_panel.gain_p_spin, self.app.service.set_stabilization_gain_p)

    def _on_stabilization_gain_i_finished(self) -> None:
        self._write_spin("gain_i", self.window.power_panel.gain_i_spin, self.app.service.set_stabilization_gain_i)

    def _on_stabilization_gain_d_finished(self) -> None:
        self._write_spin("gain_d", self.window.power_panel.gain_d_spin, self.app.service.set_stabilization_gain_d)

    def _on_stabilization_hold_output_on_unlock_changed(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        checked = self.window.power_panel.hold_output_check.isChecked()
        if checked != snapshot.hold_output_on_unlock:
            self._submit(lambda: self.app.service.set_stabilization_hold_output_on_unlock(checked))

    def _on_stabilization_window_enabled_toggled(self, checked: bool) -> None:
        snapshot = self._snapshot()
        if snapshot is not None and checked != snapshot.window_enabled:
            self._submit(lambda: self.app.service.set_stabilization_window_enabled(checked))

    def _on_stabilization_window_level_finished(self) -> None:
        self._write_spin("window_level_low", self.window.detection_panel.level_spin, self.app.service.set_stabilization_window_level_low)

    def _on_stabilization_window_hysteresis_finished(self) -> None:
        self._write_spin("window_level_hysteresis", self.window.detection_panel.hysteresis_spin, self.app.service.set_stabilization_window_level_hysteresis)

    def _write_spin(self, attr: str, spinbox, setter) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        value = spinbox.value()
        if abs(value - getattr(snapshot, attr)) >= 1e-9:
            self._submit(lambda: setter(value))
