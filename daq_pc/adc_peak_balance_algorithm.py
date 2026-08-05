"""Raw-ADC carrier selection and Scan Offset/Amplitude control policy."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np


Polarity = Literal["auto", "positive", "negative"]


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
    offset_step: float = 0.01
    min_offset_step: float = 0.001
    max_offset_deviation: float = 0.2
    shrink_ratio: float = 0.75
    target_amplitude: float = 0.2
    max_search_amplitude_factor: float = 2.0
    min_amplitude_fraction: float = 0.05
    safety_margin: float = 0.25
    balance_tolerance: float = 0.05
    stable_windows: int = 3
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
        if not 1.0 <= self.max_search_amplitude_factor <= 10.0:
            raise ValueError("无峰最大扩幅倍数必须位于1到10之间")
        if self.carrier_dominance_ratio <= 1.0:
            raise ValueError("00模/次峰强度比必须大于1")
        if not 0.0 < self.balance_tolerance < 0.5:
            raise ValueError("峰间隔容差必须位于0到0.5之间")
        if not (self.coarse_boundary > self.medium_boundary
                > self.fine_boundary > self.target_amplitude):
            raise ValueError("阶梯幅度边界必须满足：宽扫>中扫>细扫>最终目标")
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
        if not (self.coarse_step >= self.medium_step >= self.fine_step
                >= self.narrow_step >= self.final_step):
            raise ValueError("Offset步长必须随缩幅阶段逐级减小或保持不变")
        for value in (
            self.coarse_shrink, self.medium_shrink,
            self.fine_shrink, self.narrow_shrink,
        ):
            if not 0.2 <= value < 1.0:
                raise ValueError("各阶段缩幅倍率必须位于0.2到1之间")
        for value in (
            self.coarse_windows, self.medium_windows,
            self.fine_windows, self.narrow_windows, self.stable_windows,
        ):
            if not 1 <= int(value) <= 10:
                raise ValueError("各阶段连续确认窗口必须位于1到10之间")
        return replace(self, channel=channel)

    def stage_for(self, amplitude: float, amplitude_floor: float) -> AmplitudeStage:
        amplitude = abs(float(amplitude))
        if amplitude <= amplitude_floor * 1.001:
            return AmplitudeStage(
                "最终验收", self.balance_tolerance, self.final_step,
                self.min_offset_step, None, self.stable_windows,
            )
        if amplitude > self.coarse_boundary:
            return AmplitudeStage(
                "宽扫", self.coarse_tolerance, self.coarse_step,
                self.medium_step, self.coarse_shrink, self.coarse_windows,
            )
        if amplitude > self.medium_boundary:
            return AmplitudeStage(
                "中扫", self.medium_tolerance, self.medium_step,
                self.fine_step, self.medium_shrink, self.medium_windows,
            )
        if amplitude > self.fine_boundary:
            return AmplitudeStage(
                "细扫", self.fine_tolerance, self.fine_step,
                self.narrow_step, self.fine_shrink, self.fine_windows,
            )
        return AmplitudeStage(
            "窄扫", self.narrow_tolerance, self.narrow_step,
            self.min_offset_step, self.narrow_shrink, self.narrow_windows,
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
    baseline = float(np.median(values))
    noise = float(np.median(np.abs(values - baseline)) * 1.4826)
    return baseline, noise


def _peak_groups(values: np.ndarray, valid: np.ndarray, threshold: float,
                 bin_seconds: float):
    mask = valid & (values >= threshold)
    edges = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    peaks = []
    for start, stop in zip(starts, stops):
        if stop <= start:
            continue
        local = values[start:stop]
        index = int(start + np.argmax(local))
        peaks.append((index, float(values[index]), (stop - start) * bin_seconds))
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
    groups = _peak_groups(
        values, valid, baseline + prominence_threshold,
        float(history.bin_seconds),
    )
    period = 1.0 / float(scan_frequency)
    # Noise can split one broad peak top into two threshold islands. Merge
    # islands that are far too close to be separate scan crossings before
    # comparing the carrier family with sidebands.
    merged = []
    merge_bins = max(1, int(round(0.12 * period / history.bin_seconds)))
    for peak in groups:
        if merged and peak[0] - merged[-1][0] < merge_bins:
            previous = merged[-1]
            stronger = peak if peak[1] > previous[1] else previous
            merged[-1] = (
                stronger[0], stronger[1], previous[2] + peak[2]
            )
        else:
            merged.append(peak)
    groups = merged
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
        if self.settings.target_amplitude > self.start_amplitude + 1e-12:
            raise ValueError("最终扫频范围目标不能大于启动Scan Amplitude")
        self.last_good_amplitude = self.current_amplitude
        self.state = "select"

    def sync(self, offset: float, amplitude: float) -> None:
        self.current_offset = float(offset)
        self.current_amplitude = abs(float(amplitude))

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
        return True

    def _action(self, kind, value, reason, state=None):
        if state is not None:
            self.state = state
        return ControlAction(kind, value, reason, self.state)

    def _offset_action(self, target: float, reason: str, state=None):
        low, high = self.offset_limits
        bounded = min(high, max(low, float(target)))
        if abs(bounded - self.current_offset) < 1e-12:
            return self._action("stop", None, "Offset已到允许边界", "fault")
        self.previous_offset = self.current_offset
        return self._action("offset", bounded, reason, state)

    def _begin_centering(self, observation: PeakObservation):
        self.previous_error = observation.balance_error
        self.stable_count = 0
        return self._offset_action(
            self.current_offset + self.step_size,
            "试探Offset响应方向", "probe",
        )

    def update(self, observation: PeakObservation) -> ControlAction:
        s = self.settings
        stage = self.current_stage
        if (observation.ambiguous
                and self.state not in {"verify_shrink", "refine"}):
            self.ambiguous_count += 1
            if self.ambiguous_count < 3:
                return self._action(
                    "none", None,
                    f"00模候选不唯一，等待独立窗口复核 {self.ambiguous_count}/3",
                )
            return self._action("stop", None, observation.reason, "ambiguous")
        if observation.valid:
            self.ambiguous_count = 0
            self.missing_count = 0
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
                    target = min(
                        self.search_amplitude_ceiling,
                        self.current_amplitude * 1.25,
                    )
                    if target > self.current_amplitude * 1.001:
                        return self._action(
                            "amplitude", target,
                            "启动幅度未找到00模，扩大Scan Amplitude继续搜索",
                            "select",
                        )
                    return self._action(
                        "stop", None,
                        "已达到无峰最大搜索幅度，仍未找到00模", "fault",
                    )
                return self._action("none", None, observation.reason)
            self.fingerprint = CarrierFingerprint(
                observation.prominence, observation.width_seconds,
                observation.polarity,
            )
            if observation.balance_error > stage.balance_tolerance:
                return self._begin_centering(observation)
            # A safely centered initial window may enter the stage
            # confirmation directly; a blind direction probe is unnecessary.
            self.previous_error = observation.balance_error
            self.previous_offset = self.current_offset
            self.stable_count = 0
            self.state = "center"

        if not observation.valid:
            if self.state in {"verify_shrink", "center", "probe", "track"}:
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

        if self.state == "probe":
            improved = (
                self.previous_error is None
                or observation.balance_error < self.previous_error
            )
            if not improved:
                self.direction = -1.0
                self.step_size = max(
                    stage.min_offset_step, self.step_size / 2.0
                )
                return self._offset_action(
                    self.previous_offset - self.step_size,
                    "正向试探变差，改为反向调节", "center",
                )
            self.direction = 1.0
            self.previous_error = observation.balance_error
            self.state = "center"

        if self.state in {"center", "track"}:
            if observation.balance_error <= stage.balance_tolerance:
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
                target = max(
                    self.amplitude_floor,
                    self.current_amplitude * stage.shrink_ratio,
                )
                if target >= self.current_amplitude * 0.999:
                    self.finalized = True
                    return self._action(
                        "none", None,
                        "达到最终Scan Amplitude目标并通过峰间隔复核", "track",
                    )
                return self._action(
                    "amplitude", target, "00模已居中，缩小Scan Amplitude",
                    "verify_shrink",
                )
            self.stable_count = 0
            if self.state == "track":
                self.bad_track_count += 1
                if self.bad_track_count < 2:
                    return self._action("none", None, "保持状态首次超差，等待复核")
            if (self.previous_error is not None
                    and observation.balance_error > self.previous_error * 1.05):
                self.direction *= -1.0
                self.step_size = max(
                    stage.min_offset_step, self.step_size / 2.0
                )
            self.previous_error = observation.balance_error
            return self._offset_action(
                self.current_offset + self.direction * self.step_size,
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
