"""Raw-ADC 00-mode selection and two-stage Scan Offset control policy.

The device-facing constraints (triangle scan, PC Voltage output and physical
voltage limits) come from the DLC pro operating model.  Peak-family selection,
triangle-geometry centering and the state machine are project algorithms.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
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
    next_amplitude: float | None
    stable_windows: int


@dataclass(slots=True)
class PeakBalanceSettings:
    """The 21 user-visible parameters used by the current algorithm."""

    channel: str = "A"
    polarity: Polarity = "auto"
    min_prominence_codes: float = 50.0
    noise_sigma: float = 6.0
    main_family_ratio: float = 5.0
    period_tolerance: float = 0.10
    narrow_main_height_ratio: float = 0.05
    invalid_retry_windows: int = 3

    search_frequency_hz: float = 10.0
    initial_search_amplitude: float = 2.5
    initial_offset_search_step: float = 1.0
    wide_probe_step: float = 0.05
    wide_shrink_tolerance: float = 0.08
    wide_confirm_windows: int = 2
    wide_model_corrections: int = 2

    final_amplitude: float = 0.2
    final_coarse_step: float = 0.01
    final_fine_step: float = 0.001
    final_max_offset_deviation: float = 0.09
    final_balance_tolerance: float = 0.05
    falc_confirm_windows: int = 3

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def validated(self) -> "PeakBalanceSettings":
        values = self.as_dict()
        values["channel"] = str(values["channel"]).upper()
        result = PeakBalanceSettings(**values)
        if result.channel not in {"A", "B"}:
            raise ValueError("透射峰通道必须是A或B")
        if result.polarity not in {"auto", "positive", "negative"}:
            raise ValueError("峰极性无效")
        if not 0 <= result.min_prominence_codes <= 32767:
            raise ValueError("最小峰突出度必须位于0到32767 ADC码")
        if not 1.0 <= result.noise_sigma <= 30.0:
            raise ValueError("噪声门槛倍数必须位于1到30之间")
        if result.main_family_ratio <= 1.0:
            raise ValueError("主峰族最小强度比必须大于1")
        if not 0.001 <= result.period_tolerance < 0.5:
            raise ValueError("峰周期允许误差必须位于0.1%到50%之间")
        if not 0.0 < result.narrow_main_height_ratio <= 1.0:
            raise ValueError("窄扫主峰最低保留比例必须位于0到100%之间")
        if not 1 <= int(result.invalid_retry_windows) <= 10:
            raise ValueError("无效窗口原地重采次数必须位于1到10之间")
        if not 0.01 <= result.search_frequency_hz <= 1000.0:
            raise ValueError("快速扫频频率必须位于0.01到1000 Hz之间")
        if result.initial_search_amplitude <= 0 or result.final_amplitude <= 0:
            raise ValueError("初始化与最终Scan Amplitude必须大于0")
        if result.final_amplitude > result.initial_search_amplitude:
            raise ValueError("最终Scan Amplitude不能大于初始化Scan Amplitude")
        if result.initial_offset_search_step <= 0 or result.wide_probe_step <= 0:
            raise ValueError("初始化无峰步长和宽扫方向试探步长必须大于0")
        if result.final_coarse_step <= 0 or result.final_fine_step <= 0:
            raise ValueError("最终粗调和精调步长必须大于0")
        if result.final_fine_step > result.final_coarse_step:
            raise ValueError("最终精调步长不能大于最终粗调步长")
        if result.final_max_offset_deviation < result.final_coarse_step:
            raise ValueError("最终最大Offset偏移不能小于最终粗调步长")
        for value, label in (
            (result.wide_shrink_tolerance, "宽扫缩幅门槛"),
            (result.final_balance_tolerance, "最终锁定不均匀度门槛"),
        ):
            if not 0.0 < value < 0.5:
                raise ValueError(f"{label}必须位于0到50%之间")
        if not 1 <= int(result.wide_confirm_windows) <= 10:
            raise ValueError("宽扫缩幅确认窗口必须位于1到10之间")
        if not 0 <= int(result.wide_model_corrections) <= 10:
            raise ValueError("宽扫理论残差修正次数必须位于0到10之间")
        if not 1 <= int(result.falc_confirm_windows) <= 10:
            raise ValueError("自动FALC确认窗口必须位于1到10之间")
        return result

    def stage_for(self, amplitude: float, amplitude_floor: float) -> AmplitudeStage:
        amplitude = abs(float(amplitude))
        if amplitude <= amplitude_floor * 1.001:
            return AmplitudeStage(
                "最终锁定", self.final_balance_tolerance,
                self.final_fine_step, self.final_fine_step, None,
                self.falc_confirm_windows,
            )
        return AmplitudeStage(
            "宽扫寻峰", self.wide_shrink_tolerance,
            self.wide_probe_step, self.final_fine_step,
            amplitude_floor,
            self.wide_confirm_windows,
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
    reason_code: str = ""
    polarity: str = "positive"
    baseline: float = 0.0
    noise: float = 0.0
    threshold: float = 0.0
    peak_times: tuple[float, ...] = ()
    peak_count: int = 0
    family_count: int = 0
    prominence: float = 0.0
    second_prominence: float = 0.0
    dominance_ratio: float = 0.0
    width_seconds: float = 0.0
    snr: float = 0.0
    delta_t1: float = 0.0
    delta_t2: float = 0.0
    expected_period: float = 0.0
    measured_period: float = 0.0
    period_error: float = 0.0
    signed_error: float = 0.0
    balance_error: float = 1.0
    reference_height_ratio: float = 0.0

    @property
    def ambiguous(self) -> bool:
        return self.reason_code == "FAMILY_UNCERTAIN" or self.reason == "00模候选不唯一"


@dataclass(slots=True)
class ControlAction:
    kind: Literal["none", "offset", "amplitude", "stop"]
    value: float | None
    reason: str
    state: str
    reason_code: str = ""


@dataclass(slots=True)
class _PeakFamily:
    peaks: tuple[tuple[int, float, float], ...]
    prominence: float
    width_seconds: float
    delta_t1: float
    delta_t2: float
    measured_period: float
    period_error: float
    signed_error: float
    phase_pair: tuple[float, float]


def _robust_noise(values: np.ndarray) -> tuple[float, float]:
    cutoff = float(np.percentile(values, 20.0))
    floor = values[values <= cutoff]
    baseline = float(np.median(floor))
    noise = float(np.median(np.abs(floor - baseline)) * 1.4826)
    return baseline, noise


def _peak_groups(values: np.ndarray, valid: np.ndarray, threshold: float,
                 bin_seconds: float, min_distance_bins: int):
    if values.size < 3:
        return []
    # A broad resonance often contains many equal-height/noisy local maxima.
    # Treat one contiguous threshold excursion as one physical crossing, then
    # keep its strongest sample.  This removes the former repeated-maximum
    # ambiguity without using peak width as a hard identity fingerprint.
    mask = valid & (values >= threshold)
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    candidates = []
    for start, stop in zip(starts, stops):
        if stop - start < 1:
            continue
        candidates.append(int(start + np.argmax(values[start:stop])))
    candidates = np.asarray(candidates, dtype=np.int64)
    if not candidates.size:
        return []
    selected: list[int] = []
    for index in candidates[np.argsort(values[candidates])[::-1]]:
        index = int(index)
        if all(abs(index - previous) >= min_distance_bins for previous in selected):
            selected.append(index)
    peaks = []
    for index in sorted(selected):
        half_height = threshold + 0.5 * (float(values[index]) - threshold)
        start = index
        while start > 0 and valid[start - 1] and values[start - 1] >= half_height:
            start -= 1
        stop = index + 1
        while stop < values.size and valid[stop] and values[stop] >= half_height:
            stop += 1
        peaks.append((index, float(values[index]), max(1, stop - start) * bin_seconds))
    return peaks


def _phase_distance(left: float, right: float, period: float) -> float:
    distance = abs(left - right)
    return min(distance, period - distance)


def _build_families(peaks, baseline: float, period: float,
                    bin_seconds: float) -> list[_PeakFamily]:
    """Build repeated forward/reverse crossing families from four peaks.

    A family must contain two occurrences of each triangle-scan crossing.  The
    broad 35% recurrence allowance lets the caller report a quantitative
    PERIOD_MISMATCH instead of degrading it into a false NO_PEAK.
    """
    raw: list[_PeakFamily] = []
    for chosen in combinations(peaks, 4):
        ordered = tuple(sorted(chosen, key=lambda item: item[0]))
        times = np.asarray([p[0] * bin_seconds for p in ordered])
        recur = np.asarray([times[2] - times[0], times[3] - times[1]])
        if np.any(recur <= 0):
            continue
        measured_period = float(np.median(recur))
        period_error = abs(measured_period - period) / max(period, 1e-12)
        if period_error > 0.35:
            continue
        intervals = np.diff(times)
        if np.any(intervals < 0.02 * period):
            continue
        delta1 = float(np.median([intervals[0], intervals[2]]))
        delta2 = float(intervals[1])
        if abs((delta1 + delta2) - measured_period) / max(period, 1e-12) > 0.20:
            continue
        prominences = np.asarray([p[1] - baseline for p in ordered])
        if float(np.min(prominences)) < 0.20 * float(np.max(prominences)):
            continue
        phase_pair = tuple(sorted((times[0] % period, times[1] % period)))
        signed = (delta1 - delta2) / max(measured_period, 1e-12)
        raw.append(_PeakFamily(
            peaks=ordered,
            prominence=float(np.median(prominences)),
            width_seconds=float(np.median([p[2] for p in ordered])),
            delta_t1=delta1,
            delta_t2=delta2,
            measured_period=measured_period,
            period_error=period_error,
            signed_error=signed,
            phase_pair=(float(phase_pair[0]), float(phase_pair[1])),
        ))
    # Five edge crossings can generate two four-peak combinations for the same
    # physical line.  Deduplicate by the two scan phases, not by rank.
    families: list[_PeakFamily] = []
    for candidate in sorted(raw, key=lambda item: (item.period_error, -item.prominence)):
        duplicate = False
        for previous in families:
            direct = (
                _phase_distance(candidate.phase_pair[0], previous.phase_pair[0], period)
                + _phase_distance(candidate.phase_pair[1], previous.phase_pair[1], period)
            )
            crossed = (
                _phase_distance(candidate.phase_pair[0], previous.phase_pair[1], period)
                + _phase_distance(candidate.phase_pair[1], previous.phase_pair[0], period)
            )
            if min(direct, crossed) <= 0.08 * period:
                duplicate = True
                if candidate.prominence > previous.prominence:
                    families[families.index(previous)] = candidate
                break
        if not duplicate:
            families.append(candidate)
    return families


def analyze_carrier(history, settings: PeakBalanceSettings,
                    scan_frequency: float,
                    fingerprint: CarrierFingerprint | None = None,
                    after_bin: int | None = None) -> PeakObservation:
    settings = settings.validated()
    if scan_frequency <= 0:
        return PeakObservation(False, "扫描频率无效", "INVALID_FREQUENCY")
    period = 1.0 / float(scan_frequency)
    indices = np.asarray(history.bin_indices, dtype=np.int64)
    valid = np.asarray(history.valid, dtype=bool)
    keep = indices > int(after_bin) if after_bin is not None else np.ones(indices.size, dtype=bool)
    indices, valid = indices[keep], valid[keep]
    required_bins = max(16, int(round(2.0 * period / history.bin_seconds)))
    if indices.size < required_bins:
        return PeakObservation(
            False, "等待足够的扫描周期", "WAITING",
            expected_period=period,
        )
    # Exactly two periods: timer jitter must not add a fifth carrier crossing.
    indices, valid = indices[:required_bins], valid[:required_bins]
    if not np.all(valid) or np.any(np.diff(indices) != 1):
        return PeakObservation(
            False, "分析窗口存在ADC索引空洞", "DATA_GAP",
            expected_period=period,
        )
    source_keep = np.flatnonzero(keep)[:required_bins]
    if settings.channel == "A":
        minimum = np.asarray(history.minimum_a)[source_keep].astype(np.float64)
        maximum = np.asarray(history.maximum_a)[source_keep].astype(np.float64)
    else:
        minimum = np.asarray(history.minimum_b)[source_keep].astype(np.float64)
        maximum = np.asarray(history.maximum_b)[source_keep].astype(np.float64)
    positive_baseline, positive_noise = _robust_noise(maximum)
    negative_values = -minimum
    negative_baseline, negative_noise = _robust_noise(negative_values)
    polarity = settings.polarity
    if polarity == "auto":
        positive_score = float(np.max(maximum) - positive_baseline)
        negative_score = float(np.max(negative_values) - negative_baseline)
        polarity = "positive" if positive_score >= negative_score else "negative"
    if polarity == "positive":
        values, baseline, noise = maximum, positive_baseline, positive_noise
    else:
        values, baseline, noise = negative_values, negative_baseline, negative_noise
    threshold = max(settings.min_prominence_codes, settings.noise_sigma * max(noise, 1e-9))
    min_distance = max(1, int(round(0.04 * period / history.bin_seconds)))
    peaks = _peak_groups(
        values, valid, baseline + threshold,
        float(history.bin_seconds), min_distance,
    )
    if len(peaks) < 4:
        strongest = max((p[1] - baseline for p in peaks), default=0.0)
        return PeakObservation(
            False, "未找到足够的00模穿越峰", "NO_PEAK",
            polarity=polarity, baseline=baseline, noise=noise,
            threshold=threshold, peak_count=len(peaks), prominence=strongest,
            expected_period=period,
        )
    families = _build_families(peaks, baseline, period, float(history.bin_seconds))
    if not families:
        return PeakObservation(
            False, "主峰族周期结构不完整", "PERIOD_MISMATCH",
            polarity=polarity, baseline=baseline, noise=noise,
            threshold=threshold, peak_count=len(peaks), expected_period=period,
        )
    families.sort(key=lambda item: item.prominence, reverse=True)
    main = families[0]
    second = families[1].prominence if len(families) > 1 else 0.0
    ratio = main.prominence / max(second, noise, 1e-9)
    common = dict(
        polarity=polarity, baseline=baseline, noise=noise, threshold=threshold,
        peak_times=tuple(p[0] * float(history.bin_seconds) for p in main.peaks),
        peak_count=len(peaks), family_count=len(families),
        prominence=main.prominence, second_prominence=second,
        dominance_ratio=ratio, width_seconds=main.width_seconds,
        snr=main.prominence / max(noise, 1e-9),
        delta_t1=main.delta_t1, delta_t2=main.delta_t2,
        expected_period=period, measured_period=main.measured_period,
        period_error=main.period_error, signed_error=main.signed_error,
        balance_error=abs(main.signed_error),
    )
    if len(families) > 1 and ratio < settings.main_family_ratio:
        return PeakObservation(False, "主峰族强度优势不足", "FAMILY_UNCERTAIN", **common)
    if main.period_error > settings.period_tolerance:
        return PeakObservation(False, "峰周期与DLC pro扫描频率不一致", "PERIOD_MISMATCH", **common)
    height_ratio = 0.0
    if fingerprint is not None:
        height_ratio = main.prominence / max(fingerprint.prominence, 1e-9)
        if height_ratio < settings.narrow_main_height_ratio:
            return PeakObservation(
                False, "当前主峰高度低于宽扫参考", "REFERENCE_TOO_WEAK",
                reference_height_ratio=height_ratio, **common,
            )
    return PeakObservation(
        True, "00模主峰族有效", "VALID",
        reference_height_ratio=height_ratio, **common,
    )


class PeakBalanceEngine:
    """Two-stage controller: wide theoretical jump, final directional climb."""

    def __init__(self, settings: PeakBalanceSettings):
        self.settings = settings.validated()
        self.state = "idle"
        self.start_offset = self.current_offset = 0.0
        self.start_amplitude = self.current_amplitude = 0.0
        self.previous_amplitude = 0.0
        self.last_good_amplitude = 0.0
        self.fingerprint: CarrierFingerprint | None = None
        self.previous_error: float | None = None
        self.previous_offset = 0.0
        self.direction = 1.0
        self.step_size = self.settings.wide_probe_step
        self.stable_count = 0
        self.bad_track_count = 0
        self.finalized = False
        self.invalid_count = 0
        self.missing_count = 0
        self.startup_search_attempt = 0
        self.trial_origin_error: float | None = None
        self.trial_origin_offset: float | None = None
        self.origin_signed_error = 0.0
        self.plus_probe_error: float | None = None
        self.neutral_count = 0
        self.physical_direction = 1.0
        self.model_reference_error: float | None = None
        self.model_correction_count = 0
        self.final_origin_offset: float | None = None
        self.best_offset = 0.0
        self.best_error: float | None = None
        self.final_reversed = False
        self.final_candidates: list[float] = []

    @property
    def amplitude_floor(self) -> float:
        return self.settings.final_amplitude

    @property
    def current_stage(self) -> AmplitudeStage:
        return self.settings.stage_for(self.current_amplitude, self.amplitude_floor)

    @property
    def offset_limits(self) -> tuple[float, float]:
        low = PC_VOLTAGE_MIN + 0.5 * self.current_amplitude
        high = PC_VOLTAGE_MAX - 0.5 * self.current_amplitude
        if self.current_amplitude <= self.amplitude_floor * 1.001:
            origin = self.final_origin_offset
            if origin is not None:
                span = self.settings.final_max_offset_deviation
                low, high = max(low, origin - span), min(high, origin + span)
        return low, high

    def start(self, offset: float, amplitude: float) -> None:
        self.start_offset = self.current_offset = float(offset)
        self.start_amplitude = self.current_amplitude = abs(float(amplitude))
        if self.settings.final_amplitude > self.start_amplitude + 1e-12:
            raise ValueError("最终Scan Amplitude不能大于启动Amplitude")
        self.previous_amplitude = self.current_amplitude
        self.last_good_amplitude = self.current_amplitude
        self.previous_offset = self.current_offset
        self.best_offset = self.current_offset
        self.final_origin_offset = (
            self.current_offset
            if self.current_amplitude <= self.amplitude_floor * 1.001 else None
        )
        self.step_size = (
            self.settings.final_fine_step
            if self.final_origin_offset is not None else self.settings.wide_probe_step
        )
        self.state = "select"

    def sync(self, offset: float, amplitude: float) -> None:
        self.previous_amplitude = self.current_amplitude
        self.current_offset = float(offset)
        self.current_amplitude = abs(float(amplitude))

    def reset_after_amplitude_change(self) -> None:
        self.invalid_count = self.missing_count = self.stable_count = 0
        self.previous_error = None
        self.finalized = False
        if self.current_amplitude <= self.amplitude_floor * 1.001:
            self.final_origin_offset = self.current_offset
            self.best_offset = self.current_offset
            self.best_error = None
            self.step_size = self.settings.final_fine_step
            self.state = "select"

    def reset_direction_experiment(self) -> None:
        self.previous_error = None
        self.previous_offset = self.current_offset
        self.neutral_count = 0

    def set_offset_step(self, step: float) -> bool:
        changed = abs(self.step_size - float(step)) > 1e-12
        self.step_size = float(step)
        return changed

    @staticmethod
    def theoretical_distance(amplitude: float, balance_error: float) -> float:
        return 0.5 * abs(float(amplitude)) * abs(float(balance_error))

    @staticmethod
    def _decision_margin(reference_error: float) -> float:
        return max(0.005, abs(float(reference_error)) * 0.05)

    def _action(self, kind, value, reason, state=None, code="") -> ControlAction:
        self.state = state or self.state
        return ControlAction(kind, value, reason, self.state, code)

    def _offset_action(self, target: float, reason: str, state: str) -> ControlAction:
        low, high = self.offset_limits
        target = min(high, max(low, float(target)))
        if abs(target - self.current_offset) < 1e-12:
            return self._action("stop", None, "Offset已到安全边界，无法继续调节", "fault", "BOUNDARY")
        return self._action("offset", target, reason, state)

    def _startup_search(self) -> ControlAction:
        step = self.settings.initial_offset_search_step
        low = PC_VOLTAGE_MIN + 0.5 * self.current_amplitude
        high = PC_VOLTAGE_MAX - 0.5 * self.current_amplitude
        maximum_index = int(np.ceil(max(
            self.start_offset - low, high - self.start_offset
        ) / step - 1e-12))
        while self.startup_search_attempt < 2 * maximum_index:
            index = self.startup_search_attempt // 2 + 1
            sign = 1.0 if self.startup_search_attempt % 2 == 0 else -1.0
            self.startup_search_attempt += 1
            target = self.start_offset + sign * index * step
            if low <= target <= high:
                return self._action(
                    "offset", target,
                    f"初始化无主峰，保持Amplitude并搜索Offset {sign * index * step:+.6f} V",
                    "startup_offset_search", "NO_PEAK_SEARCH",
                )
        return self._action(
            "stop", None, "PC Voltage物理范围内仍未找到主峰", "fault", "NO_PEAK",
        )

    def _final_reacquire_candidates(self) -> list[float]:
        origin = self.final_origin_offset if self.final_origin_offset is not None else self.current_offset
        step = self.settings.final_coarse_step
        count = int(self.settings.final_max_offset_deviation / step + 1e-9)
        low = PC_VOLTAGE_MIN + 0.5 * self.current_amplitude
        high = PC_VOLTAGE_MAX - 0.5 * self.current_amplitude
        result = []
        for index in range(1, count + 1):
            for sign in (1.0, -1.0):
                value = origin + sign * index * step
                if low <= value <= high:
                    result.append(value)
        return result

    def _advance_reacquire(self) -> ControlAction:
        if not self.final_candidates:
            self.final_candidates = self._final_reacquire_candidates()
        if not self.final_candidates:
            return self._action("stop", None, "最终范围内没有可用Offset", "fault", "NO_PEAK")
        target = self.final_candidates.pop(0)
        return self._action(
            "offset", target, "连续无主峰，按最终粗调步长左右重新捕获",
            "final_reacquire", "NO_PEAK_SEARCH",
        )

    def _begin_wide_probe(self, observation: PeakObservation) -> ControlAction:
        self.trial_origin_offset = self.current_offset
        self.trial_origin_error = observation.balance_error
        self.origin_signed_error = observation.signed_error
        self.plus_probe_error = None
        self.neutral_count = 0
        self.step_size = self.settings.wide_probe_step
        return self._offset_action(
            self.current_offset + self.step_size,
            "宽扫超差，执行一次正向方向试探", "wide_probe",
        )

    def _wide_target(self, origin: float, direction: float,
                     error: float, state: str, reason: str) -> ControlAction:
        distance = self.theoretical_distance(self.current_amplitude, error)
        self.physical_direction = direction
        self.model_reference_error = error
        return self._offset_action(origin + direction * distance, reason, state)

    def _begin_wide_confirm(self, observation: PeakObservation) -> ControlAction:
        self.stable_count = 1
        self.previous_error = observation.balance_error
        if self.stable_count >= self.settings.wide_confirm_windows:
            self.last_good_amplitude = self.current_amplitude
            return self._action(
                "amplitude", self.amplitude_floor,
                "宽扫门槛通过，Scan Amplitude直接缩到最终目标",
                "final_shrink", "WIDE_ACCEPT",
            )
        return self._action(
            "none", None,
            f"宽扫缩幅确认 {self.stable_count}/{self.settings.wide_confirm_windows}",
            "wide_confirm", "WIDE_CONFIRM",
        )

    def _accept_final(self, observation: PeakObservation) -> ControlAction:
        self.stable_count += 1
        self.previous_error = observation.balance_error
        if self.stable_count >= self.settings.falc_confirm_windows:
            self.finalized = True
            return self._action(
                "none", None,
                f"最终连续{self.settings.falc_confirm_windows}个窗口通过",
                "track", "FINAL_ACCEPT",
            )
        return self._action(
            "none", None,
            f"最终FALC确认 {self.stable_count}/{self.settings.falc_confirm_windows}",
            "final_confirm", "FINAL_CONFIRM",
        )

    def _final_step_for(self, observation: PeakObservation) -> float:
        coarse_effect = 2.0 * self.settings.final_coarse_step / max(self.current_amplitude, 1e-12)
        excess = observation.balance_error - self.settings.final_balance_tolerance
        return (
            self.settings.final_coarse_step
            if excess > 0.5 * coarse_effect else self.settings.final_fine_step
        )

    def _begin_final_adjust(self, observation: PeakObservation) -> ControlAction:
        if self.final_origin_offset is None:
            self.final_origin_offset = self.current_offset
        self.best_offset = self.current_offset
        self.best_error = observation.balance_error
        self.previous_error = observation.balance_error
        self.previous_offset = self.current_offset
        self.direction = 1.0
        self.step_size = self._final_step_for(observation)
        self.final_reversed = False
        self.neutral_count = 0
        return self._offset_action(
            self.current_offset + self.step_size,
            f"最终定向调节，步长={self.step_size:.6f} V", "final_adjust",
        )

    def _handle_final_adjust(self, observation: PeakObservation) -> ControlAction:
        if observation.balance_error <= self.settings.final_balance_tolerance:
            return self._accept_final(observation)
        if self.best_error is None or observation.balance_error < self.best_error:
            self.best_error = observation.balance_error
            self.best_offset = self.current_offset
        previous = self.previous_error if self.previous_error is not None else observation.balance_error
        moved = self.current_offset - self.previous_offset
        moved_direction = 1.0 if moved >= 0 else -1.0
        margin = self._decision_margin(previous)
        if observation.balance_error < previous - margin:
            self.direction = moved_direction
            self.neutral_count = 0
            target = self.current_offset + self.direction * self.step_size
        elif observation.balance_error >= previous + margin:
            if self.step_size > self.settings.final_fine_step * 1.001:
                self.step_size = self.settings.final_fine_step
                self.direction = -moved_direction
                self.final_reversed = False
                target = self.best_offset + self.direction * self.step_size
            elif not self.final_reversed:
                self.direction = -moved_direction
                self.final_reversed = True
                target = self.best_offset + self.direction * self.step_size
            else:
                if abs(self.current_offset - self.best_offset) > 1e-12:
                    return self._offset_action(
                        self.best_offset, "两个精调方向均未改善，恢复最佳Offset",
                        "final_return",
                    )
                return self._action(
                    "stop", None, "最终两个精调方向均未达到门槛",
                    "fault", "FINAL_NOT_CONVERGED",
                )
        else:
            self.neutral_count += 1
            if self.neutral_count < 2:
                return self._action(
                    "none", None, "最终调节变化落在死区，原地复测",
                    "final_adjust", "RETRY_SAME_OFFSET",
                )
            self.neutral_count = 0
            self.step_size = self.settings.final_fine_step
            self.direction = -moved_direction
            target = self.best_offset + self.direction * self.step_size
        self.previous_error = observation.balance_error
        self.previous_offset = self.current_offset
        action = self._offset_action(target, "按不均匀度趋势继续最终定向调节", "final_adjust")
        if action.kind == "stop" and not self.final_reversed:
            self.final_reversed = True
            self.direction *= -1.0
            return self._offset_action(
                self.best_offset + self.direction * self.settings.final_fine_step,
                "触及最终范围边界，恢复最佳点后反向精调", "final_adjust",
            )
        return action

    def _handle_invalid(self, observation: PeakObservation) -> ControlAction:
        if observation.reason_code == "WAITING":
            return self._action("none", None, observation.reason, self.state, observation.reason_code)
        if observation.reason_code == "NO_PEAK" or observation.reason == "未找到足够的00模穿越峰":
            self.invalid_count = 0
            self.missing_count += 1
            final_stage = self.current_amplitude <= self.amplitude_floor * 1.001
            if self.state == "final_reacquire":
                return self._advance_reacquire()
            if self.missing_count < 2:
                return self._action(
                    "none", None, "未找到主峰，原地复核 1/2",
                    self.state, "RETRY_SAME_OFFSET",
                )
            self.missing_count = 0
            return self._advance_reacquire() if final_stage else self._startup_search()
        self.missing_count = 0
        self.invalid_count += 1
        if self.invalid_count <= self.settings.invalid_retry_windows:
            return self._action(
                "none", None,
                f"{observation.reason}，Offset保持不动并原地重采 "
                f"{self.invalid_count}/{self.settings.invalid_retry_windows}",
                self.state, "RETRY_SAME_OFFSET",
            )
        return self._action(
            "stop", None,
            f"{observation.reason}连续超过原地重采次数，停止自动流程",
            "fault", observation.reason_code,
        )

    def update(self, observation: PeakObservation) -> ControlAction:
        if not observation.valid:
            return self._handle_invalid(observation)
        self.invalid_count = self.missing_count = 0
        if self.state == "startup_offset_search":
            self.start_offset = self.current_offset
            self.best_offset = self.current_offset
            self.startup_search_attempt = 0
            self.state = "select"
        if self.fingerprint is None:
            self.fingerprint = CarrierFingerprint(
                observation.prominence, observation.width_seconds,
                observation.polarity,
            )
        elif self.current_amplitude > self.amplitude_floor * 1.001:
            self.fingerprint.update(observation)

        final_stage = self.current_amplitude <= self.amplitude_floor * 1.001
        if self.state == "select":
            if final_stage:
                self.final_origin_offset = self.current_offset
                self.stable_count = 0
                if observation.balance_error <= self.settings.final_balance_tolerance:
                    return self._accept_final(observation)
                return self._begin_final_adjust(observation)
            if observation.balance_error <= self.settings.wide_shrink_tolerance:
                return self._begin_wide_confirm(observation)
            return self._begin_wide_probe(observation)

        if self.state == "wide_probe":
            origin_error = self.trial_origin_error or observation.balance_error
            margin = self._decision_margin(origin_error)
            if observation.balance_error < origin_error - margin:
                direction = 1.0
            elif observation.balance_error > origin_error + margin:
                direction = -1.0
            else:
                self.plus_probe_error = observation.balance_error
                self.neutral_count += 1
                if self.neutral_count < 2:
                    return self._action(
                        "none", None, "正向试探变化落在死区，原地复测",
                        "wide_probe", "RETRY_SAME_OFFSET",
                    )
                return self._offset_action(
                    float(self.trial_origin_offset) - self.settings.wide_probe_step,
                    "正向试探不明确，执行一次负向试探", "wide_probe_negative",
                )
            origin = float(self.trial_origin_offset)
            self.model_correction_count = 0
            return self._wide_target(
                origin, direction, origin_error, "wide_jump",
                "方向已确定，从试探前Offset直接跳转完整理论距离",
            )

        if self.state == "wide_probe_negative":
            origin_error = self.trial_origin_error or observation.balance_error
            margin = self._decision_margin(origin_error)
            if observation.balance_error < origin_error - margin:
                direction = -1.0
            elif self.plus_probe_error is not None and self.plus_probe_error < origin_error - margin:
                direction = 1.0
            else:
                return self._action(
                    "stop", None, "正负方向试探均不能可靠改善不均匀度",
                    "fault", "DIRECTION_UNCERTAIN",
                )
            self.model_correction_count = 0
            return self._wide_target(
                float(self.trial_origin_offset), direction, origin_error,
                "wide_jump", "负向试探完成，直接跳转完整理论距离",
            )

        if self.state in {"wide_jump", "wide_correct"}:
            if observation.balance_error <= self.settings.wide_shrink_tolerance:
                return self._begin_wide_confirm(observation)
            reference = self.model_reference_error or observation.balance_error
            if self.model_correction_count >= self.settings.wide_model_corrections:
                return self._action(
                    "stop", None, "宽扫理论残差修正次数已用完仍未达到门槛",
                    "fault", "WIDE_NOT_CONVERGED",
                )
            margin = self._decision_margin(reference)
            if observation.balance_error >= reference + margin:
                self.physical_direction *= -1.0
            distance = self.theoretical_distance(
                self.current_amplitude, observation.balance_error
            )
            self.model_reference_error = observation.balance_error
            self.model_correction_count += 1
            return self._offset_action(
                self.current_offset + self.physical_direction * distance,
                f"按剩余不均匀度直接修正Offset "
                f"{self.model_correction_count}/{self.settings.wide_model_corrections}",
                "wide_correct",
            )

        if self.state == "wide_confirm":
            if observation.balance_error <= self.settings.wide_shrink_tolerance:
                self.stable_count += 1
                if self.stable_count >= self.settings.wide_confirm_windows:
                    self.last_good_amplitude = self.current_amplitude
                    return self._action(
                        "amplitude", self.amplitude_floor,
                        "宽扫确认通过，直接缩到最终Scan Amplitude",
                        "final_shrink", "WIDE_ACCEPT",
                    )
                return self._action(
                    "none", None,
                    f"宽扫缩幅确认 {self.stable_count}/{self.settings.wide_confirm_windows}",
                    "wide_confirm", "WIDE_CONFIRM",
                )
            self.stable_count = 0
            return self._begin_wide_probe(observation)

        if self.state == "final_reacquire":
            self.final_candidates.clear()
            self.stable_count = 0
            if observation.balance_error <= self.settings.final_balance_tolerance:
                return self._accept_final(observation)
            return self._begin_final_adjust(observation)

        if self.state == "final_adjust":
            return self._handle_final_adjust(observation)

        if self.state == "final_return":
            if observation.balance_error <= self.settings.final_balance_tolerance:
                return self._accept_final(observation)
            return self._action(
                "stop", None, "已恢复最佳Offset但仍未达到最终门槛",
                "fault", "FINAL_NOT_CONVERGED",
            )

        if self.state == "final_confirm":
            if observation.balance_error <= self.settings.final_balance_tolerance:
                return self._accept_final(observation)
            self.stable_count = 0
            return self._begin_final_adjust(observation)

        if self.state == "track":
            return self._action("none", None, "最终锁定已完成", "track", "FINAL_ACCEPT")

        return self._action("none", None, "保持当前参数", self.state)
