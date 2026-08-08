"""Qt coordinator for raw-ADC peak balancing and DLC pro scan writes."""
from __future__ import annotations

import csv
import json
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from .adc_peak_balance_algorithm import (
    CarrierFingerprint, ControlAction,
    PeakBalanceEngine,
    PeakBalanceSettings,
    PeakObservation,
    analyze_carrier,
)


class _AutoLockCsvSession:
    """One flushed CSV per run; only the four public event types are stored."""

    FIELDS = (
        "event", "timestamp", "elapsed_s", "sequence", "mode", "state",
        "valid", "reason_code", "reason", "frequency_hz", "amplitude_vpp",
        "offset_v", "scan_low_v", "scan_high_v", "peak_count", "family_count",
        "main_prominence", "second_prominence", "family_ratio", "snr",
        "peak_width_s", "expected_period_s", "measured_period_s", "period_error",
        "delta_t1_s", "delta_t2_s", "signed_error", "balance_error",
        "balance_tolerance", "reference_value", "step_v", "direction",
        "theoretical_distance_v", "action", "target_value", "write_kind",
        "requested_value", "readback_value", "write_tolerance", "write_ok",
        "result", "settings_json", "device_start_json", "details_json",
    )

    def __init__(self, directory: Path, *, mode: str, settings: dict,
                 device_start: dict):
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.started = time.monotonic()
        self.sequence = 0
        self.mode = mode
        self._partial = directory / f"{stamp}_running.partial.csv"
        self.path = self._partial
        self._handle = self._partial.open("w", newline="", encoding="utf-8-sig")
        self._writer = csv.DictWriter(self._handle, fieldnames=self.FIELDS)
        self._writer.writeheader()
        self.write("START", settings_json=json.dumps(settings, ensure_ascii=False),
                   device_start_json=json.dumps(device_start, ensure_ascii=False))

    def write(self, event: str, **values) -> None:
        if self._handle.closed:
            return
        self.sequence += 1
        row = {field: "" for field in self.FIELDS}
        row.update(values)
        row.update({
            "event": event,
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "elapsed_s": f"{time.monotonic() - self.started:.6f}",
            "sequence": self.sequence,
            "mode": self.mode,
        })
        self._writer.writerow(row)
        self._handle.flush()

    def finish(self, result: str, reason: str) -> Path:
        if self._handle.closed:
            return self.path
        self.write("END", result=result, reason=reason)
        self._handle.close()
        safe = result.lower().replace(" ", "_") or "ended"
        final = self._partial.with_name(
            self._partial.name.replace("_running.partial.csv", f"_{safe}.csv")
        )
        self._partial.replace(final)
        self.path = final
        return final


class AdcPeakBalanceController(QObject):
    ANALYSIS_CYCLES = 2.0
    SETTLE_CYCLES = 1.0
    # DLC pro scan-frequency readback is quantized and need not equal the
    # requested IEEE-754 value bit-for-bit.  Accept 1 mHz (or 10 ppm at high
    # frequencies); analysis always uses the actual device readback.
    FREQUENCY_READBACK_TOLERANCE_HZ = 0.001
    LOG_DIRECTORY = Path(__file__).resolve().parent / "captures" / "auto_lock_logs"
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
        self.pending_value: float | None = None
        self.pending_wait_cycles = 0.0
        self.settle_until = 0.0
        self.settle_pending = False
        self.settle_kind = ""
        self._pending_start: tuple[PeakBalanceSettings, bool, bool] | None = None
        self.auto_engage_falc = False
        self.falc_engaged = False
        self.gate_bin: int | None = None
        self.available_after = 0.0
        self.required_cycles = self.ANALYSIS_CYCLES
        self.scan_frequency = 0.0
        self.observe_only = True
        self.start_offset: float | None = None
        self.start_amplitude: float | None = None
        self.start_frequency: float | None = None
        self.restore_offset: float | None = None
        self.restore_amplitude: float | None = None
        self.scan_unit = ""
        self.step_profile = "用户设定"
        self.last_observation = PeakObservation(False, "尚未开始")
        self.restore_queue: list[tuple[str, float]] = []
        self.log_session: _AutoLockCsvSession | None = None
        self.last_log_path: Path | None = None
        self._last_action = ControlAction("none", None, "", "idle")
        self.manual_advice = "尚未开始观察"
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._tick)
        self.session.write_snapshot_changed.connect(self._write_completed)
        falc_signal = getattr(self.session, "falc_engaged", None)
        if falc_signal is not None:
            falc_signal.connect(self._falc_completed)
        self.session.connection_changed.connect(self._connection_changed)
        self.session.error.connect(self._session_error)

    def start(self, settings: PeakBalanceSettings, *,
              observe_only: bool = False,
              auto_engage_falc: bool = False) -> None:
        if self.running:
            return
        if not self.acquisition_running():
            raise RuntimeError("请先连接PL板卡并启动ADC采集")
        if not self.session.is_connected:
            raise RuntimeError("请先连接DLC pro")
        snapshot = self.session.snapshot()
        if snapshot is None:
            raise RuntimeError("尚未取得DLC pro扫描参数")
        settings = settings.validated()
        frequency = float(snapshot.sc_frequency)
        if frequency <= 0:
            raise RuntimeError("DLC pro扫描频率必须大于0")
        analysis_frequency = (
            frequency if observe_only else settings.search_frequency_hz
        )
        if self.ANALYSIS_CYCLES / analysis_frequency > self.ring.HISTORY_SECONDS:
            raise RuntimeError("当前扫描频率过低，原始码历史不足以覆盖2个完整周期")
        # The project's verified Scan configuration uses signal type 1 for the
        # triangle waveform required by the alternating-interval algorithm.
        if int(snapshot.sc_signal_type) != 1:
            raise RuntimeError("当前算法只允许已确认的三角扫描波形")
        scan_output = int(getattr(snapshot, "sc_output_channel", -1))
        scan_unit = str(getattr(snapshot, "sc_unit", "") or "").strip()
        if scan_output != 50:
            raise RuntimeError(
                "自动找峰只允许Scan Output=PC Voltage（PZT压电电压，通道50）；"
                "当前不是PC Voltage。请先在DLC pro扫频控制中改为PC Voltage，"
                "软件不会自动切换输出通道。"
            )
        if scan_unit.lower() not in {"v", "volt", "volts"}:
            raise RuntimeError(
                f"PC Voltage扫描单位应为V，当前设备读回单位为“{scan_unit or '未知'}”"
            )
        falc = getattr(snapshot, "falc1", None)
        if not observe_only and falc is not None:
            path = int(falc.path_selection)
            if ((path & 1 and bool(falc.unlim.enabled))
                    or (path & 2 and bool(falc.main.enabled))):
                raise RuntimeError(
                    "FALC pro当前仍有选中路径处于使能状态；请先解除FALC锁定，"
                    "软件不会为了开启Scan而自动关闭已有闭环。"
                )
        if auto_engage_falc and not observe_only:
            if falc is None:
                raise RuntimeError("未读取到FALC pro模块，不能启用自动FALC接管")
            path = int(falc.path_selection)
            if path not in (1, 2, 3):
                raise RuntimeError(
                    "FALC pro的Path Selection为None；请先打开FALC pro设置选择路径"
                )
        if (observe_only
                and settings.final_amplitude
                > abs(float(snapshot.sc_amplitude)) + 1e-12):
            raise RuntimeError(
                "最终扫频范围目标不能大于当前启动Scan Amplitude"
            )
        self._begin_log_session(settings, snapshot, observe_only)
        self._pending_start = (settings, bool(observe_only), bool(auto_engage_falc))
        self.start_frequency = frequency
        self.restore_offset = float(snapshot.sc_offset)
        self.restore_amplitude = abs(float(snapshot.sc_amplitude))
        if (not observe_only
                and not self._frequency_matches(
                    frequency, settings.search_frequency_hz
                )):
            self.running = True
            self.pending_write = True
            self.pending_kind = "frequency_start"
            self.pending_value = settings.search_frequency_hz
            self.running_changed.emit(True)
            self.manual_advice = (
                f"正在把快速寻峰频率从{frequency:g} Hz切换到"
                f"{settings.search_frequency_hz:g} Hz并等待设备读回"
            )
            self._log(self.manual_advice)
            self.session.set_scan_frequency(settings.search_frequency_hz)
            return
        self._continue_start(snapshot)

    @classmethod
    def _frequency_matches(cls, actual: float, expected: float) -> bool:
        tolerance = max(
            cls.FREQUENCY_READBACK_TOLERANCE_HZ,
            abs(float(expected)) * 1e-5,
        )
        return abs(float(actual) - float(expected)) <= tolerance

    def _continue_start(self, snapshot) -> None:
        if self._pending_start is None:
            return
        settings, observe_only, _auto_engage_falc = self._pending_start
        if (not observe_only
                and abs(abs(float(snapshot.sc_amplitude))
                        - settings.initial_search_amplitude) > 5e-7):
            self.running = True
            self.pending_write = True
            self.pending_kind = "amplitude_start"
            self.pending_value = settings.initial_search_amplitude
            self.running_changed.emit(True)
            self.manual_advice = (
                f"正在把初始化Scan Amplitude从"
                f"{abs(float(snapshot.sc_amplitude)):.6f} Vpp切换到"
                f"{settings.initial_search_amplitude:.6f} Vpp并等待设备读回"
            )
            self._log(self.manual_advice)
            self.session.set_scan_amplitude(settings.initial_search_amplitude)
            return
        if not bool(snapshot.sc_enabled):
            if observe_only:
                raise RuntimeError("观察模式禁止写入DLC pro；请先手动启用Scan")
            self.running = True
            self.pending_write = True
            self.pending_kind = "scan_enable"
            self.pending_value = 1.0
            self.running_changed.emit(True)
            self.manual_advice = "Scan当前关闭，正在自动开启并等待设备读回"
            self._log(self.manual_advice)
            self.session.set_scan_enabled(True)
            return
        self._begin_analysis(snapshot)

    def _begin_analysis(self, snapshot) -> None:
        if self._pending_start is None:
            raise RuntimeError("自动找峰启动参数已丢失")
        settings, observe_only, auto_engage_falc = self._pending_start
        self._pending_start = None
        frequency = float(snapshot.sc_frequency)
        scan_unit = str(getattr(snapshot, "sc_unit", "") or "").strip()
        engine = PeakBalanceEngine(settings)
        engine.start(float(snapshot.sc_offset), float(snapshot.sc_amplitude))
        self.scan_unit = scan_unit
        self._apply_amplitude_step_profile(engine, self.scan_unit)
        self.settings = settings
        self.engine = engine
        self.scan_frequency = frequency
        self.observe_only = observe_only
        self.auto_engage_falc = bool(auto_engage_falc and not observe_only)
        self.falc_engaged = False
        self.start_offset = float(snapshot.sc_offset)
        self.start_amplitude = abs(float(snapshot.sc_amplitude))
        self.pending_write = False
        self.pending_value = None
        self.pending_wait_cycles = 0.0
        self.settle_pending = False
        self.settle_until = 0.0
        self.settle_kind = ""
        self.restore_queue.clear()
        self.manual_advice = "正在采集2个完整扫描周期，请暂时不要调节"
        self.gate_bin = self._latest_bin()
        self._wait_for_new_window(self.ANALYSIS_CYCLES, keep_gate=True)
        was_running = self.running
        self.running = True
        if not was_running:
            self.running_changed.emit(True)
        self._log(
            f"启动{'观察模式（禁止写入）' if self.observe_only else '自动控制模式'}："
            f"Offset={self.start_offset:.6f}，"
            f"Amplitude={self.start_amplitude:.6f}，频率={frequency:g} Hz"
        )
        self.timer.start()
        self._emit_status(PeakObservation(False, "采集2个扫描周期建立00模基准"))

    def stop(self, reason: str = "用户停止", result: str | None = None) -> None:
        if not self.running and self.log_session is None:
            return
        self.running = False
        self.timer.stop()
        self.pending_write = False
        self.pending_value = None
        self.pending_wait_cycles = 0.0
        self.settle_pending = False
        self.settle_until = 0.0
        self.settle_kind = ""
        self._pending_start = None
        self.running_changed.emit(False)
        if result is None:
            if self.falc_engaged:
                result = "falc_complete"
            elif self.engine is not None and self.engine.finalized:
                result = "locked"
            elif "用户" in reason or "手动" in reason:
                result = "stopped"
            else:
                result = "fault"
        self._finish_log_session(result, reason)
        self.stopped.emit(reason)

    def restore_start_values(self) -> None:
        if self.restore_offset is None or self.restore_amplitude is None:
            raise RuntimeError("本次尚未保存启动Offset/Amplitude")
        self.stop("停止自动控制并恢复启动参数")
        self.restore_queue = [
            ("offset", float(self.restore_offset)),
            ("amplitude", float(self.restore_amplitude)),
        ]
        if self.start_frequency is not None:
            self.restore_queue.append(("frequency", float(self.start_frequency)))
        self._run_restore_queue()

    def _run_restore_queue(self) -> None:
        if self.pending_write or not self.restore_queue:
            return
        kind, value = self.restore_queue.pop(0)
        self.pending_write = True
        self.pending_kind = f"restore_{kind}"
        self.pending_value = value
        self.pending_wait_cycles = 0.0
        if kind == "offset":
            self.session.set_scan_offset(value)
        elif kind == "amplitude":
            self.session.set_scan_amplitude(value)
        else:
            self.session.set_scan_frequency(value)

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
        if self.settle_pending:
            if time.monotonic() < self.settle_until:
                return
            settled_kind = self.settle_kind
            self.settle_pending = False
            self.settle_kind = ""
            self.gate_bin = self._latest_bin()
            self._wait_for_new_window(self.ANALYSIS_CYCLES, keep_gate=True)
            self._log(
                f"{settled_kind}写入后的稳定期结束；从当前ADC bin开始采集2个全新周期"
            )
            return
        if abs(frequency - self.scan_frequency) / max(self.scan_frequency, 1e-12) > 0.02:
            self.scan_frequency = frequency
            self.engine.reset_after_frequency_change()
            self.gate_bin = self._latest_bin()
            self._wait_for_new_window(self.ANALYSIS_CYCLES, keep_gate=True)
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
                # A manual parameter change starts a new control experiment.
                # Never carry a confirmation count or direction comparison
                # across different Offset/Amplitude values.
                self.engine.stable_count = 0
                self.engine.previous_error = None
                self.engine.previous_offset = offset
                if amplitude_changed:
                    self.engine.finalized = False
                self.scan_unit = str(
                    getattr(snapshot, "sc_unit", self.scan_unit) or ""
                ).strip()
                self._apply_amplitude_step_profile(
                    self.engine, self.scan_unit
                )
                self.gate_bin = self._latest_bin()
                self._wait_for_new_window(self.ANALYSIS_CYCLES, keep_gate=True)
                self.manual_advice = (
                    "已检测到人工调节：" + "；".join(changes)
                    + "。正在等待2个全新扫描周期，期间不要继续改参数。"
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
        if observation.reason_code == "WAITING":
            if self.observe_only:
                self.manual_advice = "正在等待一批完整且未分析过的新数据；请保持扫频参数不动。"
                self._emit_status(observation)
            return
        if self.observe_only:
            action = self._observe(observation)
            self._log_decision(observation, action)
        else:
            action = self.engine.update(observation)
            if (not self.auto_engage_falc and observation.valid
                    and self.engine.current_amplitude
                    <= self.engine.amplitude_floor * 1.001
                    and observation.balance_error
                    <= self.engine.settings.final_balance_tolerance):
                self.engine.finalized = True
                action = ControlAction(
                    "none", None,
                    "最终窗口首次达标；未启用自动FALC，立即停止写入",
                    "track", "FINAL_PASS",
                )
            self._log_decision(observation, action)
        self._emit_status(observation, action)
        if action.kind == "stop":
            self.stop(action.reason)
        elif action.kind in {"offset", "amplitude"} and action.value is not None:
            self._submit_action(action)
        elif (self.engine.finalized and action.state == "track"
              and observation.valid
              and observation.balance_error
              <= self.engine.settings.final_balance_tolerance):
            if self.auto_engage_falc:
                self._engage_falc()
            else:
                self.manual_advice = (
                    "最终验收通过；未勾选自动使能FALC pro。"
                    "已停止自动调节并保持当前Scan、Offset和Amplitude。"
                )
                self.stop(self.manual_advice)
        else:
            # Consume this window. Stable confirmations and tracking checks
            # must never count the same ADC bins more than once.
            self.gate_bin = int(history.bin_indices[-1])
            self._wait_for_new_window(self.ANALYSIS_CYCLES, keep_gate=True)

    def _observe(self, observation: PeakObservation) -> ControlAction:
        """Give bounded manual instructions without issuing any device write."""
        engine = self.engine
        if engine is None:
            self.manual_advice = observation.reason
            return ControlAction("none", None, observation.reason, "observe")
        settings = engine.settings
        if not observation.valid:
            engine.stable_count = 0
            if observation.reason_code == "NO_PEAK":
                step = settings.initial_offset_search_step
                center = engine.start_offset
                if engine.current_amplitude <= engine.amplitude_floor * 1.001:
                    step = settings.final_coarse_step
                    center = engine.final_origin_offset or engine.current_offset
                self.manual_advice = (
                    "当前没有检测到透射峰。保持 Scan Amplitude="
                    f"{engine.current_amplitude:.6f} Vpp 不变，以搜索中心Offset="
                    f"{center:.6f}为中心，连续两窗确认无峰后按 +{step:.6f}、"
                    f"-{step:.6f}、+{2 * step:.6f}、-{2 * step:.6f}…"
                    "左右逐步扩大Offset；每次调节后等待2个新周期。"
                    "实际范围受PC Voltage物理边界限制。"
                )
            else:
                self.manual_advice = (
                    f"当前峰识别失败（{observation.reason}）。先保持 Offset 不动；"
                    f"原地重新采集，最多复测{settings.invalid_retry_windows}次。"
                    "确认透射峰通道、三角扫描、峰极性和ADC数据完整性。"
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

        stage = engine.current_stage
        if observation.balance_error <= stage.balance_tolerance:
            engine.stable_count += 1
            engine.previous_error = observation.balance_error
            engine.previous_offset = engine.current_offset
            if engine.stable_count >= stage.stable_windows:
                if stage.next_amplitude is None:
                    self.manual_advice = (
                        f"已连续{stage.stable_windows}个独立窗口达到最终验收标准："
                        f"Amplitude={engine.current_amplitude:.6f} Vpp，"
                        f"不均匀度≤{stage.balance_tolerance * 100:.2f}%。"
                        "观察模式不会关闭Scan或使能FALC pro；保持当前参数即可验证稳定性。"
                    )
                    return ControlAction("none", None, self.manual_advice, "observe")
                target = stage.next_amplitude
                if target >= engine.current_amplitude * 0.999:
                    self.manual_advice = (
                        f"已连续{stage.stable_windows}个独立窗口居中，且Scan "
                        f"Amplitude已达到最终目标 {engine.amplitude_floor:.6f} Vpp。"
                        "观察模式不会使能FALC pro；可保持当前参数验证稳定性。"
                    )
                else:
                    self.manual_advice = (
                        f"{stage.name}已连续{stage.stable_windows}个独立窗口通过"
                        f"（门槛≤{stage.balance_tolerance * 100:.2f}%）。"
                        "下一步进入缩幅：请把 Scan Amplitude 从 "
                        f"{engine.current_amplitude:.6f} Vpp 调到 {target:.6f} Vpp，"
                        "然后保持不动等待2个周期；该版本会一步进入最终幅度，"
                        "不再经过中扫、细扫和窄扫。"
                    )
            else:
                self.manual_advice = (
                    f"{stage.name}峰间隔已合格（门槛≤"
                    f"{stage.balance_tolerance * 100:.2f}%），正在用独立窗口复核 "
                    f"{engine.stable_count}/{stage.stable_windows}。"
                    "现在不要调节，等待下一批2个周期。"
                )
            return ControlAction("none", None, self.manual_advice, "observe")

        engine.stable_count = 0
        previous_error = engine.previous_error
        previous_offset = engine.previous_offset
        offset_delta = engine.current_offset - previous_offset
        final_stage = engine.current_amplitude <= engine.amplitude_floor * 1.001
        target_override = None
        if previous_error is None or abs(offset_delta) < 1e-12:
            direction = engine.direction
            step = (
                engine._final_step_for(observation)
                if final_stage else settings.wide_probe_step
            )
            explanation = (
                "最终阶段先按误差选择粗调或精调步长做正向试探"
                if final_stage else "宽扫先做一次正向方向试探"
            )
        else:
            changed_direction = 1.0 if offset_delta > 0 else -1.0
            if observation.balance_error < previous_error:
                direction = changed_direction
                step = engine.step_size
                explanation = "刚才的人工调节使不均匀度变小，继续同方向"
            else:
                direction = -changed_direction
                step = (
                    settings.final_fine_step if final_stage
                    else settings.wide_probe_step
                )
                explanation = (
                    "刚才的最终调节变差，恢复最佳附近并反向精调"
                    if final_stage else "宽扫正向试探变差，改用反方向"
                )
            if not final_stage:
                step = engine.theoretical_distance(
                    engine.current_amplitude, previous_error
                )
                target_override = previous_offset + direction * step
                explanation += "，从试探前Offset跳完整理论距离"
            engine.direction = direction
            engine.step_size = step
        low, high = engine.offset_limits
        if engine.current_offset < low - 1e-12 or engine.current_offset > high + 1e-12:
            self.manual_advice = (
                f"当前Scan Offset {engine.current_offset:.6f} 已超出允许范围 "
                f"[{low:.6f}, {high:.6f}]。请恢复到范围内；最终阶段范围由"
                "‘最终最大Offset偏移’和PC Voltage物理边界共同限制。"
            )
            return ControlAction("none", None, self.manual_advice, "observe")
        target = min(
            high,
            max(low, target_override if target_override is not None else (
                engine.current_offset + direction * step
            )),
        )
        if abs(target - engine.current_offset) < 1e-12:
            self.manual_advice = (
                f"Offset已到允许边界 {target:.6f}，但不均匀度仍为"
                f"{observation.balance_error * 100:.2f}%。请停止并检查搜索中心；"
                "若处于最终阶段，可在确认安全后调整‘最终最大Offset偏移’。"
            )
            return ControlAction("none", None, self.manual_advice, "observe")
        engine.previous_error = observation.balance_error
        engine.previous_offset = engine.current_offset
        self.manual_advice = (
            f"当前不均匀度 {observation.balance_error * 100:.2f}%。{explanation}："
            f"请把 Scan Offset 从 {engine.current_offset:.6f} 手动调到 "
            f"{target:.6f}（步长 {step:.6f}），然后保持不动等待2个周期。"
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

    def _apply_amplitude_step_profile(
        self, engine: PeakBalanceEngine, unit: str
    ) -> None:
        stage = engine.current_stage
        step = stage.offset_step
        profile = (
            f"{stage.name}（允许不均匀度≤{stage.balance_tolerance * 100:.2f}%，"
            f"连续{stage.stable_windows}个独立窗口）"
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
            self._wait_for_new_window(self.ANALYSIS_CYCLES)
            return
        self.pending_write = True
        self.pending_kind = action.kind
        self.pending_value = float(action.value)
        self.gate_bin = self._latest_bin()
        cycles = self.SETTLE_CYCLES
        self.pending_wait_cycles = cycles
        if action.kind == "offset":
            self.session.set_scan_offset(float(action.value))
        else:
            self.session.set_scan_amplitude(float(action.value))

    def _write_completed(self, snapshot) -> None:
        # Shared-session manual writes (especially in observe-only mode) must
            # be detected by _tick as operator changes and receive a fresh 2-cycle
        # window.  Only consume completions initiated by this controller.
        if self.pending_write and self.pending_kind == "frequency_start":
            expected = float(self.pending_value or 0.0)
            actual = float(snapshot.sc_frequency)
            tolerance = max(
                self.FREQUENCY_READBACK_TOLERANCE_HZ, abs(expected) * 1e-5
            )
            if not self._frequency_matches(actual, expected):
                self._log_write("frequency_start", expected, actual, tolerance, False, snapshot)
                self.pending_write = False
                self.pending_kind = ""
                self.pending_value = None
                self.stop(
                    f"快速扫频频率写入读回不一致：期望{expected:g} Hz，"
                    f"实际{actual:g} Hz"
                )
                return
            self._log_write("frequency_start", expected, actual, tolerance, True, snapshot)
            self.pending_write = False
            self.pending_kind = ""
            self.pending_value = None
            self._log(f"快速扫频频率已切换并读回为{actual:g} Hz")
            self._continue_start(snapshot)
            return
        if self.pending_write and self.pending_kind == "amplitude_start":
            expected = float(self.pending_value or 0.0)
            actual = abs(float(snapshot.sc_amplitude))
            tolerance = max(5e-7, abs(expected) * 1e-9)
            if abs(actual - expected) > tolerance:
                self._log_write("amplitude_start", expected, actual, tolerance, False, snapshot)
                self.pending_write = False
                self.pending_kind = ""
                self.pending_value = None
                self.stop(
                    f"初始化Scan Amplitude写入读回不一致："
                    f"期望{expected:.9g} Vpp，实际{actual:.9g} Vpp"
                )
                return
            self._log_write("amplitude_start", expected, actual, tolerance, True, snapshot)
            self.pending_write = False
            self.pending_kind = ""
            self.pending_value = None
            self._log(
                f"初始化Scan Amplitude已切换并读回为{actual:.6f} Vpp"
            )
            self._continue_start(snapshot)
            return
        if self.pending_write and self.pending_kind == "scan_enable":
            if not bool(snapshot.sc_enabled):
                self._log_write("scan_enable", 1.0, 0.0, 0.0, False, snapshot)
                self.pending_write = False
                self.pending_kind = ""
                self.stop("自动开启Scan后设备读回仍为关闭，自动锁频未启动")
                return
            self._log_write("scan_enable", 1.0, 1.0, 0.0, True, snapshot)
            self.pending_write = False
            self.pending_kind = ""
            self.pending_value = None
            self._log("Scan已自动开启并通过读回校验；开始采集2个全新周期")
            self._begin_analysis(snapshot)
            return
        if (not self.pending_write
                or self.pending_kind not in {
                    "offset", "amplitude", "restore_offset", "restore_amplitude",
                    "restore_frequency",
                }):
            return
        pending_kind = self.pending_kind
        pending_value = self.pending_value
        if pending_value is not None:
            if pending_kind.endswith("offset"):
                field = "sc_offset"
            elif pending_kind.endswith("amplitude"):
                field = "sc_amplitude"
            else:
                field = "sc_frequency"
            actual = float(getattr(snapshot, field))
            # DLC pro readback can be quantized below the six decimals shown in
            # the UI.  Half a display LSB is accepted; larger disagreement is
            # still treated as a failed device write.
            tolerance = max(5e-7, abs(pending_value) * 1e-9)
            if abs(actual - pending_value) > tolerance:
                self._log_write(pending_kind, pending_value, actual, tolerance, False, snapshot)
                self.pending_write = False
                self.pending_kind = ""
                self.pending_value = None
                self.pending_wait_cycles = 0.0
                self.stop(
                    f"DLC pro写入读回不一致：{field}期望{pending_value:.9g}，"
                    f"实际{actual:.9g}"
                )
                return
            self._log_write(pending_kind, pending_value, actual, tolerance, True, snapshot)
        if self.engine is not None:
            self.engine.sync(float(snapshot.sc_offset), float(snapshot.sc_amplitude))
            if pending_kind.endswith("amplitude"):
                self.engine.reset_after_amplitude_change()
            self.scan_unit = str(
                getattr(snapshot, "sc_unit", self.scan_unit) or ""
            ).strip()
            self._apply_amplitude_step_profile(self.engine, self.scan_unit)
        was_restore = self.pending_kind.startswith("restore_")
        wait_cycles = self.pending_wait_cycles
        if pending_kind.endswith("amplitude"):
            completed_kind = "Amplitude"
        elif pending_kind.endswith("frequency"):
            completed_kind = "Frequency"
        else:
            completed_kind = "Offset"
        self.pending_write = False
        self.pending_kind = ""
        self.pending_value = None
        self.pending_wait_cycles = 0.0
        if was_restore:
            self._run_restore_queue()
        elif self.running:
            self.gate_bin = self._latest_bin()
            self.settle_pending = True
            self.settle_kind = completed_kind
            self.settle_until = (
                time.monotonic()
                + (wait_cycles or self.SETTLE_CYCLES) / max(self.scan_frequency, 1e-12)
            )
            self.available_after = self.settle_until
            self._log(
                f"{completed_kind}写入读回一致；先丢弃"
                f"{wait_cycles or self.SETTLE_CYCLES:g}个稳定周期，"
                "随后另取2个新周期计算"
            )

    def _engage_falc(self) -> None:
        if self.pending_write or self.falc_engaged:
            return
        self.pending_write = True
        self.pending_kind = "falc"
        self.manual_advice = (
            "00模已达到设定标准；停止Scan并按FALC pro当前Path Selection使能，"
            "不会修改任何FALC增益、滤波或范围参数。双路径严格执行："
            "Scan Off并校验 → Main On并校验 → Unlim On并校验。"
        )
        self._log(self.manual_advice)
        self.session.engage_configured_falc()

    def _falc_completed(self, snapshot) -> None:
        falc = getattr(snapshot, "falc1", None)
        if falc is None:
            self._log_write("falc", 1.0, None, 0.0, False, snapshot)
            self.pending_write = False
            self.stop("FALC pro读回不可用，无法确认使能结果")
            return
        path = int(falc.path_selection)
        main_ok = not (path & 2) or bool(falc.main.enabled)
        unlim_ok = not (path & 1) or bool(falc.unlim.enabled)
        scan_stopped = not bool(snapshot.sc_enabled)
        if path not in (1, 2, 3) or not main_ok or not unlim_ok or not scan_stopped:
            self._log_write("falc", 1.0, 0.0, 0.0, False, snapshot)
            self.pending_write = False
            self.stop("FALC pro使能后读回校验失败，已停止自动流程")
            return
        self.pending_write = False
        self.pending_kind = ""
        self.falc_engaged = True
        self._log_write("falc", 1.0, 1.0, 0.0, True, snapshot)
        selected_states = []
        if path & 1:
            selected_states.append(
                f"Unlim Lock State={'锁定' if falc.unlim.lock_state else '待确认'}"
            )
        if path & 2:
            selected_states.append(
                f"Main Lock State={'锁定' if falc.main.lock_state else '待确认'}"
            )
        self.manual_advice = (
            "FALC pro接管读回通过（Scan=Off，Main先于Unlim使能）；"
            + "，".join(selected_states)
            + "。自动找峰流程已结束，请观察波形并确认锁定状态。"
        )
        self._emit_status(
            self.last_observation,
            ControlAction("none", None, self.manual_advice, "falc_enabled"),
        )
        self.stop(self.manual_advice, result="falc_complete")

    def _connection_changed(self, connected: bool, text: str) -> None:
        if self.running and not connected:
            self.stop(f"DLC pro{text}，自动锁频终止")

    def _session_error(self, message: str) -> None:
        if self.pending_write:
            self.pending_write = False
            self.pending_value = None
            self.pending_wait_cycles = 0.0
            self.settle_pending = False
            self.restore_queue.clear()
        if self.running:
            self.stop(f"DLC pro写入失败：{message}")

    def _emit_status(self, observation: PeakObservation,
                     action: ControlAction | None = None) -> None:
        engine = self.engine
        stage = engine.current_stage if engine is not None else None
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
            "target_amplitude": (
                engine.amplitude_floor if engine is not None else 0.0
            ),
            "scan_frequency": self.scan_frequency,
            "scan_unit": self.scan_unit,
            "offset_step": (
                engine.step_size if engine is not None else 0.0
            ),
            "step_profile": self.step_profile,
            "stage_name": stage.name if stage is not None else "--",
            "stage_tolerance": (
                stage.balance_tolerance if stage is not None else 0.0
            ),
            "stage_windows": stage.stable_windows if stage is not None else 0,
            "stage_target_amplitude": (
                stage.next_amplitude if stage is not None else None
            ),
            "manual_advice": self.manual_advice,
        })

    def _log(self, text: str) -> None:
        # Waiting/settling guidance belongs to the status area.  Keeping it out
        # of the event stream makes the four algorithm event types replayable.
        self.manual_advice = text

    def _emit_event_line(self, event: str, fields: list[str]) -> None:
        body = "，".join(item for item in fields if item)
        self.log_message.emit(f"{time.strftime('%H:%M:%S')}  {event}  {body}")

    def _begin_log_session(self, settings: PeakBalanceSettings, snapshot,
                           observe_only: bool) -> None:
        device = {
            "frequency_hz": float(snapshot.sc_frequency),
            "amplitude_vpp": abs(float(snapshot.sc_amplitude)),
            "offset_v": float(snapshot.sc_offset),
            "scan_enabled": bool(snapshot.sc_enabled),
            "scan_signal_type": int(snapshot.sc_signal_type),
            "scan_output_channel": int(getattr(snapshot, "sc_output_channel", -1)),
            "scan_unit": str(getattr(snapshot, "sc_unit", "") or ""),
        }
        self.log_session = _AutoLockCsvSession(
            self.LOG_DIRECTORY,
            mode="observe" if observe_only else "auto",
            settings=settings.as_dict(),
            device_start=device,
        )
        self.last_log_path = self.log_session.path
        self._emit_event_line("START", [
            f"模式={'观察' if observe_only else '自动'}",
            f"频率={device['frequency_hz']:.6f} Hz",
            f"Amplitude={device['amplitude_vpp']:.6f} Vpp",
            f"Offset={device['offset_v']:.6f} V",
            "参数=21项已记录",
        ])

    def _finish_log_session(self, result: str, reason: str) -> None:
        session = self.log_session
        self.log_session = None
        if session is None:
            return
        path = session.finish(result, reason)
        self.last_log_path = path
        self._emit_event_line("END", [f"结果={result}", f"原因={reason}", f"文件={path}"])

    def _log_write(self, kind: str, requested: float | None, actual: float | None,
                   tolerance: float | None, ok: bool, snapshot=None) -> None:
        engine = self.engine
        amplitude = (
            abs(float(snapshot.sc_amplitude)) if snapshot is not None
            else (engine.current_amplitude if engine is not None else "")
        )
        offset = (
            float(snapshot.sc_offset) if snapshot is not None
            else (engine.current_offset if engine is not None else "")
        )
        if self.log_session is not None:
            self.log_session.write(
                "WRITE", state=engine.state if engine is not None else "initializing",
                frequency_hz=(float(snapshot.sc_frequency) if snapshot is not None else self.scan_frequency),
                amplitude_vpp=amplitude, offset_v=offset, write_kind=kind,
                requested_value=requested, readback_value=actual,
                write_tolerance=tolerance, write_ok=int(ok),
            )
        self._emit_event_line("WRITE", [
            f"类型={kind}", f"请求={requested if requested is not None else '--'}",
            f"读回={actual if actual is not None else '--'}", f"结果={'通过' if ok else '失败'}",
            f"Amplitude={float(amplitude):.6f} Vpp" if amplitude != "" else "",
            f"Offset={float(offset):.6f} V" if offset != "" else "",
        ])

    def _log_decision(
        self, observation: PeakObservation, action: ControlAction
    ) -> None:
        engine = self.engine
        if engine is None:
            return
        reference = engine.trial_origin_error
        low = engine.current_offset - 0.5 * engine.current_amplitude
        high = engine.current_offset + 0.5 * engine.current_amplitude
        theoretical_error = (
            reference if action.state == "wide_jump" and reference is not None
            else observation.balance_error
        )
        theoretical = (
            engine.theoretical_distance(engine.current_amplitude, theoretical_error)
            if observation.valid and engine.current_amplitude > engine.amplitude_floor * 1.001
            else 0.0
        )
        stage = engine.current_stage
        if self.log_session is not None:
            self.log_session.write(
                "MEASURE", state=action.state, valid=int(observation.valid),
                reason_code=observation.reason_code or action.reason_code,
                reason=observation.reason, frequency_hz=self.scan_frequency,
                amplitude_vpp=engine.current_amplitude, offset_v=engine.current_offset,
                scan_low_v=low, scan_high_v=high, peak_count=observation.peak_count,
                family_count=observation.family_count,
                main_prominence=observation.prominence,
                second_prominence=observation.second_prominence,
                family_ratio=observation.dominance_ratio, snr=observation.snr,
                peak_width_s=observation.width_seconds,
                expected_period_s=observation.expected_period,
                measured_period_s=observation.measured_period,
                period_error=observation.period_error,
                delta_t1_s=observation.delta_t1, delta_t2_s=observation.delta_t2,
                signed_error=observation.signed_error,
                balance_error=observation.balance_error,
                balance_tolerance=stage.balance_tolerance,
                reference_value=reference, step_v=engine.step_size,
                direction=engine.direction, theoretical_distance_v=theoretical,
                action=action.kind, target_value=action.value,
                details_json=json.dumps({"action_reason": action.reason}, ensure_ascii=False),
            )
        self._emit_event_line("MEASURE", [
            f"状态={action.state}", f"有效={int(observation.valid)}",
            f"原因码={observation.reason_code or action.reason_code or '--'}",
            f"频率={self.scan_frequency:.6f} Hz",
            f"Amplitude={engine.current_amplitude:.6f} Vpp",
            f"Offset={engine.current_offset:.6f} V",
            f"扫描=[{low:.6f},{high:.6f}] V",
            f"主/次峰族={observation.prominence:.1f}/{observation.second_prominence:.1f}",
            f"强度比={observation.dominance_ratio:.2f}",
            f"周期误差={observation.period_error * 100:.2f}%",
            f"不均匀度={observation.balance_error * 100:.2f}%",
            f"门槛={stage.balance_tolerance * 100:.2f}%",
            f"步长={engine.step_size:.6f} V",
            f"动作={action.kind}->{action.value if action.value is not None else '--'}",
        ])
