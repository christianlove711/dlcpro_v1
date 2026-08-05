from __future__ import annotations

import math
import time

from PySide6.QtWidgets import QMessageBox

from controllers.auto_lock_acquisition import AcquisitionFrame, FpgaAcquisitionConfig
from controllers.auto_lock_settings import AutoLockSettings
from controllers.auto_lock_strategies import SignalAnalysis, create_auto_lock_strategy
from ui_text import TEXT


class AutoLockController:
    def __init__(self, owner) -> None:
        self.owner = owner
        self.window = None
        self._running = False
        self._phase = "idle"
        self._status_message = ""
        self._backend = None
        self._device_write_pending = False
        self._last_frame: AcquisitionFrame | None = None
        self._last_analysis: SignalAnalysis | None = None
        self._settings = AutoLockSettings()
        self._strategy = create_auto_lock_strategy(self._settings.strategy)
        self._start_offset = 0.0
        self._current_offset = 0.0
        self._current_amplitude = 0.0
        self._last_good_offset = 0.0
        self._last_good_amplitude = 0.0
        self._offset_attempt = 0
        self._center_stable = 0
        self._ready_started = False
        self._probe_previous: tuple[float, float] | None = None
        self._offset_to_peak_gain: float | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_acquisition_connected(self) -> bool:
        return self._backend is not None

    def bind_window(self, window) -> None:
        self.window = window
        self._push_status()

    def apply_texts(self) -> None:
        if self.window is not None:
            self.window.apply_texts(self.owner.language)
            self._push_status()

    def render_snapshot(self, snapshot) -> None:
        if snapshot is None:
            return
        self._current_offset = float(snapshot.sc_offset)
        self._current_amplitude = float(snapshot.sc_amplitude)
        if self.window is not None:
            self.window.render_snapshot(snapshot)

    def set_writable(self, writable: bool, previewable: bool, running: bool) -> None:
        if self.window is not None:
            self.window.set_writable(writable, previewable, running)

    def handle_disconnect(self) -> None:
        self.stop(silent=True)
        self.disconnect_acquisition()
        if self.window is not None:
            self.window.reset_state(self.owner.language)

    def handle_task_failure(self, error: object) -> None:
        self._log(f"device task failed: {self.owner.service.format_error(error) if isinstance(error, Exception) else error}")
        self.stop(silent=True)

    def shutdown(self) -> None:
        self.stop(silent=True)
        self.disconnect_acquisition()

    def open_falc_window(self) -> None:
        self.owner.show_falc_window()

    def show_log_window(self) -> None:
        if self.window is not None:
            self.window.open_log_window()

    def show_algorithm_config(self) -> None:
        if self.window is not None:
            self.window.open_algorithm_config_window(self._settings)

    def apply_algorithm_settings(self, settings: AutoLockSettings) -> None:
        self._settings = settings
        self._strategy = create_auto_lock_strategy(settings.strategy)
        self._log(
            "algorithm config updated: "
            f"strategy={self._strategy.key}, "
            f"wide={settings.wide_amplitude:.6f}, min={settings.min_amplitude:.6f}, "
            f"offset_step={settings.offset_step:.6f}, "
            f"peak_tol={settings.peak_center_tolerance:.4f}, "
            f"zero_tol={settings.zero_center_tolerance:.4f}, guard_tol={settings.transmission_guard_tolerance:.4f}"
        )

    def connect_acquisition(self) -> None:
        if self.window is None:
            return
        t = TEXT[self.owner.language]
        try:
            config: FpgaAcquisitionConfig = self.window.acquisition_config()
            config.validate()
        except ValueError as exc:
            QMessageBox.warning(self.window, t["warning_title"], str(exc))
            return
        self._log(t["auto_lock_fpga_pending"])
        self.window.set_acquisition_status(False, t["auto_lock_fpga_pending"])
        QMessageBox.information(self.window, t["auto_lock_fpga_pending_title"], t["auto_lock_fpga_pending"])

    def disconnect_acquisition(self) -> None:
        self._backend = None
        if self.window is not None:
            self.window.set_acquisition_status(False, "")
        if not self._running:
            self._set_phase("idle")

    def start_preview(self) -> None:
        return

    def stop_preview(self) -> None:
        return

    def request_frame(self) -> None:
        return

    def start(self) -> None:
        if self._running:
            return
        t = TEXT[self.owner.language]
        if not self.owner.service.is_connected or self.owner.snapshot is None:
            QMessageBox.warning(self.owner, t["warning_title"], t["auto_lock_warn_dlc_not_connected"])
            return
        if self._backend is None:
            QMessageBox.warning(self.owner, t["warning_title"], t["auto_lock_fpga_pending"])
            return
        scan_error = self._scan_configuration_error(self.owner.snapshot)
        if scan_error:
            QMessageBox.warning(self.owner, t["warning_title"], scan_error)
            return
        self._settings = self.window.current_algorithm_settings() if self.window is not None else self._settings
        self._strategy = create_auto_lock_strategy(self._settings.strategy)
        self._running = True
        self._ready_started = False
        self._device_write_pending = False
        self._offset_attempt = 0
        self._center_stable = 0
        self._offset_to_peak_gain = None
        self._probe_previous = None
        self._start_offset = float(self.owner.snapshot.sc_offset)
        self._current_offset = self._start_offset
        self._current_amplitude = float(self.owner.snapshot.sc_amplitude)
        self._last_good_offset = self._current_offset
        self._last_good_amplitude = self._current_amplitude
        self.owner.set_background_refresh_enabled(False)
        self.owner.set_operation_busy(False)
        self._log("one-click AutoLock started")
        self._set_phase("prepare")
        if not self.owner.snapshot.sc_enabled:
            self._submit_device(lambda: self.owner.service.set_sc_enabled(True), self._after_scan_enabled, "enable Scan")
            return
        self._after_scan_enabled(self.owner.snapshot)

    def stop(self, *_args, silent: bool = False) -> None:
        if not self._running:
            return
        self._running = False
        self._ready_started = False
        self._device_write_pending = False
        self._set_phase("idle")
        if not silent:
            self._log("AutoLock stopped")
        self.owner.set_operation_busy(False)
        self.owner.set_background_refresh_enabled(True)

    def poll_acquisition_future(self) -> None:
        return

    def _handle_frame(self, frame: AcquisitionFrame) -> None:
        self._last_frame = frame
        analysis = self._analyze_frame(frame)
        self._last_analysis = analysis
        if self.window is not None:
            self.window.render_frame(frame, analysis)
        if self._running:
            self._advance_algorithm(analysis)

    def _after_scan_enabled(self, snapshot) -> None:
        if not self._running:
            return
        self.owner.publish_snapshot(snapshot)
        self._current_offset = float(snapshot.sc_offset)
        self._current_amplitude = float(snapshot.sc_amplitude)
        self._log("Scan is enabled for search")
        target = self._settings.wide_amplitude
        if abs(target) > 1e-12 and abs(target - self._current_amplitude) > 1e-9:
            self._submit_device(
                lambda value=target: self.owner.service.set_sc_amplitude(value),
                self._after_wide_amplitude_written,
                f"set wide Scan Amplitude {target:.6f}",
            )
            return
        self._after_wide_amplitude_written(snapshot)

    def _after_wide_amplitude_written(self, snapshot) -> None:
        if not self._running:
            return
        self.owner.publish_snapshot(snapshot)
        self._current_amplitude = float(snapshot.sc_amplitude)
        self._last_good_amplitude = self._current_amplitude
        self._set_phase("coarse_search")
        self.start_preview()

    def _advance_algorithm(self, analysis: SignalAnalysis) -> None:
        if self._device_write_pending or self._ready_started:
            return
        if self._phase in {"prepare", "connecting_acquisition", "idle"}:
            return
        if self._phase == "coarse_search":
            self._coarse_step(analysis)
            return
        if self._phase in {"center_peak", "verify_shrink", "recover_peak"}:
            self._center_or_shrink_step(analysis)

    def _coarse_step(self, analysis: SignalAnalysis) -> None:
        if self._strategy.coarse_found(analysis):
            self._set_phase("center_peak")
            self._last_good_offset = self._current_offset
            self._last_good_amplitude = self._current_amplitude
            self._log(self._strategy.candidate_found_message(analysis))
            return
        if self._offset_attempt >= self._settings.max_offset_attempts:
            self._log(self._strategy.search_exhausted_message())
            self.stop(silent=True)
            return
        target = self._start_offset + self._next_offset_delta()
        self._offset_attempt += 1
        self._write_offset(target, self._strategy.no_candidate_message(self._offset_attempt))

    def _center_or_shrink_step(self, analysis: SignalAnalysis) -> None:
        control_fraction = self._strategy.control_fraction(analysis)
        if not self._strategy.control_ready(analysis) or control_fraction is None:
            self._set_phase("recover_peak")
            self._center_stable = 0
            self._log(self._strategy.lost_message())
            self._write_amplitude(self._last_good_amplitude, self._strategy.restore_amplitude_message())
            return

        self._last_good_offset = self._current_offset
        self._last_good_amplitude = self._current_amplitude
        center_error = control_fraction - 0.5
        if abs(center_error) > self._strategy.center_tolerance(self._settings, analysis):
            self._center_stable = 0
            target = self._next_center_offset(control_fraction, center_error)
            self._write_offset(target, self._strategy.center_message(center_error))
            return

        if not self._strategy.guard_ready(analysis):
            self._center_stable = 0
            self._log(self._strategy.guard_not_ready_message(analysis))
            return

        self._center_stable += 1
        self._log(self._strategy.ready_candidate_message(self._center_stable, self._settings.stable_frames, analysis))
        if self._center_stable < self._settings.stable_frames:
            return

        if abs(self._current_amplitude) > self._settings.min_amplitude + 1e-12:
            previous = self._current_amplitude
            target = max(self._settings.min_amplitude, abs(self._current_amplitude) * self._settings.shrink_factor)
            self._center_stable = 0
            self._set_phase("verify_shrink")
            self._write_amplitude(target, f"shrink Scan Amplitude {previous:.6f}->{target:.6f}")
            return

        self._finish_ready()

    def _next_center_offset(self, signal_fraction: float, center_error: float) -> float:
        if self._probe_previous is not None:
            previous_offset, previous_fraction = self._probe_previous
            delta_offset = self._current_offset - previous_offset
            delta_fraction = signal_fraction - previous_fraction
            if abs(delta_offset) > 1e-12 and abs(delta_fraction) > 1e-5:
                self._offset_to_peak_gain = delta_fraction / delta_offset
                self._probe_previous = None
                self._log(
                    f"measured offset-to-{self._strategy.control_label} response: "
                    f"{self._offset_to_peak_gain:+.4f} fraction/V"
                )

        if self._offset_to_peak_gain is None:
            probe = self._current_offset + max(self._settings.offset_step * 0.5, 1e-6)
            self._probe_previous = (self._current_offset, signal_fraction)
            return probe

        if abs(self._offset_to_peak_gain) < 1e-9:
            return self._current_offset - math.copysign(self._settings.offset_step, center_error)
        correction = -center_error / self._offset_to_peak_gain
        limited = max(-2.0 * self._settings.offset_step, min(2.0 * self._settings.offset_step, correction))
        return self._current_offset + limited * self._settings.offset_correction_gain

    def _finish_ready(self) -> None:
        if self._ready_started:
            return
        self._ready_started = True
        self._set_phase("ready")
        self._log(
            f"Ready for FALC: Scan Offset={self._current_offset:.6f}, "
            f"Scan Amplitude={self._current_amplitude:.6f}. Closing Scan before FALC enable."
        )
        self._submit_device(lambda: self.owner.service.set_sc_enabled(False), self._after_scan_disabled_for_falc, "disable Scan")

    def _after_scan_disabled_for_falc(self, snapshot) -> None:
        self.owner.publish_snapshot(snapshot)
        if snapshot.falc1 is None:
            self._log("FALC module is not available; cannot auto-enable FALC")
            self.stop(silent=True)
            return
        path = int(snapshot.falc1.path_selection)
        if path == 0:
            self._log("FALC Path Selection is None; cannot auto-enable FALC")
            self.stop(silent=True)
            return
        self._set_phase("enable_falc")
        self._log(f"enabling FALC by current Path Selection={path}")
        if path == 1:
            self._submit_device(lambda: self.owner.service.set_falc1_unlim_enabled(True), self._after_falc_enabled, "enable FALC Unlim")
            return
        if path == 2:
            self._submit_device(lambda: self.owner.service.set_falc1_main_enabled(True), self._after_falc_enabled, "enable FALC Main")
            return
        self._submit_device(lambda: self.owner.service.set_falc1_unlim_enabled(True), self._after_unlim_enabled_for_falc, "enable FALC Unlim")

    def _after_unlim_enabled_for_falc(self, snapshot) -> None:
        self.owner.publish_snapshot(snapshot)
        self._submit_device(lambda: self.owner.service.set_falc1_main_enabled(True), self._after_falc_enabled, "enable FALC Main")

    def _after_falc_enabled(self, snapshot) -> None:
        self.owner.publish_snapshot(snapshot)
        self._set_phase("locked")
        self._log("FALC enabled. AutoLock completed.")
        self._running = False
        self._ready_started = False
        self._device_write_pending = False
        self.owner.set_operation_busy(False)
        self.owner.set_background_refresh_enabled(True)

    def _write_offset(self, value: float, reason: str) -> None:
        self._log(f"{reason}: Scan Offset {self._current_offset:.6f}->{value:.6f}")
        self._submit_device(lambda target=value: self.owner.service.set_sc_offset(target), self._after_offset_written, "write Scan Offset")

    def _after_offset_written(self, snapshot) -> None:
        self.owner.publish_snapshot(snapshot)
        self._current_offset = float(snapshot.sc_offset)

    def _write_amplitude(self, value: float, reason: str) -> None:
        self._log(f"{reason}: Scan Amplitude {self._current_amplitude:.6f}->{value:.6f}")
        self._submit_device(lambda target=value: self.owner.service.set_sc_amplitude(target), self._after_amplitude_written, "write Scan Amplitude")

    def _after_amplitude_written(self, snapshot) -> None:
        self.owner.publish_snapshot(snapshot)
        self._current_amplitude = float(snapshot.sc_amplitude)

    def _submit_device(self, fn, on_success, description: str) -> None:
        if not self._running and "FALC" not in description:
            return
        self._device_write_pending = True

        def wrapped_success(snapshot) -> None:
            self._device_write_pending = False
            self._log(f"device write ok: {description}")
            on_success(snapshot)

        queued = self.owner.submit_device_task(fn, wrapped_success)
        if not queued:
            self._device_write_pending = False
            self._log(f"device write queued failed/busy: {description}")

    def _next_offset_delta(self) -> float:
        step_index = self._offset_attempt + 1
        magnitude = (step_index + 1) // 2
        sign = 1.0 if step_index % 2 == 1 else -1.0
        return sign * magnitude * self._settings.offset_step

    def _analyze_frame(self, frame: AcquisitionFrame) -> SignalAnalysis:
        return self._strategy.analyze(frame, self._settings)

    def _scan_configuration_error(self, snapshot) -> str:
        t = TEXT[self.owner.language]
        problems: list[str] = []
        if int(snapshot.sc_output_channel) != 50:
            problems.append(t["auto_lock_scan_invalid_output"].format(value=snapshot.sc_output_channel))
        if abs(float(snapshot.sc_frequency) - 1.0) > 0.05:
            problems.append(t["auto_lock_scan_invalid_frequency"].format(value=snapshot.sc_frequency))
        if int(snapshot.sc_signal_type) != 1:
            problems.append(t["auto_lock_scan_invalid_shape"].format(value=snapshot.sc_signal_type))
        if not problems:
            return ""
        return t["auto_lock_scan_invalid_header"] + "\n" + "\n".join(problems)

    def _set_phase(self, phase: str) -> None:
        self._phase = phase
        self._push_status()

    def _push_status(self) -> None:
        if self.window is not None:
            self.window.set_phase(self._phase)

    def _log(self, text: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        line = f"{stamp}  {text}"
        if self.window is not None:
            self.window.append_log(line)
