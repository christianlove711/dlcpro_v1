"""Qt coordinator for raw-ADC peak balancing and DLC pro scan writes."""
from __future__ import annotations

import time

from PySide6.QtCore import QObject, QTimer, Signal

from .adc_peak_balance_algorithm import (
    CarrierFingerprint, ControlAction,
    PeakBalanceEngine,
    PeakBalanceSettings,
    PeakObservation,
    analyze_carrier,
)


class AdcPeakBalanceController(QObject):
    running_changed = Signal(bool)
    status_changed = Signal(dict)
    log_message = Signal(str)
    stopped = Signal(str)

    def __init__(self, ring, dlc_session, acquisition_running, parent=None):
        super().__init__(parent)
        self.ring = ring
        self.session = dlc_session
        self.acquisition_running = acquisition_running
        self.engine: PeakBalanceEngine | None = None
        self.settings: PeakBalanceSettings | None = None
        self.running = False
        self.pending_write = False
        self.pending_kind = ""
        self.gate_bin: int | None = None
        self.available_after = 0.0
        self.required_cycles = 4.0
        self.scan_frequency = 0.0
        self.observe_only = True
        self.start_offset: float | None = None
        self.start_amplitude: float | None = None
        self.scan_unit = ""
        self.step_profile = "用户设定"
        self.last_observation = PeakObservation(False, "尚未开始")
        self.restore_queue: list[tuple[str, float]] = []
        self.manual_advice = "尚未开始观察"
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._tick)
        self.session.write_snapshot_changed.connect(self._write_completed)
        self.session.connection_changed.connect(self._connection_changed)
        self.session.error.connect(self._session_error)

    def start(self, settings: PeakBalanceSettings, *,
              observe_only: bool = False) -> None:
        if self.running:
            return
        if not self.acquisition_running():
            raise RuntimeError("请先连接PL板卡并启动ADC采集")
        if not self.session.is_connected:
            raise RuntimeError("请先连接DLC pro")
        snapshot = self.session.snapshot()
        if snapshot is None:
            raise RuntimeError("尚未取得DLC pro扫描参数")
        if not bool(snapshot.sc_enabled):
            raise RuntimeError("请先在DLC pro中启用Scan")
        frequency = float(snapshot.sc_frequency)
        if frequency <= 0:
            raise RuntimeError("DLC pro扫描频率必须大于0")
        if 2.0 / frequency > self.ring.HISTORY_SECONDS:
            raise RuntimeError("当前扫描频率过低，20秒原始码历史不足以覆盖两个周期")
        # The project's verified Scan configuration uses signal type 1 for the
        # triangle waveform required by the alternating-interval algorithm.
        if int(snapshot.sc_signal_type) != 1:
            raise RuntimeError("当前算法只允许已确认的三角扫描波形")
        settings = settings.validated()
        engine = PeakBalanceEngine(settings)
        engine.start(float(snapshot.sc_offset), float(snapshot.sc_amplitude))
        self.scan_unit = str(getattr(snapshot, "sc_unit", "") or "").strip()
        self._apply_amplitude_step_profile(engine, self.scan_unit)
        self.settings = settings
        self.engine = engine
        self.scan_frequency = frequency
        self.observe_only = bool(observe_only)
        self.start_offset = float(snapshot.sc_offset)
        self.start_amplitude = float(snapshot.sc_amplitude)
        self.pending_write = False
        self.restore_queue.clear()
        self.manual_advice = "正在采集4个完整扫描周期，请暂时不要调节"
        self.gate_bin = self._latest_bin()
        self._wait_for_new_window(4.0, keep_gate=True)
        self.running = True
        self.running_changed.emit(True)
        self._log(
            f"启动{'观察模式（禁止写入）' if self.observe_only else '自动控制模式'}："
            f"Offset={self.start_offset:.6f}，"
            f"Amplitude={self.start_amplitude:.6f}，频率={frequency:g} Hz"
        )
        self.timer.start()
        self._emit_status(PeakObservation(False, "采集4个扫描周期建立00模基准"))

    def stop(self, reason: str = "用户停止") -> None:
        if not self.running:
            return
        self.running = False
        self.timer.stop()
        self.pending_write = False
        self.running_changed.emit(False)
        self._log(reason)
        self.stopped.emit(reason)

    def restore_start_values(self) -> None:
        if self.start_offset is None or self.start_amplitude is None:
            raise RuntimeError("本次尚未保存启动Offset/Amplitude")
        self.stop("停止自动控制并恢复启动参数")
        self.restore_queue = [
            ("offset", float(self.start_offset)),
            ("amplitude", float(self.start_amplitude)),
        ]
        self._run_restore_queue()

    def _run_restore_queue(self) -> None:
        if self.pending_write or not self.restore_queue:
            return
        kind, value = self.restore_queue.pop(0)
        self.pending_write = True
        self.pending_kind = f"restore_{kind}"
        if kind == "offset":
            self.session.set_scan_offset(value)
        else:
            self.session.set_scan_amplitude(value)

    def _latest_bin(self) -> int | None:
        frame = self.ring.raw_history(0.01)
        return int(frame.bin_indices[-1]) if frame.bin_indices.size else None

    def _tick(self) -> None:
        if not self.running or self.pending_write or self.engine is None:
            return
        if not self.acquisition_running():
            self.stop("ADC采集已停止，自动锁频终止")
            return
        snapshot = self.session.snapshot()
        if snapshot is None or not self.session.is_connected:
            self.stop("DLC pro连接中断，自动锁频终止")
            return
        frequency = float(snapshot.sc_frequency)
        if frequency <= 0:
            self.stop("DLC pro扫描频率无效")
            return
        if not bool(snapshot.sc_enabled):
            self.stop("DLC pro扫描已关闭，观察/自动锁频终止")
            return
        if int(snapshot.sc_signal_type) != 1:
            self.stop("扫描波形已不是三角波，观察/自动锁频终止")
            return
        if abs(frequency - self.scan_frequency) / max(self.scan_frequency, 1e-12) > 0.02:
            self.scan_frequency = frequency
            self.gate_bin = self._latest_bin()
            self._wait_for_new_window(4.0, keep_gate=True)
            self._log(f"扫描频率变化为{frequency:g} Hz，重新建立峰周期")
            return
        if self.observe_only:
            offset = float(snapshot.sc_offset)
            amplitude = abs(float(snapshot.sc_amplitude))
            offset_changed = abs(offset - self.engine.current_offset) > 1e-12
            amplitude_changed = abs(amplitude - self.engine.current_amplitude) > 1e-12
            if offset_changed or amplitude_changed:
                changes = []
                if offset_changed:
                    changes.append(
                        f"Offset {self.engine.current_offset:.6f} → {offset:.6f}"
                    )
                if amplitude_changed:
                    changes.append(
                        f"Amplitude {self.engine.current_amplitude:.6f} → {amplitude:.6f}"
                    )
                self.engine.sync(offset, amplitude)
                self.scan_unit = str(
                    getattr(snapshot, "sc_unit", self.scan_unit) or ""
                ).strip()
                self._apply_amplitude_step_profile(
                    self.engine, self.scan_unit
                )
                self.gate_bin = self._latest_bin()
                self._wait_for_new_window(4.0, keep_gate=True)
                self.manual_advice = (
                    "已检测到人工调节：" + "；".join(changes)
                    + "。正在等待4个全新扫描周期，期间不要继续改参数。"
                )
                self._log(self.manual_advice)
                self._emit_status(PeakObservation(
                    False, "等待人工调节后的独立新窗口"
                ))
                return
        if time.monotonic() < self.available_after:
            return
        cycles = self.required_cycles
        seconds = min(self.ring.HISTORY_SECONDS, cycles / frequency + 0.25)
        history = self.ring.raw_history(seconds)
        observation = analyze_carrier(
            history, self.engine.settings, frequency,
            self.engine.fingerprint, self.gate_bin,
        )
        self.last_observation = observation
        self._emit_status(observation)
        if observation.reason in {
            "等待足够的扫描周期", "分析窗口存在ADC索引空洞"
        }:
            if observation.reason.endswith("索引空洞"):
                self.gate_bin = self._latest_bin()
                self._wait_for_new_window(cycles, keep_gate=True)
                retry_seconds = cycles / max(frequency, 1e-12)
                self._log(
                    "丢弃包含ADC/网络空洞的分析窗口；"
                    f"等待{cycles:g}个全新周期后重试（约{retry_seconds:.1f}秒）"
                )
            if self.observe_only and observation.reason.endswith("索引空洞"):
                action = self._observe(observation)
                self._emit_status(observation, action)
            elif self.observe_only:
                self.manual_advice = (
                    "正在等待一批完整且未分析过的新数据；请保持扫频参数不动。"
                )
                self._emit_status(observation)
            return
        if self.observe_only:
            action = self._observe(observation)
        else:
            action = self.engine.update(observation)
        self._emit_status(observation, action)
        if action.kind == "stop":
            self.stop(action.reason)
        elif action.kind in {"offset", "amplitude"} and action.value is not None:
            self._submit_action(action)
        else:
            # Consume this window. Stable confirmations and tracking checks
            # must never count the same ADC bins more than once.
            self.gate_bin = int(history.bin_indices[-1])
            self._wait_for_new_window(4.0, keep_gate=True)

    def _observe(self, observation: PeakObservation) -> ControlAction:
        """Give bounded manual instructions without issuing any device write."""
        engine = self.engine
        if engine is None:
            self.manual_advice = observation.reason
            return ControlAction("none", None, observation.reason, "observe")
        settings = engine.settings
        if not observation.valid:
            engine.stable_count = 0
            if engine.current_amplitude < engine.last_good_amplitude * 0.999:
                self.manual_advice = (
                    f"当前峰识别失败（{observation.reason}）。请先把 Scan Amplitude "
                    f"恢复到最近可靠值 {engine.last_good_amplitude:.6f}，然后等待4个周期。"
                )
            else:
                self.manual_advice = (
                    f"当前峰识别失败（{observation.reason}）。先保持 Offset 不动；"
                    "确认透射峰通道、三角扫描和峰极性。若画面确实扫不到00模，"
                    "请适当增大 Scan Amplitude 后等待4个周期。"
                )
            return ControlAction("none", None, self.manual_advice, "observe")

        if engine.fingerprint is None:
            engine.fingerprint = CarrierFingerprint(
                observation.prominence,
                observation.width_seconds,
                observation.polarity,
            )
        else:
            engine.fingerprint.update(observation)
        engine.last_good_amplitude = engine.current_amplitude

        if observation.balance_error <= settings.balance_tolerance:
            engine.stable_count += 1
            engine.previous_error = observation.balance_error
            engine.previous_offset = engine.current_offset
            if engine.stable_count >= settings.stable_windows:
                minimum = engine.start_amplitude * settings.min_amplitude_fraction
                target = max(
                    minimum, engine.current_amplitude * settings.shrink_ratio
                )
                self.manual_advice = (
                    f"已连续{settings.stable_windows}个独立窗口居中。"
                    f"如果要继续缩小扫频范围，请手动把 Scan Amplitude 调到 "
                    f"{target:.6f}；如果只验证居中，保持当前值即可。调节后等待4个周期。"
                )
            else:
                self.manual_advice = (
                    f"峰间隔已合格，正在用独立窗口复核 "
                    f"{engine.stable_count}/{settings.stable_windows}。"
                    "现在不要调节，等待下一批4个周期。"
                )
            return ControlAction("none", None, self.manual_advice, "observe")

        engine.stable_count = 0
        previous_error = engine.previous_error
        previous_offset = engine.previous_offset
        offset_delta = engine.current_offset - previous_offset
        minimum_step = engine.base_step_size / 8.0
        if previous_error is None or abs(offset_delta) < 1e-12:
            direction = engine.direction
            step = engine.step_size
            explanation = "单个窗口不能知道DLC pro正负方向，先做一次正向试探"
        else:
            changed_direction = 1.0 if offset_delta > 0 else -1.0
            if observation.balance_error < previous_error:
                direction = changed_direction
                step = engine.step_size
                explanation = "刚才的人工调节使不均匀度变小，继续同方向"
            else:
                direction = -changed_direction
                step = max(minimum_step, engine.step_size / 2.0)
                explanation = "刚才的人工调节使不均匀度变大，反向并减小步长"
            engine.direction = direction
            engine.step_size = step
        low, high = engine.offset_limits
        target = min(
            high,
            max(low, engine.current_offset + direction * step),
        )
        engine.previous_error = observation.balance_error
        engine.previous_offset = engine.current_offset
        self.manual_advice = (
            f"当前不均匀度 {observation.balance_error * 100:.2f}%。{explanation}："
            f"请把 Scan Offset 从 {engine.current_offset:.6f} 手动调到 "
            f"{target:.6f}（步长 {step:.6f}），然后保持不动等待4个周期。"
        )
        return ControlAction("none", None, self.manual_advice, "observe")

    def _wait_for_new_window(self, cycles: float, *,
                             keep_gate: bool = False) -> None:
        self.required_cycles = float(cycles)
        if not keep_gate:
            self.gate_bin = self._latest_bin()
        self.available_after = (
            time.monotonic() + self.required_cycles / self.scan_frequency
        )

    @staticmethod
    def _operator_step_for_amplitude(
        amplitude: float, unit: str, fallback: float
    ) -> tuple[float, str]:
        """Apply the operator's verified voltage-scan tuning gears only to V."""
        normalized_unit = str(unit or "").strip().lower().replace(" ", "")
        if normalized_unit not in {"v", "vpp", "volt", "volts"}:
            return float(fallback), "用户设定"
        amplitude = abs(float(amplitude))
        if amplitude <= 0.5 + 1e-12:
            return 0.001, "细调（Amplitude≤0.5 Vpp）"
        if amplitude <= 1.0 + 1e-12:
            return 0.01, "中调（Amplitude≤1 Vpp）"
        return 0.1, "粗调（Amplitude>1 Vpp）"

    def _apply_amplitude_step_profile(
        self, engine: PeakBalanceEngine, unit: str
    ) -> None:
        step, profile = self._operator_step_for_amplitude(
            engine.current_amplitude, unit, engine.settings.offset_step
        )
        changed = engine.set_offset_step(step)
        self.step_profile = profile
        if changed:
            self._log(
                f"按当前Amplitude切换Offset步进：{profile}，步长={step:.6f}"
            )

    def _submit_action(self, action: ControlAction) -> None:
        if self.observe_only:
            self._log(
                f"仅观察，未执行建议：{action.kind} -> {action.value}"
            )
            self._wait_for_new_window(4.0)
            return
        self.pending_write = True
        self.pending_kind = action.kind
        self.gate_bin = self._latest_bin()
        cycles = 3.0 if action.kind == "amplitude" else 2.0
        self._wait_for_new_window(cycles, keep_gate=True)
        self._log(f"{action.reason}：{action.kind} -> {action.value:.6f}")
        if action.kind == "offset":
            self.session.set_scan_offset(float(action.value))
        else:
            self.session.set_scan_amplitude(float(action.value))

    def _write_completed(self, snapshot) -> None:
        if self.engine is not None:
            self.engine.sync(float(snapshot.sc_offset), float(snapshot.sc_amplitude))
            self.scan_unit = str(
                getattr(snapshot, "sc_unit", self.scan_unit) or ""
            ).strip()
            self._apply_amplitude_step_profile(self.engine, self.scan_unit)
        was_restore = self.pending_kind.startswith("restore_")
        self.pending_write = False
        self.pending_kind = ""
        if was_restore:
            self._run_restore_queue()
        elif self.running:
            self.gate_bin = self._latest_bin()

    def _connection_changed(self, connected: bool, text: str) -> None:
        if self.running and not connected:
            self.stop(f"DLC pro{text}，自动锁频终止")

    def _session_error(self, message: str) -> None:
        if self.pending_write:
            self.pending_write = False
            self.restore_queue.clear()
        if self.running:
            self.stop(f"DLC pro写入失败：{message}")

    def _emit_status(self, observation: PeakObservation,
                     action: ControlAction | None = None) -> None:
        engine = self.engine
        self.status_changed.emit({
            "running": self.running,
            "state": action.state if action is not None else (
                engine.state if engine is not None else "idle"
            ),
            "message": action.reason if action is not None else observation.reason,
            "observation": observation,
            "offset": engine.current_offset if engine is not None else 0.0,
            "start_offset": self.start_offset,
            "amplitude": engine.current_amplitude if engine is not None else 0.0,
            "start_amplitude": self.start_amplitude,
            "last_good_amplitude": (
                engine.last_good_amplitude if engine is not None else 0.0
            ),
            "scan_frequency": self.scan_frequency,
            "scan_unit": self.scan_unit,
            "offset_step": (
                engine.step_size if engine is not None else 0.0
            ),
            "step_profile": self.step_profile,
            "manual_advice": self.manual_advice,
        })

    def _log(self, text: str) -> None:
        self.log_message.emit(f"{time.strftime('%H:%M:%S')}  {text}")
