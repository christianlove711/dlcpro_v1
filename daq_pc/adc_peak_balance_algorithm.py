"""Raw-ADC carrier selection and Scan Offset/Amplitude control policy."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np


Polarity = Literal["auto", "positive", "negative"]
PC_VOLTAGE_MIN = -1.0
PC_VOLTAGE_MAX = 140.0


@dataclass(frozen=True, slots=True)
class AmplitudeStage:
    name: str
    balance_tolerance: float
    offset_step: float
    min_offset_step: float
    shrink_ratio: float | None
    stable_windows: int


@dataclass(slots=True)
class PeakBalanceSettings:
    channel: str = "A"
    polarity: Polarity = "auto"
    min_prominence_codes: float = 50.0
    noise_sigma: float = 6.0
    carrier_dominance_ratio: float = 2.0
    offset_step: float = 0.05
    min_offset_step: float = 0.001
    max_offset_deviation: float = 0.5
    shrink_ratio: float = 0.75
    target_amplitude: float = 0.2
    max_search_amplitude_factor: float = 2.0
    min_amplitude_fraction: float = 0.05
    safety_margin: float = 0.25
    balance_tolerance: float = 0.05
    stable_windows: int = 3
    search_tolerance: float = 0.08
    search_windows: int = 2
    prediction_gain: float = 0.8
    max_model_corrections: int = 2
    final_local_max_distance: float = 0.009
    final_fallback_step: float = 0.01
    final_fallback_max_distance: float = 0.09
    final_local_entry_tolerance: float = 0.15
    search_frequency_hz: float = 10.0
    initial_search_amplitude: float = 2.5
    initial_offset_search_step: float = 1.0
    coarse_boundary: float = 2.0
    medium_boundary: float = 1.0
    fine_boundary: float = 0.5
    coarse_tolerance: float = 0.20
    medium_tolerance: float = 0.12
    fine_tolerance: float = 0.08
    narrow_tolerance: float = 0.06
    coarse_step: float = 0.1
    medium_step: float = 0.05
    fine_step: float = 0.01
    narrow_step: float = 0.001
    final_step: float = 0.001
    coarse_shrink: float = 0.70
    medium_shrink: float = 0.75
    fine_shrink: float = 0.75
    narrow_shrink: float = 0.80
    coarse_windows: int = 1
    medium_windows: int = 2
    fine_windows: int = 2
    narrow_windows: int = 2

    def validated(self) -> "PeakBalanceSettings":
        channel = str(self.channel).upper()
        if channel not in {"A", "B"}:
            raise ValueError("透射峰通道必须是A或B")
        if self.polarity not in {"auto", "positive", "negative"}:
            raise ValueError("峰极性无效")
        if (self.offset_step <= 0 or self.min_offset_step <= 0
                or self.max_offset_deviation <= 0):
            raise ValueError("Offset步长和最大允许偏移必须大于0")
        if self.min_offset_step > self.offset_step:
            raise ValueError("Offset最小步长不能大于Offset初始步长")
        if not 0.2 <= self.shrink_ratio < 1.0:
            raise ValueError("Amplitude缩小比例必须位于0.2到1之间")
        if not 0.0 < self.min_amplitude_fraction < 1.0:
            raise ValueError("最小幅度保护比例必须位于0到1之间")
        if self.target_amplitude <= 0:
            raise ValueError("最终扫频范围目标必须大于0")
        if self.initial_search_amplitude < self.target_amplitude:
            raise ValueError("初始化扫频范围不能小于最终扫频范围目标")
        if self.initial_offset_search_step <= 0:
            raise ValueError("初始化无峰Offset步长必须大于0")
        if not 1.0 <= self.max_search_amplitude_factor <= 10.0:
            raise ValueError("无峰最大扩幅倍数必须位于1到10之间")
        if self.carrier_dominance_ratio <= 1.0:
            raise ValueError("00模/次峰强度比必须大于1")
        if not 0.0 < self.balance_tolerance < 0.5:
            raise ValueError("峰间隔容差必须位于0到0.5之间")
        if not 0.0 < self.search_tolerance < 0.5:
            raise ValueError("快速寻峰允许不均匀度必须位于0到0.5之间")
        if not 0.0 < self.final_local_entry_tolerance < 0.5:
            raise ValueError("最终邻域搜索入口必须位于0到0.5之间")
        if self.final_local_entry_tolerance < self.balance_tolerance:
            raise ValueError("最终邻域搜索入口不能小于最终验收门槛")
        if not 0.0 < self.prediction_gain <= 1.0:
            raise ValueError("理论预测增益必须位于0到1之间")
        if not 0 <= int(self.max_model_corrections) <= 10:
            raise ValueError("模型最大修正次数必须位于0到10之间")
        if self.final_local_max_distance < self.min_offset_step:
            raise ValueError("最终邻域最大距离不能小于Offset最小步长")
        if self.final_fallback_step <= self.min_offset_step:
            raise ValueError("最终扩展搜索步长必须大于Offset最小步长")
        if self.final_fallback_max_distance < self.final_fallback_step:
            raise ValueError("最终扩展搜索范围不能小于最终扩展搜索步长")
        if not 0.01 <= self.search_frequency_hz <= 1000.0:
            raise ValueError("快速扫频频率必须位于0.01到1000 Hz之间")
        for value in (
            self.coarse_tolerance, self.medium_tolerance,
            self.fine_tolerance, self.narrow_tolerance,
        ):
            if not 0.0 < value < 0.5:
                raise ValueError("各阶段允许不均匀度必须位于0到50%之间")
        for value in (
            self.coarse_step, self.medium_step,
            self.fine_step, self.narrow_step, self.final_step,
        ):
            if value < self.min_offset_step:
                raise ValueError("各阶段Offset步长不能小于Offset绝对最小步长")
        for value in (
            self.coarse_shrink, self.medium_shrink,
            self.fine_shrink, self.narrow_shrink,
        ):
            if not 0.2 <= value < 1.0:
                raise ValueError("各阶段缩幅倍率必须位于0.2到1之间")
        for value in (
            self.search_windows, self.stable_windows,
        ):
            if not 1 <= int(value) <= 10:
                raise ValueError("各阶段连续确认窗口必须位于1到10之间")
        return replace(self, channel=channel)

    def stage_for(self, amplitude: float, amplitude_floor: float) -> AmplitudeStage:
        amplitude = abs(float(amplitude))
        if amplitude <= amplitude_floor * 1.001:
            return AmplitudeStage(
                "最终锁定", self.balance_tolerance, self.min_offset_step,
                self.min_offset_step, None, self.stable_windows,
            )
        direct_ratio = amplitude_floor / max(amplitude, 1e-12)
        return AmplitudeStage(
            "快速寻峰", self.search_tolerance, self.offset_step,
            self.min_offset_step, direct_ratio, self.search_windows,
        )


@dataclass(slots=True)
class CarrierFingerprint:
    prominence: float
    width_seconds: float
    polarity: str

    def update(self, observation: "PeakObservation", alpha: float = 0.1) -> None:
        self.prominence = (
            (1.0 - alpha) * self.prominence + alpha * observation.prominence
        )
        self.width_seconds = (
            (1.0 - alpha) * self.width_seconds
            + alpha * observation.width_seconds
        )


@dataclass(slots=True)
class PeakObservation:
    valid: bool
    reason: str
    polarity: str = "positive"
    baseline: float = 0.0
    noise: float = 0.0
    threshold: float = 0.0
    peak_times: tuple[float, ...] = ()
    prominence: float = 0.0
    second_prominence: float = 0.0
    dominance_ratio: float = 0.0
    width_seconds: float = 0.0
    snr: float = 0.0
    delta_t1: float = 0.0
    delta_t2: float = 0.0
    measured_period: float = 0.0
    balance_error: float = 1.0

    @property
    def ambiguous(self) -> bool:
        return self.reason == "00模候选不唯一"


@dataclass(slots=True)
class ControlAction:
    kind: Literal["none", "offset", "amplitude", "stop"]
    value: float | None
    reason: str
    state: str


def _robust_noise(values: np.ndarray) -> tuple[float, float]:
    # At 0.2 Vpp the carrier can occupy much of every scan period.  A global
    # MAD then mistakes the physical line shape for noise and raises the peak
    # threshold above the signal.  Estimate the detector floor from the lower
    # fifth of the envelope so the same criterion remains usable after the
    # one-step SEARCH→FINAL amplitude change.
    cutoff = float(np.percentile(values, 20.0))
    floor = values[values <= cutoff]
    baseline = float(np.median(floor))
    noise = float(np.median(np.abs(floor - baseline)) * 1.4826)
    return baseline, noise


def _peak_groups(values: np.ndarray, valid: np.ndarray, threshold: float,
                 bin_seconds: float, min_distance_bins: int):
    """Return separated local maxima and their half-prominence widths.

    A narrow scan can keep a broad resonance above one absolute threshold
    through a triangle-wave turning point.  Threshold-island grouping then
    joins the forward and reverse crossings into one peak.  Local maxima plus
    non-maximum suppression retains the two physical crossing times even in
    that case, while ``min_distance_bins`` rejects several noisy maxima on the
    same line shape.
    """
    if values.size < 3:
        return []
    candidates = np.flatnonzero(
        valid[1:-1]
        & (values[1:-1] >= threshold)
        & (values[1:-1] >= values[:-2])
        & (values[1:-1] > values[2:])
    ) + 1
    if candidates.size == 0:
        return []

    selected: list[int] = []
    for index in candidates[np.argsort(values[candidates])[::-1]]:
        index = int(index)
        if all(abs(index - previous) >= min_distance_bins
               for previous in selected):
            selected.append(index)

    peaks = []
    for index in sorted(selected):
        half_height = threshold + 0.5 * (float(values[index]) - threshold)
        start = index
        while (start > 0 and valid[start - 1]
               and values[start - 1] >= half_height):
            start -= 1
        stop = index + 1
        while (stop < values.size and valid[stop]
               and values[stop] >= half_height):
            stop += 1
        peaks.append((
            index, float(values[index]), max(1, stop - start) * bin_seconds,
        ))
    return peaks


def analyze_carrier(history, settings: PeakBalanceSettings,
                    scan_frequency: float,
                    fingerprint: CarrierFingerprint | None = None,
                    after_bin: int | None = None) -> PeakObservation:
    """Select the strong 00-mode family and measure alternating peak spacing."""
    settings = settings.validated()
    if scan_frequency <= 0:
        return PeakObservation(False, "扫描频率无效")
    indices = np.asarray(history.bin_indices, dtype=np.int64)
    valid = np.asarray(history.valid, dtype=bool)
    if after_bin is not None:
        keep = indices > int(after_bin)
        indices, valid = indices[keep], valid[keep]
    else:
        keep = slice(None)
    if indices.size < 16:
        return PeakObservation(False, "等待足够的扫描周期")
    if not np.all(valid):
        return PeakObservation(False, "分析窗口存在ADC索引空洞")

    if settings.channel == "A":
        minimum = np.asarray(history.minimum_a)[keep].astype(np.float64)
        maximum = np.asarray(history.maximum_a)[keep].astype(np.float64)
    else:
        minimum = np.asarray(history.minimum_b)[keep].astype(np.float64)
        maximum = np.asarray(history.maximum_b)[keep].astype(np.float64)
    positive_baseline, positive_noise = _robust_noise(maximum)
    negative_values = -minimum
    negative_baseline, negative_noise = _robust_noise(negative_values)
    positive_score = float(np.max(maximum) - positive_baseline)
    negative_score = float(np.max(negative_values) - negative_baseline)
    polarity = settings.polarity
    if polarity == "auto":
        polarity = "positive" if positive_score >= negative_score else "negative"
    if polarity == "positive":
        values, baseline, noise = maximum, positive_baseline, positive_noise
    else:
        values, baseline, noise = negative_values, negative_baseline, negative_noise

    prominence_threshold = max(
        float(settings.min_prominence_codes),
        float(settings.noise_sigma) * max(noise, 1e-9),
    )
    period = 1.0 / float(scan_frequency)
    merge_bins = max(1, int(round(0.12 * period / history.bin_seconds)))
    groups = _peak_groups(
        values, valid, baseline + prominence_threshold,
        float(history.bin_seconds), merge_bins,
    )
    duration = (indices[-1] - indices[0] + 1) * float(history.bin_seconds)
    expected_carrier_peaks = max(4, int(round(2.0 * duration / period)))
    if len(groups) < 4:
        return PeakObservation(
            False, "未找到足够的00模穿越峰", polarity=polarity,
            baseline=baseline, noise=noise, threshold=prominence_threshold,
        )

    ranked = sorted(
        groups, key=lambda item: item[1] - baseline, reverse=True
    )
    carrier = ranked[:min(expected_carrier_peaks, len(ranked))]
    remaining = ranked[len(carrier):len(carrier) * 2]
    carrier_prominences = np.array(
        [item[1] - baseline for item in carrier], dtype=np.float64
    )
    prominence = float(np.median(carrier_prominences))
    second = float(np.median(
        [item[1] - baseline for item in remaining]
    )) if remaining else 0.0
    ratio = prominence / max(second, noise, 1e-9)
    if remaining and ratio < settings.carrier_dominance_ratio:
        return PeakObservation(
            False, "00模候选不唯一", polarity=polarity,
            baseline=baseline, noise=noise, threshold=prominence_threshold,
            prominence=prominence, second_prominence=second,
            dominance_ratio=ratio,
        )

    carrier.sort(key=lambda item: item[0])
    times = np.array(
        [item[0] * float(history.bin_seconds) for item in carrier],
        dtype=np.float64,
    )
    differences = np.diff(times)
    # Reject extra peaks from one family before computing alternating intervals.
    min_spacing = 0.12 * period
    if differences.size and np.any(differences < min_spacing):
        filtered = [carrier[0]]
        for peak in carrier[1:]:
            if (peak[0] - filtered[-1][0]) * history.bin_seconds >= min_spacing:
                filtered.append(peak)
        carrier = filtered
        times = np.array(
            [item[0] * float(history.bin_seconds) for item in carrier]
        )
        differences = np.diff(times)
    if differences.size < 3:
        return PeakObservation(False, "00模周期重复次数不足", polarity=polarity)
    delta1 = float(np.median(differences[::2]))
    delta2_values = differences[1::2]
    if delta2_values.size == 0:
        return PeakObservation(False, "00模双向穿越不完整", polarity=polarity)
    delta2 = float(np.median(delta2_values))
    measured_period = delta1 + delta2
    if abs(measured_period - period) / period > 0.10:
        return PeakObservation(
            False, "峰周期与DLC pro扫描频率不一致", polarity=polarity,
            measured_period=measured_period,
        )
    balance = abs(delta1 - delta2) / max(measured_period, 1e-12)
    width = float(np.median([item[2] for item in carrier]))
    snr = prominence / max(noise, 1e-9)
    if fingerprint is not None:
        height_ratio = prominence / max(fingerprint.prominence, 1e-9)
        width_ratio = width / max(fingerprint.width_seconds, history.bin_seconds)
        if not (0.2 <= height_ratio <= 5.0 and 0.2 <= width_ratio <= 5.0):
            return PeakObservation(
                False, "候选峰与00模历史指纹不符", polarity=polarity,
                prominence=prominence, width_seconds=width, snr=snr,
            )
    return PeakObservation(
        True, "00模有效", polarity=polarity, baseline=baseline, noise=noise,
        threshold=prominence_threshold, peak_times=tuple(times.tolist()),
        prominence=prominence, second_prominence=second,
        dominance_ratio=ratio, width_seconds=width, snr=snr,
        delta_t1=delta1, delta_t2=delta2,
        measured_period=measured_period, balance_error=balance,
    )


class PeakBalanceEngine:
    """Decision-only state machine; device I/O remains in the Qt controller."""

    def __init__(self, settings: PeakBalanceSettings):
        self.settings = settings.validated()
        self.state = "idle"
        self.start_offset = self.current_offset = 0.0
        self.start_amplitude = self.current_amplitude = 0.0
        self.previous_amplitude = 0.0
        self.last_good_amplitude = 0.0
        self.fail_amplitude: float | None = None
        self.fingerprint: CarrierFingerprint | None = None
        self.previous_error: float | None = None
        self.previous_offset = 0.0
        self.direction = 1.0
        self.base_step_size = self.settings.offset_step
        self.step_size = self.base_step_size
        self.stable_count = 0
        self.bad_track_count = 0
        self.recovery_attempt = 0
        self.recovery_origin: float | None = None
        self.refine_attempt = 0
        self.finalized = False
        self.ambiguous_count = 0
        self.missing_count = 0
        self.startup_search_attempt = 0
        self.trial_origin_offset: float | None = None
        self.trial_origin_error: float | None = None
        self.trial_direction = 1.0
        self.trial_step = self.step_size
        self.best_offset = 0.0
        self.best_error: float | None = None
        self.best_observation: PeakObservation | None = None
        self.neutral_count = 0
        self.boundary_directions: set[int] = set()
        self.last_decision = ""
        self.origin_offset: float | None = None
        self.origin_error: float | None = None
        self.predicted_distance = 0.0
        self.physical_direction: int | None = None
        self.model_correction_count = 0
        self.model_reference_error: float | None = None
        self.full_prediction_retried = False
        self.local_origin_offset: float | None = None
        self.local_candidates: list[float] = []
        self.local_best_offset = 0.0
        self.local_best_error: float | None = None
        self.local_search_completed = False
        self.local_search_phase = ""
        self.final_fallback_started = False

    @property
    def offset_limits(self) -> tuple[float, float]:
        span = self.settings.max_offset_deviation
        return self.start_offset - span, self.start_offset + span

    @property
    def amplitude_floor(self) -> float:
        """The explicit operator target is the hard staged-control floor."""
        return self.settings.target_amplitude

    @property
    def search_amplitude_ceiling(self) -> float:
        return self.start_amplitude * self.settings.max_search_amplitude_factor

    @property
    def current_stage(self) -> AmplitudeStage:
        return self.settings.stage_for(self.current_amplitude, self.amplitude_floor)

    def start(self, offset: float, amplitude: float) -> None:
        if abs(amplitude) <= 1e-12:
            raise ValueError("启动Scan Amplitude不能为0")
        self.start_offset = self.current_offset = float(offset)
        self.start_amplitude = self.current_amplitude = abs(float(amplitude))
        self.previous_amplitude = self.current_amplitude
        if self.settings.target_amplitude > self.start_amplitude + 1e-12:
            raise ValueError("最终扫频范围目标不能大于启动Scan Amplitude")
        self.last_good_amplitude = self.current_amplitude
        self.best_offset = self.current_offset
        self.best_error = None
        self.best_observation = None
        self.origin_offset = None
        self.origin_error = None
        self.predicted_distance = 0.0
        self.physical_direction = None
        self.model_correction_count = 0
        self.model_reference_error = None
        self.full_prediction_retried = False
        self.local_origin_offset = None
        self.local_candidates.clear()
        self.local_best_offset = self.current_offset
        self.local_best_error = None
        self.local_search_completed = False
        self.local_search_phase = ""
        self.final_fallback_started = False
        self.finalized = False
        self.stable_count = 0
        self.startup_search_attempt = 0
        self._clear_trial()
        self.state = "select"

    def sync(self, offset: float, amplitude: float) -> None:
        self.current_offset = float(offset)
        amplitude = abs(float(amplitude))
        if abs(amplitude - self.current_amplitude) > 1e-12:
            self.previous_amplitude = self.current_amplitude
        self.current_amplitude = amplitude

    def set_offset_step(self, step: float) -> bool:
        """Switch the amplitude-dependent tuning gear without carrying old probes."""
        step = max(
            float(step), self.settings.min_offset_step,
            self.current_stage.min_offset_step,
        )
        if step <= 0:
            raise ValueError("Offset步长必须大于0")
        if abs(step - self.base_step_size) <= 1e-12:
            return False
        self.base_step_size = step
        self.step_size = step
        self.previous_error = None
        self.previous_offset = self.current_offset
        self._clear_trial()
        return True

    @staticmethod
    def _decision_margin(reference_error: float) -> float:
        """Absolute balance-error deadband: 0.5 percentage point or 5%."""
        return max(0.005, abs(float(reference_error)) * 0.05)

    def _clear_trial(self) -> None:
        self.trial_origin_offset = None
        self.trial_origin_error = None
        self.neutral_count = 0

    def reset_direction_experiment(self) -> None:
        """Discard direction evidence after a frequency or operator change."""
        self.previous_error = None
        self.previous_offset = self.current_offset
        self.direction = 1.0
        self.step_size = self.base_step_size
        self.stable_count = 0
        self.bad_track_count = 0
        self.boundary_directions.clear()
        self._clear_trial()

    def reset_after_amplitude_change(self) -> None:
        """Preserve the learned Offset direction across the SEARCH→FINAL jump."""
        if (self.fingerprint is not None and self.current_amplitude > 1e-12
                and self.previous_amplitude > 1e-12):
            # For the same spectral peak, its temporal width scales roughly
            # inversely with triangle-scan amplitude.  Rebase the fingerprint
            # before validating the first narrow-window observation.
            self.fingerprint.width_seconds *= (
                self.previous_amplitude / self.current_amplitude
            )
        self.best_offset = self.current_offset
        self.best_error = None
        self.best_observation = None
        self.recovery_attempt = 0
        self.recovery_origin = None
        if self.state == "final_shrink":
            self.stable_count = 0
            self.local_origin_offset = self.current_offset
            self.local_candidates.clear()
            self.local_best_offset = self.current_offset
            self.local_best_error = None
            self.local_search_completed = False
            self.local_search_phase = ""
            self.final_fallback_started = False
            self.state = "final_verify"
            return
        self.reset_direction_experiment()

    def reset_after_frequency_change(self) -> None:
        """Frequency changes invalidate both timing evidence and old optima."""
        self.best_offset = self.current_offset
        self.best_error = None
        self.best_observation = None
        self.recovery_attempt = 0
        self.recovery_origin = None
        self.physical_direction = None
        self.reset_direction_experiment()

    def _remember_best(self, observation: PeakObservation) -> None:
        if (self.best_error is None
                or observation.balance_error < self.best_error):
            self.best_error = observation.balance_error
            self.best_offset = self.current_offset
            self.best_observation = observation
            self.boundary_directions.clear()

    def _action(self, kind, value, reason, state=None):
        if state is not None:
            self.state = state
        return ControlAction(kind, value, reason, self.state)

    def _offset_action(
        self, target: float, reason: str, state=None, *,
        physical_bounds: bool = False,
    ):
        if physical_bounds:
            low = PC_VOLTAGE_MIN + 0.5 * self.current_amplitude
            high = PC_VOLTAGE_MAX - 0.5 * self.current_amplitude
        else:
            low, high = self.offset_limits
        target = float(target)
        requested_direction = 1 if target > self.current_offset else -1
        if target < low - 1e-12 or target > high + 1e-12:
            self.boundary_directions.add(requested_direction)
            opposite = -requested_direction
            reduced = max(
                self.current_stage.min_offset_step, self.step_size / 2.0
            )
            reverse_target = self.best_offset + opposite * reduced
            if (opposite not in self.boundary_directions
                    and low <= reverse_target <= high
                    and abs(reverse_target - self.current_offset) > 1e-12):
                self.direction = float(opposite)
                self.step_size = reduced
                self.trial_origin_offset = self.best_offset
                self.trial_origin_error = self.best_error
                self.trial_direction = self.direction
                self.trial_step = reduced
                self.last_decision = "单侧安全边界：回到最佳点并反向减小步长"
                return self._action(
                    "offset", reverse_target,
                    f"即将越过Offset安全边界[{low:.6f}, {high:.6f}]；"
                    f"从最佳Offset={self.best_offset:.6f}反向，步长={reduced:.6f}",
                    state or "center",
                )
            if abs(self.current_offset - self.best_offset) > 1e-12:
                self.last_decision = "两侧边界受限：恢复历史最佳Offset"
                return self._action(
                    "offset", self.best_offset,
                    f"Offset两侧搜索受限；恢复最佳Offset={self.best_offset:.6f}，"
                    f"最佳不均匀度={((self.best_error if self.best_error is not None else 1.0) * 100):.2f}%",
                    "boundary_recover",
                )
            detail = (
                f"Offset安全范围[{low:.6f}, {high:.6f}]两侧均已尝试；"
                f"最佳Offset={self.best_offset:.6f}，最佳不均匀度="
                f"{((self.best_error if self.best_error is not None else 1.0) * 100):.2f}%"
            )
            if self.current_amplitude < self.last_good_amplitude * 0.999:
                return self._action(
                    "amplitude", self.last_good_amplitude,
                    detail + "；先恢复上一级可靠Amplitude后重新识别",
                    "restore_amplitude",
                )
            return self._action("stop", None, detail, "fault")
        bounded = target
        if abs(bounded - self.current_offset) < 1e-12:
            return self._action("none", None, "Offset目标与当前读回相同", state)
        self.previous_offset = self.current_offset
        return self._action("offset", bounded, reason, state)

    def _start_trial(
        self, observation: PeakObservation, direction: float, step: float,
        reason: str, state: str = "probe", *, origin_offset: float | None = None,
        origin_error: float | None = None,
    ) -> ControlAction:
        origin = self.current_offset if origin_offset is None else origin_offset
        reference = (
            observation.balance_error if origin_error is None else origin_error
        )
        self.trial_origin_offset = float(origin)
        self.trial_origin_error = float(reference)
        self.trial_direction = 1.0 if direction >= 0 else -1.0
        self.trial_step = float(step)
        self.direction = self.trial_direction
        self.step_size = float(step)
        self.neutral_count = 0
        self.last_decision = reason
        return self._offset_action(
            origin + self.trial_direction * self.trial_step,
            f"{reason}；参考不均匀度={reference * 100:.2f}%，"
            f"方向={'+' if self.trial_direction > 0 else '-'}，步长={step:.6f}",
            state,
        )

    def _reverse_from_best(self, reason: str) -> ControlAction:
        stage = self.current_stage
        old_direction = self.trial_direction or self.direction
        step = max(stage.min_offset_step, self.trial_step / 2.0)
        reference = self.best_error
        if reference is None:
            reference = self.trial_origin_error
        if reference is None:
            reference = 1.0
        origin = self.best_offset
        self.trial_origin_offset = origin
        self.trial_origin_error = reference
        self.trial_direction = -old_direction
        self.trial_step = step
        self.direction = self.trial_direction
        self.step_size = step
        self.neutral_count = 0
        self.last_decision = reason
        return self._offset_action(
            origin + self.trial_direction * step,
            f"{reason}；恢复最佳Offset={origin:.6f}，反向后步长={step:.6f}，"
            f"参考不均匀度={reference * 100:.2f}%",
            "center",
        )

    @staticmethod
    def theoretical_distance(amplitude: float, balance_error: float) -> float:
        """Triangle-scan geometry: distance from center = A(Vpp)/2 × E."""
        return 0.5 * abs(float(amplitude)) * abs(float(balance_error))

    def _begin_centering(self, observation: PeakObservation) -> ControlAction:
        """Start the fast model path with exactly one positive direction probe."""
        self.origin_offset = self.current_offset
        self.origin_error = observation.balance_error
        self.predicted_distance = self.theoretical_distance(
            self.current_amplitude, observation.balance_error
        )
        self.model_reference_error = observation.balance_error
        self.model_correction_count = 0
        self.physical_direction = None
        self.full_prediction_retried = False
        self.previous_error = observation.balance_error
        self._remember_best(observation)
        self.stable_count = 0
        return self._start_trial(
            observation, 1.0, self.settings.offset_step,
            f"理论距离={self.predicted_distance:.6f} V，单次正向试探确定物理方向",
            "search_direction_probe", origin_offset=self.origin_offset,
            origin_error=self.origin_error,
        )

    def _begin_legacy_centering(
        self, observation: PeakObservation, reason: str
    ) -> ControlAction:
        """Fallback keeps the proven bounded probe/reverse/halve search."""
        self.previous_error = observation.balance_error
        self._remember_best(observation)
        self.stable_count = 0
        self.physical_direction = None
        return self._start_trial(
            observation, self.direction, max(self.step_size, self.settings.min_offset_step),
            reason, "probe",
        )

    def _search_acceptance(self, observation: PeakObservation) -> ControlAction:
        self.stable_count += 1
        self.state = "search_accept"
        if self.stable_count < self.settings.search_windows:
            return self._action(
                "none", None,
                f"快速寻峰居中确认 {self.stable_count}/{self.settings.search_windows}",
            )
        self.stable_count = 0
        self.last_good_amplitude = self.current_amplitude
        return self._action(
            "amplitude", self.amplitude_floor,
            f"快速寻峰通过；Amplitude从{self.current_amplitude:.6f} Vpp直接缩到"
            f"{self.amplitude_floor:.6f} Vpp",
            "final_shrink",
        )

    def _startup_offset_search_action(self) -> ControlAction:
        """Search symmetrically around the startup Offset without changing A."""
        final_stage = self.current_stage.shrink_ratio is None
        step = (
            self.settings.min_offset_step if final_stage
            else self.settings.initial_offset_search_step
        )
        search_span = (
            min(
                self.settings.max_offset_deviation,
                self.settings.final_local_max_distance,
            )
            if final_stage else self.settings.max_offset_deviation
        )
        if not final_stage:
            # Manual.md specifies the PC output range as -1 .. +140 V. Keep
            # the complete triangle (Offset ± A/2) inside that range while
            # performing the user-requested 1 V symmetric initialization scan.
            low = PC_VOLTAGE_MIN + 0.5 * self.current_amplitude
            high = PC_VOLTAGE_MAX - 0.5 * self.current_amplitude
            max_radius_index = int(np.ceil(
                max(self.start_offset - low, high - self.start_offset)
                / step - 1e-12
            ))
            while self.startup_search_attempt < 2 * max_radius_index:
                radius_index = self.startup_search_attempt // 2 + 1
                sign = 1.0 if self.startup_search_attempt % 2 == 0 else -1.0
                self.startup_search_attempt += 1
                target = self.start_offset + sign * radius_index * step
                if not low <= target <= high:
                    continue
                self.previous_offset = self.current_offset
                return self._action(
                    "offset", target,
                    f"初始化范围无透射峰；保持Amplitude="
                    f"{self.current_amplitude:.6f} Vpp，以{step:.6f} V为单位"
                    f"围绕初始化Offset搜索到{sign * radius_index * step:+.6f}",
                    "startup_offset_search",
                )
            return self._action(
                "stop", None,
                f"已在PC Voltage物理范围[{low:.3f}, {high:.3f}]内完成"
                "初始化Offset搜索，仍未找到透射峰",
                "fault",
            )
        max_radius_index = int(np.ceil(search_span / step - 1e-12))
        radius_index = self.startup_search_attempt // 2 + 1
        if radius_index > max_radius_index:
            self.local_origin_offset = self.start_offset
            self.local_best_offset = self.start_offset
            self.local_best_error = None
            self.local_search_phase = "fine"
            return self._begin_final_fallback_search(
                "最终幅度启动时0.001 V精细邻域未找到透射峰"
            )
        sign = 1.0 if self.startup_search_attempt % 2 == 0 else -1.0
        distance = min(
            radius_index * step, search_span
        )
        self.startup_search_attempt += 1
        target = self.start_offset + sign * distance
        return self._offset_action(
            target,
            f"启动窗口无透射峰；保持Amplitude={self.current_amplitude:.6f} Vpp，"
            f"围绕启动Offset以{step:.6f} V步长左右搜索到"
            f"{sign * distance:+.6f}",
            "startup_offset_search",
        )

    def _advance_invalid_final_candidate(self, reason: str) -> ControlAction:
        """Treat an invalid final-window sample as a rejected grid point."""
        if self.local_candidates:
            target = self.local_candidates.pop(0)
            return self._offset_action(
                target,
                f"当前{self._final_search_step():.3f} V候选无效（{reason}），"
                "继续比较下一候选",
                "final_local_search",
            )
        if self.local_search_phase == "fine":
            return self._begin_final_fallback_search(
                f"0.001 V精细邻域没有有效结果（{reason}）"
            )
        self.local_search_completed = True
        if (self.local_best_error is not None
                and abs(self.current_offset - self.local_best_offset) > 1e-12):
            return self._offset_action(
                self.local_best_offset,
                "最终邻域候选已遍历；恢复最后一个有效最佳Offset",
                "final_local_return",
            )
        return self._action(
            "stop", None,
            f"最终0.01 V扩展Offset搜索已遍历至"
            f"±{self.settings.final_fallback_max_distance:.3f} V，"
            "仍未得到可验收的有效透射峰；保持最终Amplitude不变",
            "fault",
        )

    def _model_target(self, origin: float, signed_move: float) -> float | None:
        low = PC_VOLTAGE_MIN + 0.5 * self.current_amplitude
        high = PC_VOLTAGE_MAX - 0.5 * self.current_amplitude
        target = origin + signed_move
        if target < low - 1e-12 or target > high + 1e-12:
            return None
        return target

    def _retry_full_prediction(self, reason: str) -> ControlAction | None:
        if (self.full_prediction_retried or self.origin_offset is None
                or self.physical_direction is None):
            return None
        target = self._model_target(
            self.origin_offset,
            self.physical_direction * self.predicted_distance,
        )
        self.full_prediction_retried = True
        if target is None or abs(target - self.current_offset) < 1e-12:
            return None
        return self._offset_action(
            target,
            f"{reason}；直接尝试原始Offset加1.00×完整理论距离",
            "search_verify",
            physical_bounds=True,
        )

    def _handle_direction_probe(self, observation: PeakObservation) -> ControlAction:
        reference = self.origin_error
        origin = self.origin_offset
        if reference is None or origin is None:
            return self._begin_legacy_centering(observation, "模型基准丢失，进入旧搜索")
        margin = self._decision_margin(reference)
        if observation.balance_error < reference - margin:
            self.physical_direction = 1
        elif observation.balance_error > reference + margin:
            self.physical_direction = -1
        else:
            self.neutral_count += 1
            if self.neutral_count < 2:
                return self._action(
                    "none", None,
                    "方向试探变化落在判定死区，等待第二个独立窗口",
                )
            return self._begin_legacy_centering(
                observation, "方向试探无法可靠判定，进入旧搜索"
            )
        move = self.settings.prediction_gain * self.predicted_distance
        target = self._model_target(origin, self.physical_direction * move)
        if target is None or abs(target - self.current_offset) < 1e-12:
            return self._begin_legacy_centering(
                observation, "理论预测触及Offset安全边界，进入旧搜索"
            )
        self.model_reference_error = reference
        self.model_correction_count = 0
        self._clear_trial()
        return self._offset_action(
            target,
            f"方向={'+' if self.physical_direction > 0 else '-'}；从原始Offset="
            f"{origin:.6f}直接跳转理论距离×{self.settings.prediction_gain:.2f}",
            "search_verify",
            physical_bounds=True,
        )

    def _handle_model_verify(self, observation: PeakObservation) -> ControlAction:
        if observation.balance_error <= self.settings.search_tolerance:
            return self._search_acceptance(observation)
        reference = self.model_reference_error
        margin = self._decision_margin(reference or observation.balance_error)
        if (self.physical_direction is None or reference is None
                or observation.balance_error >= reference - margin
                or self.model_correction_count >= self.settings.max_model_corrections):
            return self._begin_legacy_centering(
                observation, "理论预测未继续改善，进入旧搜索"
            )
        distance = self.theoretical_distance(
            self.current_amplitude, observation.balance_error
        )
        move = self.settings.prediction_gain * distance
        target = self._model_target(
            self.current_offset, self.physical_direction * move
        )
        if target is None or abs(target - self.current_offset) < 1e-12:
            return self._begin_legacy_centering(
                observation, "模型残差修正触及安全边界，进入旧搜索"
            )
        self.model_reference_error = observation.balance_error
        self.model_correction_count += 1
        return self._offset_action(
            target,
            f"按剩余不均匀度直接修正Offset（第{self.model_correction_count}/"
            f"{self.settings.max_model_corrections}次）",
            "search_model_correct",
            physical_bounds=True,
        )

    def _begin_final_acceptance(self, observation: PeakObservation) -> ControlAction:
        self.stable_count = 1
        self.state = "final_accept"
        if self.stable_count >= self.settings.stable_windows:
            self.finalized = True
            return self._action(
                "none", None, "最终窗口验收通过，允许FALC接管", "track"
            )
        return self._action(
            "none", None,
            f"最终验收 {self.stable_count}/{self.settings.stable_windows}",
        )

    def _begin_final_local_search(
        self, observation: PeakObservation | None = None, *, reason: str = ""
    ) -> ControlAction:
        origin = self.current_offset
        step = self.settings.min_offset_step
        candidates = self._final_offset_candidates(
            origin, step, self.settings.final_local_max_distance
        )
        self.local_origin_offset = origin
        self.local_candidates = candidates
        self.local_best_offset = origin
        self.local_best_error = (
            observation.balance_error
            if observation is not None and observation.valid else None
        )
        self.local_search_completed = False
        self.local_search_phase = "fine"
        self.final_fallback_started = False
        self.stable_count = 0
        if not self.local_candidates:
            return self._action("stop", None, "最终0.001 V邻域没有可用候选", "fault")
        target = self.local_candidates.pop(0)
        prefix = f"{reason}；" if reason else ""
        return self._offset_action(
            target,
            f"{prefix}保持Amplitude={self.current_amplitude:.6f} Vpp，开始最终"
            f"±{self.settings.final_local_max_distance:.3f} V邻域搜索，"
            f"固定步长={step:.3f} V",
            "final_local_search",
        )

    def _final_offset_candidates(
        self, origin: float, step: float, span: float
    ) -> list[float]:
        configured_low, configured_high = self.offset_limits
        low = max(
            configured_low,
            PC_VOLTAGE_MIN + 0.5 * self.current_amplitude,
        )
        high = min(
            configured_high,
            PC_VOLTAGE_MAX - 0.5 * self.current_amplitude,
        )
        count = int(float(span) / float(step) + 1e-9)
        candidates: list[float] = []
        for index in range(1, count + 1):
            for sign in (1.0, -1.0):
                candidate = float(origin) + sign * index * float(step)
                if low <= candidate <= high:
                    candidates.append(candidate)
        return candidates

    def _final_search_step(self) -> float:
        if self.local_search_phase == "fallback":
            return self.settings.final_fallback_step
        return self.settings.min_offset_step

    def _begin_final_fallback_search(self, reason: str) -> ControlAction:
        """Keep final amplitude and expand Offset search with a 10 mV grid."""
        origin = (
            self.local_origin_offset
            if self.local_origin_offset is not None else self.current_offset
        )
        step = self.settings.final_fallback_step
        self.local_candidates = self._final_offset_candidates(
            origin, step, self.settings.final_fallback_max_distance
        )
        self.local_search_phase = "fallback"
        self.final_fallback_started = True
        self.local_search_completed = False
        if not self.local_candidates:
            return self._action(
                "stop", None,
                f"{reason}；最终0.01 V扩展搜索没有可用Offset候选，"
                "保持最终Amplitude不变",
                "fault",
            )
        target = self.local_candidates.pop(0)
        return self._offset_action(
            target,
            f"{reason}；保持Amplitude={self.current_amplitude:.6f} Vpp，"
            f"以精细搜索中心Offset={origin:.6f} V为基准，改用"
            f"{step:.3f} V步长左右扩展搜索至"
            f"±{self.settings.final_fallback_max_distance:.3f} V",
            "final_local_search",
        )

    def _handle_invalid_final_window(self, reason: str) -> ControlAction:
        """At final amplitude, search Offset locally without widening scan."""
        if self.state == "final_local_search":
            return self._advance_invalid_final_candidate(reason)
        if self.local_search_completed:
            return self._action(
                "stop", None,
                f"最终Offset扩展搜索已完成，当前窗口仍无效（{reason}）；"
                f"保持Amplitude={self.current_amplitude:.6f} Vpp，不恢复大扫幅",
                "fault",
            )
        return self._begin_final_local_search(
            reason=f"最终幅度首窗无效（{reason}）"
        )

    def _handle_final_local_search(
        self, observation: PeakObservation
    ) -> ControlAction:
        if (self.local_best_error is None
                or observation.balance_error < self.local_best_error):
            self.local_best_error = observation.balance_error
            self.local_best_offset = self.current_offset
        if observation.balance_error <= self.settings.balance_tolerance:
            return self._begin_final_acceptance(observation)
        if self.local_candidates:
            target = self.local_candidates.pop(0)
            return self._offset_action(
                target,
                f"比较下一个{self._final_search_step():.3f} V离散Offset候选",
                "final_local_search",
            )
        if self.local_search_phase == "fine":
            return self._begin_final_fallback_search(
                "0.001 V精细邻域已遍历但未达到最终标准"
            )
        self.local_search_completed = True
        if abs(self.current_offset - self.local_best_offset) > 1e-12:
            return self._offset_action(
                self.local_best_offset,
                f"邻域搜索完成，恢复最佳Offset；最佳不均匀度="
                f"{(self.local_best_error or 1.0) * 100:.2f}%",
                "final_local_return",
            )
        if (self.local_best_error is not None
                and self.local_best_error <= self.settings.balance_tolerance):
            return self._begin_final_acceptance(observation)
        return self._action(
            "stop", None,
            f"最终邻域搜索最佳不均匀度={(self.local_best_error or 1.0) * 100:.2f}%"
            "，未达到验收门槛",
            "fault",
        )

    def update(self, observation: PeakObservation) -> ControlAction:
        s = self.settings
        stage = self.current_stage
        model_states = {
            "search_direction_probe", "search_verify",
            "search_model_correct", "search_accept",
        }
        final_states = {
            "final_verify", "final_accept", "final_local_search",
            "final_local_return",
        }
        if observation.ambiguous:
            self.ambiguous_count += 1
            if self.state in final_states:
                return self._handle_invalid_final_window(observation.reason)
            if self.state in model_states and self.best_observation is not None:
                retry = self._retry_full_prediction("预测位置00模候选不唯一")
                if retry is not None:
                    return retry
                return self._begin_legacy_centering(
                    self.best_observation,
                    "模型阶段00模候选不唯一，进入旧搜索",
                )
            if (self.state in {"probe", "center", "track"}
                    and self.best_error is not None
                    and self.trial_origin_error is not None):
                return self._reverse_from_best(
                    "00模候选不唯一，本次Offset试探判为失败"
                )
            if self.state == "verify_shrink" and self.current_amplitude < self.last_good_amplitude:
                self.fail_amplitude = self.current_amplitude
                return self._action(
                    "amplitude", self.last_good_amplitude,
                    "缩幅后00模候选不唯一，恢复上一级可靠Amplitude",
                    "restore_amplitude",
                )
            if self.fingerprint is None:
                if self.current_stage.shrink_ratio is None:
                    return self._startup_offset_search_action()
                if self.recovery_origin is None:
                    self.recovery_origin = self.start_offset
                return self._recovery_action(
                    "启动阶段00模候选不唯一，围绕启动Offset对称搜索"
                )
            if self.state in {"center", "track"}:
                self.recovery_attempt = 0
                self.recovery_origin = self.best_offset
                return self._recovery_action(
                    "00模候选不唯一，围绕最近最佳Offset对称重捕获"
                )
        if observation.valid:
            self.ambiguous_count = 0
            self.missing_count = 0
            if self.state == "startup_offset_search":
                # The coarse initialization search may move by many volts.
                # Rebase the subsequent ±max_offset_deviation fine-control
                # safety window at the first valid transmission peak.
                self.start_offset = self.current_offset
                self.best_offset = self.current_offset
                self.best_error = None
                self.best_observation = None
                self.state = "select"
            self._remember_best(observation)
        if self.state == "select":
            if not observation.valid:
                if observation.reason == "未找到足够的00模穿越峰":
                    self.missing_count += 1
                    if self.missing_count < 2:
                        return self._action(
                            "none", None,
                            "启动幅度未找到00模，等待第二个独立窗口复核 1/2",
                        )
                    self.missing_count = 0
                    return self._startup_offset_search_action()
                if stage.shrink_ratio is None:
                    return self._startup_offset_search_action()
                return self._action("none", None, observation.reason)
            self.fingerprint = CarrierFingerprint(
                observation.prominence, observation.width_seconds,
                observation.polarity,
            )
            if stage.shrink_ratio is None:
                if observation.balance_error <= s.balance_tolerance:
                    return self._begin_final_acceptance(observation)
                return self._begin_final_local_search(observation)
            ready_tolerance = stage.balance_tolerance
            if observation.balance_error > ready_tolerance:
                return self._begin_centering(observation)
            # A safely centered initial window may enter the stage
            # confirmation directly; a blind direction probe is unnecessary.
            self.previous_error = observation.balance_error
            self.previous_offset = self.current_offset
            self.stable_count = 0
            self.state = "center"

        if not observation.valid:
            if self.state in final_states:
                return self._handle_invalid_final_window(observation.reason)
            if (self.state == "startup_offset_search"
                    and observation.reason == "未找到足够的00模穿越峰"):
                return self._startup_offset_search_action()
            if self.state in model_states:
                retry = self._retry_full_prediction(
                    f"预测位置峰无效（{observation.reason}）"
                )
                if retry is not None:
                    return retry
                if self.best_observation is not None:
                    return self._begin_legacy_centering(
                        self.best_observation,
                        f"模型阶段峰无效（{observation.reason}），进入旧搜索",
                    )
                return self._recovery_action(observation.reason)
            if self.state in {
                "verify_shrink", "center", "probe", "track",
                "boundary_recover",
            }:
                self.recovery_attempt = 0
                self.recovery_origin = self.current_offset
                self.fail_amplitude = (
                    self.current_amplitude
                    if self.state == "verify_shrink" else self.fail_amplitude
                )
                return self._recovery_action(observation.reason)
            if self.state == "local_recover":
                return self._recovery_action(observation.reason)
            if self.state == "refine":
                self.fail_amplitude = self.current_amplitude
                target = max(self.last_good_amplitude, self.current_amplitude)
                return self._action(
                    "amplitude", target,
                    "二分试验幅度不可靠，恢复上一个可靠Amplitude",
                    "restore_amplitude",
                )
            if self.state == "restore_amplitude":
                if self.current_amplitude < self.search_amplitude_ceiling * 0.999:
                    target = min(
                        self.search_amplitude_ceiling,
                        max(self.last_good_amplitude, self.current_amplitude * 1.5),
                    )
                    return self._action(
                        "amplitude", target,
                        "恢复幅度后仍未找到00模，继续扩大Amplitude",
                        "restore_amplitude",
                    )
                return self._action(
                    "stop", None, "全范围无法唯一找回00模", "fault"
                )
            return self._action("none", None, observation.reason)

        if self.fingerprint is not None:
            self.fingerprint.update(observation)

        if self.state == "boundary_recover":
            # The safety handler has restored the best known Offset. Resume
            # normal evaluation instead of remaining in an unhandled state.
            self._clear_trial()
            self.stable_count = 0
            self.state = "center"

        if self.state == "search_direction_probe":
            return self._handle_direction_probe(observation)

        if self.state in {"search_verify", "search_model_correct"}:
            return self._handle_model_verify(observation)

        if self.state == "search_accept":
            if observation.balance_error <= s.search_tolerance:
                return self._search_acceptance(observation)
            self.stable_count = 0
            if self.physical_direction is not None:
                return self._handle_model_verify(observation)
            return self._begin_centering(observation)

        if self.state == "final_verify":
            if observation.balance_error <= s.balance_tolerance:
                return self._begin_final_acceptance(observation)
            return self._begin_final_local_search(
                observation,
                reason=(
                    f"一步缩幅后不均匀度={observation.balance_error * 100:.2f}%"
                ),
            )

        if self.state == "final_local_search":
            return self._handle_final_local_search(observation)

        if self.state == "final_local_return":
            if observation.balance_error <= s.balance_tolerance:
                return self._begin_final_acceptance(observation)
            return self._action(
                "stop", None,
                f"恢复最佳Offset后的不均匀度={observation.balance_error * 100:.2f}%"
                "，未达到最终验收门槛",
                "fault",
            )

        if self.state == "final_accept":
            if observation.balance_error <= s.balance_tolerance:
                self.stable_count += 1
                if self.stable_count >= s.stable_windows:
                    self.finalized = True
                    return self._action(
                        "none", None,
                        f"最终验收连续{s.stable_windows}个独立窗口通过，允许FALC接管",
                        "track",
                    )
                return self._action(
                    "none", None,
                    f"最终验收 {self.stable_count}/{s.stable_windows}",
                )
            self.stable_count = 0
            if not self.local_search_completed:
                return self._begin_final_local_search(observation)
            return self._action(
                "stop", None, "最终验收超差，未允许FALC接管", "fault"
            )

        if self.state == "legacy_restore":
            return self._begin_legacy_centering(
                observation, "已恢复大扫幅，使用旧算法慢速搜索"
            )

        if self.state == "probe":
            reference = self.trial_origin_error
            if reference is None:
                reference = self.previous_error or observation.balance_error
            margin = self._decision_margin(reference)
            if observation.balance_error > reference + margin:
                return self._reverse_from_best("Offset试探使不均匀度变差")
            if observation.balance_error >= reference - margin:
                self.neutral_count += 1
                if self.neutral_count < 2:
                    return self._action(
                        "none", None,
                        f"Offset试探落在判定死区；当前={observation.balance_error * 100:.2f}% "
                        f"参考={reference * 100:.2f}%，等待第二个独立窗口",
                    )
                return self._reverse_from_best("Offset试探连续两次没有明确改善")
            self.direction = self.trial_direction
            self.previous_error = observation.balance_error
            self.previous_offset = self.current_offset
            self._remember_best(observation)
            self._clear_trial()
            self.state = "center"

        if self.state in {"center", "track"}:
            ready_tolerance = stage.balance_tolerance
            if observation.balance_error <= ready_tolerance:
                self.stable_count += 1
                self.bad_track_count = 0
                if self.stable_count < stage.stable_windows:
                    return self._action(
                        "none", None,
                        f"{stage.name}峰间隔确认 "
                        f"{self.stable_count}/{stage.stable_windows}",
                    )
                self.stable_count = 0
                if stage.shrink_ratio is None:
                    self.finalized = True
                    return self._action(
                        "none", None,
                        "最终幅度与峰间隔连续通过，允许FALC接管", "track",
                    )
                self.last_good_amplitude = self.current_amplitude
                target = self.amplitude_floor
                if target >= self.current_amplitude * 0.999:
                    self.finalized = True
                    return self._action(
                        "none", None,
                        "达到最终Scan Amplitude目标并通过峰间隔复核", "track",
                    )
                return self._action(
                    "amplitude", target,
                    "快速寻峰已居中，Scan Amplitude一步缩到最终目标",
                    "final_shrink",
                )
            self.stable_count = 0
            if self.state == "track":
                self.bad_track_count += 1
                if self.bad_track_count < 2:
                    return self._action("none", None, "保持状态首次超差，等待复核")
                # A drifting cavity makes an old all-time optimum physically
                # obsolete. Start a new local experiment at the present point.
                self.best_offset = self.current_offset
                self.best_error = observation.balance_error
                self.best_observation = observation
                self.boundary_directions.clear()
                self._clear_trial()
            if self.trial_origin_error is not None:
                reference = self.trial_origin_error
                margin = self._decision_margin(reference)
                if observation.balance_error > reference + margin:
                    return self._reverse_from_best("Offset连续调节使不均匀度变差")
                if observation.balance_error >= reference - margin:
                    self.neutral_count += 1
                    if self.neutral_count < 2:
                        return self._action(
                            "none", None,
                            f"不均匀度变化位于死区；当前={observation.balance_error * 100:.2f}% "
                            f"参考={reference * 100:.2f}%，等待复核",
                        )
                    return self._reverse_from_best("连续两次没有明确改善")
            self._remember_best(observation)
            self.previous_error = observation.balance_error
            self.previous_offset = self.current_offset
            return self._start_trial(
                observation, self.direction, self.step_size,
                "修正00模峰间隔不均匀", "center",
            )

        if self.state == "verify_shrink":
            self.last_good_amplitude = self.current_amplitude
            self.previous_error = observation.balance_error
            return self._begin_centering(observation)

        if self.state == "local_recover":
            self.recovery_origin = None
            self.previous_error = observation.balance_error
            return self._begin_centering(observation)

        if self.state == "restore_amplitude":
            if self.fail_amplitude is None:
                return self._begin_centering(observation)
            return self._refine_action()

        if self.state == "refine":
            self.last_good_amplitude = self.current_amplitude
            return self._refine_action()

        return self._action("none", None, "等待下一分析窗口")

    def _recovery_action(self, reason: str) -> ControlAction:
        if self.recovery_origin is None:
            self.recovery_origin = self.current_offset
        self.recovery_attempt += 1
        if self.recovery_attempt <= 4:
            magnitude = (self.recovery_attempt + 1) // 2
            sign = 1.0 if self.recovery_attempt % 2 else -1.0
            probe = max(
                self.settings.min_offset_step,
                self.current_amplitude * 0.05,
            )
            # Every target is relative to the last valid offset.  Clamp the
            # local search to the current narrow scan window as well as the
            # hard start-offset limits applied by _offset_action().
            local_half_span = max(probe, self.current_amplitude * 0.5)
            target = self.recovery_origin + sign * magnitude * probe
            target = min(
                self.recovery_origin + local_half_span,
                max(self.recovery_origin - local_half_span, target),
            )
            return self._offset_action(
                target,
                f"{reason}；在当前小幅度下左右试探Offset",
                "local_recover",
            )
        self.recovery_origin = None
        target = min(self.search_amplitude_ceiling, max(
            self.last_good_amplitude, self.current_amplitude * 1.5
        ))
        if target > self.current_amplitude * 1.001:
            self.refine_attempt = 0
            return self._action(
                "amplitude", target,
                "小范围Offset试探失败，恢复可靠Scan Amplitude",
                "restore_amplitude",
            )
        return self._action("stop", None, "无法找回00模", "fault")

    def _refine_action(self) -> ControlAction:
        if self.fail_amplitude is None:
            return self._action("none", None, "最小可靠幅度无需二分", "track")
        self.refine_attempt += 1
        good = self.last_good_amplitude
        fail = self.fail_amplitude
        if self.refine_attempt > 4 or abs(good - fail) <= good * 0.05:
            operating = max(
                self.amplitude_floor,
                min(good, fail * (1.0 + self.settings.safety_margin)),
            )
            if abs(operating - self.current_amplitude) <= 1e-12:
                return self._action("none", None, "进入最小可靠幅度保持", "track")
            return self._action(
                "amplitude", operating, "应用最小可靠幅度安全裕量", "track"
            )
        trial = max(self.amplitude_floor, (good + fail) / 2.0)
        return self._action(
            "amplitude", trial, "二分验证最小可靠Scan Amplitude", "refine"
        )
