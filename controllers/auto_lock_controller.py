from __future__ import annotations

from time import monotonic

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from dlcpro_service import AutoLockTelemetry, LockPointSnapshot
from ui_text import TEXT


class AutoLockController:
    LOCKED_STATE = 5
    TEMPLATE_SCALE_FACTORS = (1.0, 0.7, 0.45)
    NO_CANDIDATE_ADVANCE_THRESHOLD = 5

    def __init__(self, owner) -> None:
        self.owner = owner
        self.window = None
        self._running = False
        self._mode = "idle"
        self._window_visible = False
        self._scope_window_visible = False
        self._phase_key = "auto_lock_phase_idle"
        self._status_message_key = "auto_lock_window_stopped"
        self._status_message_kwargs: dict[str, object] = {}
        self._target: LockPointSnapshot | None = None
        self._manual_target: LockPointSnapshot | None = None
        self._last_locked_target: LockPointSnapshot | None = None
        self._latest_telemetry: AutoLockTelemetry | None = None
        self._lock_deadline = 0.0
        self._last_search_signature: tuple[int, bool] | None = None
        self._last_wait_state: int | None = None
        self._pre_scan_initial_amplitude = 0.0
        self._pre_scan_target_amplitude = 0.0
        self._template_index = 0
        self._templates: tuple[dict[str, float], ...] = ()
        self._no_candidate_rounds = 0
        self._template_reacquire_pending = False
        self._scope_timer = QTimer(owner)
        self._scope_timer.setInterval(900)
        self._scope_timer.timeout.connect(self.request_scope_refresh)

    @property
    def is_running(self) -> bool:
        return self._running

    def bind_window(self, window) -> None:
        self.window = window

    def apply_texts(self) -> None:
        if self.window is None:
            return
        self.window.apply_texts(self.owner.language)
        self.window.set_phase(self.owner.language, self._phase_key)
        self.window.set_template_progress(
            self._template_index + 1 if self._templates else None,
            len(self._templates),
            self.owner.language,
        )
        self._refresh_status_message()
        self.window.set_target_point(self.target_for_display(), self.owner.language)

    def start(self, *_args) -> None:
        if self.window is None:
            return
        if not self._prepare_run():
            return

        base_amplitude = self._current_scan_amplitude()
        if abs(base_amplitude) < 1e-12:
            QMessageBox.warning(
                self.owner,
                "Warning",
                TEXT[self.owner.language]["auto_lock_warning_scan_amplitude_zero"],
            )
            return

        self._running = True
        self._mode = "auto_lock"
        self._target = None
        self._latest_telemetry = None
        self._lock_deadline = 0.0
        self._last_search_signature = None
        self._last_wait_state = None
        self._template_index = 0
        self._templates = self._build_templates(base_amplitude)
        self._no_candidate_rounds = 0
        self._template_reacquire_pending = False
        self.window.mark_live_telemetry_stopped()
        self.owner.refresh_timer.stop()
        self._sync_scope_timer()
        self._set_status_message("auto_lock_log_started")
        self.window.append_log(TEXT[self.owner.language]["auto_lock_log_started"])
        self.owner._set_busy(False)
        self._start_current_template()

    def start_pre_scan_sequence(self, *_args) -> None:
        if self.window is None:
            return
        if not self._prepare_run():
            return

        initial_amplitude = self._current_scan_amplitude()
        if abs(initial_amplitude) < 1e-12:
            QMessageBox.warning(
                self.owner,
                "Warning",
                TEXT[self.owner.language]["auto_lock_warning_scan_amplitude_zero"],
            )
            return

        shrink_ratio = self.window.config_panel.pre_scan_shrink_percent_spin.value() / 100.0
        duration_ms = self.window.config_panel.pre_scan_duration_spin.value()

        self._running = True
        self._mode = "pre_scan"
        self._target = None
        self._latest_telemetry = None
        self._lock_deadline = 0.0
        self._last_search_signature = None
        self._last_wait_state = None
        self._pre_scan_initial_amplitude = float(initial_amplitude)
        self._pre_scan_target_amplitude = float(initial_amplitude * shrink_ratio)
        self.window.mark_live_telemetry_stopped()
        self.owner.refresh_timer.stop()
        self._sync_scope_timer()
        self._set_phase("auto_lock_phase_pre_scan")
        self._set_status_message(
            "auto_lock_log_pre_scan_started",
            duration_ms=duration_ms,
            amplitude=initial_amplitude,
        )
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_pre_scan_started"].format(
                duration_ms=duration_ms,
                amplitude=initial_amplitude,
            )
        )
        self.owner._set_busy(False)

        if self.owner.snapshot is not None and self.owner.snapshot.sc_enabled:
            self._after_pre_scan_scan_enabled(self.owner.snapshot)
            return
        self._submit_snapshot(
            lambda: self.owner.service.set_sc_enabled(True),
            self._after_pre_scan_scan_enabled,
        )

    def stop(self, *_args, silent: bool = False) -> None:
        if self.window is None:
            return
        if not self._running:
            if not silent:
                self.window.set_status_message(TEXT[self.owner.language]["auto_lock_window_stopped"])
            return
        was_pre_scan = self._mode == "pre_scan"
        self._deactivate()
        if not silent:
            if was_pre_scan:
                self.window.append_log(TEXT[self.owner.language]["auto_lock_log_pre_scan_stopped"])
                self._set_status_message("auto_lock_log_pre_scan_stopped")
            else:
                self.window.append_log(TEXT[self.owner.language]["auto_lock_log_stopped"])
                self._set_status_message("auto_lock_window_stopped")

    def handle_disconnect(self) -> None:
        if self.window is None:
            return
        self._scope_timer.stop()
        self._window_visible = False
        self._scope_window_visible = False
        self._target = None
        self._manual_target = None
        self._deactivate()
        self.window.reset_state(self.owner.language)

    def handle_task_failure(self, error: object) -> None:
        if self.window is None:
            return
        if not self._running:
            return
        self._deactivate()
        if isinstance(error, Exception):
            self.window.set_status_message(self.owner.service.format_error(error))
            return
        self.window.set_status_message(str(error))

    def _deactivate(self) -> None:
        self._running = False
        self._mode = "idle"
        self._lock_deadline = 0.0
        self._last_wait_state = None
        self._pre_scan_initial_amplitude = 0.0
        self._pre_scan_target_amplitude = 0.0
        self._template_index = 0
        self._templates = ()
        self._no_candidate_rounds = 0
        self._template_reacquire_pending = False
        self._set_phase("auto_lock_phase_idle")
        self.window.set_template_progress(None, 0, self.owner.language)
        self.window.mark_live_telemetry_stopped()
        self.owner._set_busy(False)
        self._sync_scope_timer()
        if self.owner.service.is_connected and not self.owner.refresh_timer.isActive():
            self.owner.refresh_timer.start()

    def on_window_visibility_changed(self, visible: bool) -> None:
        self._window_visible = visible
        if not visible and self.window is not None:
            self.window.mark_live_telemetry_stopped()
        self._sync_scope_timer()
        if visible:
            self.request_scope_refresh()

    def on_scope_window_visibility_changed(self, visible: bool) -> None:
        self._scope_window_visible = visible
        self._sync_scope_timer()
        if visible:
            self.request_scope_refresh()

    def request_scope_refresh(self, *_args) -> None:
        if self.window is None or not self._scope_preview_requested() or self._running:
            return
        if not self.owner.service.is_connected:
            return
        self.owner._run_task(
            self.owner.service.read_auto_lock_telemetry,
            self._handle_scope_preview_telemetry,
            task_kind="poll",
        )

    def on_scope_channel1_changed(self) -> None:
        self._write_scope_setting(
            self.window.scope_window.scope_channel1_combo.currentData(),
            self.owner.service.set_scope_channel1_signal,
        )

    def on_scope_channel2_changed(self) -> None:
        self._write_scope_setting(
            self.window.scope_window.scope_channel2_combo.currentData(),
            self.owner.service.set_scope_channel2_signal,
        )

    def on_scope_update_rate_changed(self) -> None:
        self._write_scope_setting(
            self.window.scope_window.scope_update_rate_combo.currentData(),
            self.owner.service.set_scope_update_rate,
        )

    def on_scope_variant_requested(self, variant: int) -> None:
        if self.window is None or not self.owner.service.is_connected:
            return
        mode_text = self._scope_mode_text(variant)
        self.window.set_scope_status_message(
            TEXT[self.owner.language]["auto_lock_scope_switching"].format(mode=mode_text)
        )
        queued = self.owner._run_task(
            lambda requested=int(variant): self.owner.service.set_scope_variant(requested),
            lambda snapshot, requested=int(variant): self._after_scope_variant_written(snapshot, requested),
        )
        if not queued:
            return

    def on_scope_candidate_clicked(self, x: float, y: float) -> None:
        self._set_manual_target(LockPointSnapshot(x=float(x), y=float(y)))

    def on_candidate_row_clicked(self, row: int, _column: int) -> None:
        if self._latest_telemetry is None or row < 0 or row >= len(self._latest_telemetry.candidates):
            return
        self._set_manual_target(self._latest_telemetry.candidates[row])

    def target_for_display(self) -> LockPointSnapshot | None:
        if self._target is not None:
            return self._target
        return self._manual_target

    def _poll_candidates(self) -> None:
        if not self._running:
            return
        self._set_phase("auto_lock_phase_searching")
        self._submit(
            self.owner.service.read_auto_lock_telemetry,
            self._handle_candidate_telemetry,
            task_kind="poll",
        )

    def _handle_candidate_telemetry(self, telemetry: AutoLockTelemetry) -> None:
        if not self._running:
            return
        self._latest_telemetry = telemetry
        self.window.render_telemetry(telemetry, self.owner.language)
        self.window.set_target_point(self.target_for_display(), self.owner.language)

        if telemetry.lock_enabled:
            self._set_status_message("auto_lock_log_disable_lock")
            self.window.append_log(TEXT[self.owner.language]["auto_lock_log_disable_lock"])
            self._submit_snapshot(
                lambda: self.owner.service.set_lock_enabled(False),
                self._after_disabled_for_search,
            )
            return

        if not telemetry.sc_enabled:
            if self.window.config_panel.auto_enable_scan_check.isChecked():
                self._set_status_message("auto_lock_log_enable_scan")
                self.window.append_log(TEXT[self.owner.language]["auto_lock_log_enable_scan"])
                self._submit_snapshot(
                    lambda: self.owner.service.set_sc_enabled(True),
                    self._after_scan_enabled,
                )
                return
            self.window.append_log(TEXT[self.owner.language]["auto_lock_log_scan_required"])
            self._set_status_message("auto_lock_log_scan_required")
            self.stop(silent=True)
            return

        if telemetry.lock_without_lockpoint:
            self._set_status_message("auto_lock_log_candidate_mode")
            self.window.append_log(TEXT[self.owner.language]["auto_lock_log_candidate_mode"])
            self._submit_snapshot(
                lambda: self.owner.service.set_lock_without_lockpoint(False),
                self._after_candidate_mode_enabled,
            )
            return

        target = self._pick_target(telemetry)
        if target is None:
            signature = (len(telemetry.candidates), telemetry.sc_enabled)
            if signature != self._last_search_signature:
                self.window.append_log(TEXT[self.owner.language]["auto_lock_log_no_candidate"])
                self._set_status_message("auto_lock_log_no_candidate")
                self._last_search_signature = signature
            self._no_candidate_rounds += 1
            if self._no_candidate_rounds >= self.NO_CANDIDATE_ADVANCE_THRESHOLD:
                self.window.append_log(TEXT[self.owner.language]["auto_lock_log_no_candidate_advance"])
                self._set_status_message("auto_lock_log_no_candidate_advance")
                self._advance_to_next_template()
                return
            self._schedule(self.window.config_panel.search_interval_spin.value(), self._poll_candidates)
            return

        self._last_search_signature = None
        self._no_candidate_rounds = 0
        self._target = target
        self.window.set_target_point(target, self.owner.language)
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_select_target"].format(x=target.x, y=target.y)
        )
        self._set_status_message("auto_lock_log_select_target", x=target.x, y=target.y)

        self._narrow_scan_on_target()

    def _after_disabled_for_search(self, _snapshot) -> None:
        self.window.append_log(TEXT[self.owner.language]["auto_lock_log_retry_after_disable"])
        self._set_status_message("auto_lock_log_retry_after_disable")
        self._schedule(self.window.config_panel.reacquire_delay_spin.value(), self._poll_candidates)

    def _after_scan_enabled(self, _snapshot) -> None:
        self._schedule(150, self._poll_candidates)

    def _after_candidate_mode_enabled(self, _snapshot) -> None:
        self._schedule(150, self._poll_candidates)

    def _after_lock_without_lockpoint_enabled(self, _snapshot) -> None:
        self._center_on_target()

    def _narrow_scan_on_target(self) -> None:
        if not self._running or self._target is None:
            return
        template = self._current_template()
        if template is None:
            self.stop(silent=True)
            return
        self._set_phase("auto_lock_phase_pre_scan_narrowing")
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_template_narrowing"].format(
                index=int(template["index"]),
                initial=template["wide_amplitude"],
                target=template["narrow_amplitude"],
            )
        )
        self._set_status_message(
            "auto_lock_log_template_narrowing",
            index=int(template["index"]),
            initial=template["wide_amplitude"],
            target=template["narrow_amplitude"],
        )
        self._submit_snapshot(
            lambda value=template["narrow_amplitude"]: self.owner.service.set_sc_amplitude(value),
            self._after_narrow_scan_written,
        )

    def _after_narrow_scan_written(self, _snapshot) -> None:
        if not self._running:
            return
        self.window.append_log(TEXT[self.owner.language]["auto_lock_log_enable_center_lock"])
        self._set_status_message("auto_lock_log_enable_center_lock")
        self._submit_snapshot(
            lambda: self.owner.service.set_lock_without_lockpoint(True),
            self._after_lock_without_lockpoint_enabled,
        )

    def _center_on_target(self) -> None:
        if not self._running or self._target is None:
            return
        self._set_phase("auto_lock_phase_centering")
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_move_offset"].format(x=self._target.x)
        )
        self._set_status_message("auto_lock_log_move_offset", x=self._target.x)
        # SDK example confirms candidate x is on the same displayed x-axis as the scan trace;
        # Manual.md states Lock Without Lockpoint locks at the spectrum center (Offset).
        self._submit_snapshot(
            lambda: self.owner.service.set_sc_offset(self._target.x),
            self._after_offset_written,
        )

    def _after_offset_written(self, _snapshot) -> None:
        if not self._running:
            return
        self._set_phase("auto_lock_phase_settling")
        self._schedule(self.window.config_panel.settle_delay_spin.value(), self._enable_lock)

    def _enable_lock(self) -> None:
        if not self._running:
            return
        self._set_phase("auto_lock_phase_locking")
        self.window.append_log(TEXT[self.owner.language]["auto_lock_log_enable_lock"])
        self._set_status_message("auto_lock_log_enable_lock")
        self._lock_deadline = monotonic() + (
            self.window.config_panel.lock_timeout_spin.value() / 1000.0
        )
        self._last_wait_state = None
        self._submit_snapshot(
            lambda: self.owner.service.set_lock_enabled(True),
            self._after_lock_enabled,
        )

    def _after_lock_enabled(self, _snapshot) -> None:
        self._schedule(180, self._poll_lock_state)

    def _poll_lock_state(self) -> None:
        if not self._running:
            return
        self._submit(
            self.owner.service.read_auto_lock_telemetry,
            self._handle_lock_state_telemetry,
            task_kind="poll",
        )

    def _handle_lock_state_telemetry(self, telemetry: AutoLockTelemetry) -> None:
        if not self._running:
            return
        self._latest_telemetry = telemetry
        self.window.render_telemetry(telemetry, self.owner.language)
        self.window.set_target_point(self.target_for_display(), self.owner.language)

        if telemetry.lock_state == self.LOCKED_STATE:
            self._last_locked_target = self._target
            self.window.append_log(TEXT[self.owner.language]["auto_lock_log_lock_success"])
            self._set_status_message("auto_lock_log_lock_success")
            if self.window.config_panel.watch_after_lock_check.isChecked():
                self._set_phase("auto_lock_phase_monitoring")
                self._schedule(self.window.config_panel.monitor_interval_spin.value(), self._poll_monitor)
                return
            self._deactivate()
            return

        current_state = -1 if telemetry.lock_state is None else telemetry.lock_state
        if self._last_wait_state != current_state:
            self.window.append_log(
                TEXT[self.owner.language]["auto_lock_log_lock_waiting"].format(state=current_state)
            )
            self._set_status_message("auto_lock_log_lock_waiting", state=current_state)
            self._last_wait_state = current_state

        if monotonic() >= self._lock_deadline:
            self.window.append_log(TEXT[self.owner.language]["auto_lock_log_lock_timeout"])
            self._set_status_message("auto_lock_log_lock_timeout")
            self._begin_reacquire(telemetry)
            return

        self._schedule(self.window.config_panel.monitor_interval_spin.value(), self._poll_lock_state)

    def _poll_monitor(self) -> None:
        if not self._running:
            return
        self._submit(
            self.owner.service.read_auto_lock_telemetry,
            self._handle_monitor_telemetry,
            task_kind="poll",
        )

    def _handle_monitor_telemetry(self, telemetry: AutoLockTelemetry) -> None:
        if not self._running:
            return
        self._latest_telemetry = telemetry
        self.window.render_telemetry(telemetry, self.owner.language)
        self.window.set_target_point(self.target_for_display(), self.owner.language)

        if telemetry.lock_enabled and telemetry.lock_state == self.LOCKED_STATE:
            self._schedule(self.window.config_panel.monitor_interval_spin.value(), self._poll_monitor)
            return

        self.window.append_log(TEXT[self.owner.language]["auto_lock_log_monitor_lost"])
        self._set_status_message("auto_lock_log_monitor_lost")
        self._begin_reacquire(telemetry)

    def _begin_reacquire(self, telemetry: AutoLockTelemetry) -> None:
        if not self._running:
            return
        self._set_phase("auto_lock_phase_reacquiring")
        self._template_reacquire_pending = True
        if telemetry.lock_enabled:
            self._submit_snapshot(
                lambda: self.owner.service.set_lock_enabled(False),
                self._after_disabled_for_reacquire,
            )
            return
        self._advance_to_next_template()

    def _after_disabled_for_reacquire(self, _snapshot) -> None:
        if not self._running:
            return
        self._advance_to_next_template()

    def _advance_to_next_template(self) -> None:
        if not self._running:
            return
        next_index = self._template_index + 1
        if next_index >= len(self._templates):
            self.window.append_log(TEXT[self.owner.language]["auto_lock_log_templates_exhausted"])
            self._set_status_message("auto_lock_log_templates_exhausted")
            self.stop(silent=True)
            return
        previous = self._template_index + 1
        self._template_index = next_index
        current = self._template_index + 1
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_retry_template"].format(
                previous=previous,
                current=current,
            )
        )
        self._set_status_message(
            "auto_lock_log_retry_template",
            previous=previous,
            current=current,
        )
        self._schedule(self.window.config_panel.reacquire_delay_spin.value(), self._start_current_template)

    def _pick_target(self, telemetry: AutoLockTelemetry) -> LockPointSnapshot | None:
        points = list(telemetry.candidates)
        if not points:
            return None

        if self._manual_target is not None:
            reference = self._manual_target
            return min(
                points,
                key=lambda point: ((point.x - reference.x) ** 2 + (point.y - reference.y) ** 2),
            )

        strategy = str(self.window.config_panel.strategy_combo.currentData() or "nearest_center")
        if strategy == "nearest_last" and self._last_locked_target is not None:
            reference_x = self._last_locked_target.x
            return min(points, key=lambda point: abs(point.x - reference_x))
        if strategy == "highest_y":
            return max(points, key=lambda point: (point.y, -abs(point.x - telemetry.sc_offset)))
        if strategy == "leftmost":
            return min(points, key=lambda point: point.x)
        if strategy == "rightmost":
            return max(points, key=lambda point: point.x)
        return min(points, key=lambda point: abs(point.x - telemetry.sc_offset))

    def _build_templates(self, base_amplitude: float) -> tuple[dict[str, float], ...]:
        base = abs(float(base_amplitude))
        shrink_ratio = self.window.config_panel.pre_scan_shrink_percent_spin.value() / 100.0
        templates: list[dict[str, float]] = []
        for index, factor in enumerate(self.TEMPLATE_SCALE_FACTORS, start=1):
            wide = max(base * factor, 1e-6)
            narrow = max(wide * shrink_ratio, 1e-6)
            templates.append(
                {
                    "index": float(index),
                    "wide_amplitude": wide,
                    "narrow_amplitude": narrow,
                }
            )
        return tuple(templates)

    def _current_template(self) -> dict[str, float] | None:
        if 0 <= self._template_index < len(self._templates):
            return self._templates[self._template_index]
        return None

    def _start_current_template(self) -> None:
        if not self._running:
            return
        template = self._current_template()
        if template is None:
            self.window.append_log(TEXT[self.owner.language]["auto_lock_log_templates_exhausted"])
            self._set_status_message("auto_lock_log_templates_exhausted")
            self.stop(silent=True)
            return
        self._target = None
        self._last_search_signature = None
        self._last_wait_state = None
        self._no_candidate_rounds = 0
        self._template_reacquire_pending = False
        self._set_phase("auto_lock_phase_pre_scan")
        self.window.set_template_progress(self._template_index + 1, len(self._templates), self.owner.language)
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_template_start"].format(
                index=int(template["index"]),
                wide=template["wide_amplitude"],
                narrow=template["narrow_amplitude"],
            )
        )
        self._set_status_message(
            "auto_lock_log_template_start",
            index=int(template["index"]),
            wide=template["wide_amplitude"],
            narrow=template["narrow_amplitude"],
        )
        self._submit_snapshot(
            lambda value=template["wide_amplitude"]: self.owner.service.set_sc_amplitude(value),
            self._after_template_wide_amplitude_written,
        )

    def _after_template_wide_amplitude_written(self, _snapshot) -> None:
        if not self._running:
            return
        if self.owner.snapshot is not None and self.owner.snapshot.sc_enabled:
            self._after_template_scan_enabled(self.owner.snapshot)
            return
        if self.window.config_panel.auto_enable_scan_check.isChecked():
            self.window.append_log(TEXT[self.owner.language]["auto_lock_log_enable_scan"])
            self._set_status_message("auto_lock_log_enable_scan")
            self._submit_snapshot(
                lambda: self.owner.service.set_sc_enabled(True),
                self._after_template_scan_enabled,
            )
            return
        self.window.append_log(TEXT[self.owner.language]["auto_lock_log_scan_required"])
        self._set_status_message("auto_lock_log_scan_required")
        self.stop(silent=True)

    def _after_template_scan_enabled(self, _snapshot) -> None:
        if not self._running:
            return
        template = self._current_template()
        if template is None:
            self.stop(silent=True)
            return
        duration_ms = self.window.config_panel.pre_scan_duration_spin.value()
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_template_running"].format(
                index=int(template["index"]),
                duration_ms=duration_ms,
                amplitude=template["wide_amplitude"],
            )
        )
        self._set_status_message(
            "auto_lock_log_template_running",
            index=int(template["index"]),
            duration_ms=duration_ms,
            amplitude=template["wide_amplitude"],
        )
        self._schedule(duration_ms, self._poll_candidates)

    def _submit(self, fn, on_success, task_kind: str) -> None:
        if not self._running:
            return
        queued = self.owner._run_task(
            fn,
            lambda result: self._handle_success(on_success, result),
            task_kind=task_kind,
        )
        if queued:
            return
        self._schedule(60, lambda: self._submit(fn, on_success, task_kind))

    def _submit_snapshot(self, fn, on_success) -> None:
        self._submit(
            fn,
            lambda snapshot: self._handle_snapshot_and_continue(snapshot, on_success),
            task_kind="action",
        )

    def _handle_success(self, on_success, result) -> None:
        if not self._running:
            return
        on_success(result)

    def _handle_snapshot_and_continue(self, snapshot, on_success) -> None:
        self.owner._on_snapshot_updated(snapshot)
        if not self._running:
            return
        on_success(snapshot)

    def _schedule(self, delay_ms: int, callback) -> None:
        QTimer.singleShot(delay_ms, lambda: callback() if self._running else None)

    def _set_phase(self, phase_key: str) -> None:
        self._phase_key = phase_key
        self.window.set_phase(self.owner.language, phase_key)

    def _set_status_message(self, text_key: str, **kwargs) -> None:
        self._status_message_key = text_key
        self._status_message_kwargs = kwargs
        self._refresh_status_message()

    def _refresh_status_message(self) -> None:
        if self.window is None:
            return
        template = TEXT[self.owner.language][self._status_message_key]
        self.window.set_status_message(template.format(**self._status_message_kwargs))

    def _handle_scope_preview_telemetry(self, telemetry: AutoLockTelemetry) -> None:
        self._latest_telemetry = telemetry
        if self.window is None:
            return
        self.window.render_telemetry(telemetry, self.owner.language)
        self.window.set_target_point(self.target_for_display(), self.owner.language)

    def _write_scope_setting(self, raw_value, setter) -> None:
        if self.window is None or not self.owner.service.is_connected:
            return
        if raw_value is None:
            return
        self.owner._run_task(
            lambda value=int(raw_value): setter(value),
            self._after_scope_setting_written,
        )

    def _after_scope_setting_written(self, snapshot) -> None:
        self.owner._on_snapshot_updated(snapshot)
        self.request_scope_refresh()

    def _after_scope_variant_written(self, snapshot, variant: int) -> None:
        self.owner._on_snapshot_updated(snapshot)
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_scope_variant"].format(mode=self._scope_mode_text(variant))
        )
        self.request_scope_refresh()

    def _set_manual_target(self, point: LockPointSnapshot) -> None:
        self._manual_target = point
        if self.window is None:
            return
        self.window.set_target_point(point, self.owner.language)
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_click_target"].format(x=point.x, y=point.y)
        )
        self.window.set_scope_status_message(TEXT[self.owner.language]["auto_lock_scope_click_hint"])
        if not self._running:
            self._set_status_message("auto_lock_log_click_target", x=point.x, y=point.y)

    def _sync_scope_timer(self) -> None:
        if self._scope_preview_requested() and self.owner.service.is_connected and not self._running:
            if not self._scope_timer.isActive():
                self._scope_timer.start()
            return
        self._scope_timer.stop()

    def _prepare_run(self) -> bool:
        if self._running:
            return False
        if not self.owner.service.is_connected:
            QMessageBox.warning(
                self.owner,
                "Warning",
                TEXT[self.owner.language]["auto_lock_warning_not_connected"],
            )
            return False
        if self.owner.pending_future is not None:
            QMessageBox.warning(
                self.owner,
                "Warning",
                TEXT[self.owner.language]["auto_lock_warning_busy"],
            )
            return False
        return True

    def _current_scan_amplitude(self) -> float:
        if self.owner.snapshot is not None:
            return float(self.owner.snapshot.sc_amplitude)
        return float(self.owner.scan_amplitude_spin.value())

    def _after_pre_scan_scan_enabled(self, _snapshot) -> None:
        if not self._running or self._mode != "pre_scan":
            return
        duration_ms = self.window.config_panel.pre_scan_duration_spin.value()
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_pre_scan_running"].format(
                duration_ms=duration_ms,
                amplitude=self._pre_scan_initial_amplitude,
            )
        )
        self._set_status_message(
            "auto_lock_log_pre_scan_running",
            duration_ms=duration_ms,
            amplitude=self._pre_scan_initial_amplitude,
        )
        self._schedule(duration_ms, self._shrink_pre_scan_range)

    def _shrink_pre_scan_range(self) -> None:
        if not self._running or self._mode != "pre_scan":
            return
        self._set_phase("auto_lock_phase_pre_scan_narrowing")
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_pre_scan_narrowing"].format(
                initial=self._pre_scan_initial_amplitude,
                target=self._pre_scan_target_amplitude,
            )
        )
        self._set_status_message(
            "auto_lock_log_pre_scan_narrowing",
            initial=self._pre_scan_initial_amplitude,
            target=self._pre_scan_target_amplitude,
        )
        self._submit_snapshot(
            lambda: self.owner.service.set_sc_amplitude(self._pre_scan_target_amplitude),
            self._after_pre_scan_range_shrunk,
        )

    def _after_pre_scan_range_shrunk(self, _snapshot) -> None:
        if not self._running or self._mode != "pre_scan":
            return
        self.window.append_log(
            TEXT[self.owner.language]["auto_lock_log_pre_scan_complete"].format(
                target=self._pre_scan_target_amplitude
            )
        )
        self._set_status_message(
            "auto_lock_log_pre_scan_complete",
            target=self._pre_scan_target_amplitude,
        )
        self._deactivate()

    def _scope_preview_requested(self) -> bool:
        return self._window_visible or self._scope_window_visible

    def _scope_mode_text(self, variant: int) -> str:
        t = TEXT[self.owner.language]
        if variant == 0:
            return t["auto_lock_scope_mode_xy"]
        if variant == 1:
            return t["auto_lock_scope_mode_time"]
        if variant == 2:
            return t["auto_lock_scope_mode_frequency"]
        return str(variant)
