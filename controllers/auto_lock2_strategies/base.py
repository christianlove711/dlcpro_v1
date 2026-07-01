from __future__ import annotations

import statistics
from dataclasses import dataclass

from controllers.auto_lock2_acquisition import AcquisitionFrame
from controllers.auto_lock2_settings import AutoLock2Settings


@dataclass(slots=True)
class SignalAnalysis:
    peak_found: bool
    peak_fraction: float | None
    peak_prominence: float
    peak_threshold: float
    transmission_noise: float
    transmission_guard_ready: bool
    zero_fraction: float | None
    zero_to_peak_distance: float | None
    zero_found: bool
    zero_slope: float
    zero_slope_threshold: float
    error_ready: bool
    confidence: float
    message: str


class AutoLock2StrategyBase:
    key = "base"
    text_key = "auto_lock2_strategy_hybrid"
    control_label = "signal"

    def analyze(self, frame: AcquisitionFrame, settings: AutoLock2Settings) -> SignalAnalysis:
        return analyze_signals(frame, settings)

    def coarse_found(self, analysis: SignalAnalysis) -> bool:
        raise NotImplementedError

    def control_ready(self, analysis: SignalAnalysis) -> bool:
        raise NotImplementedError

    def control_fraction(self, analysis: SignalAnalysis) -> float | None:
        raise NotImplementedError

    def guard_ready(self, analysis: SignalAnalysis) -> bool:
        return analysis.transmission_guard_ready

    def center_tolerance(self, settings: AutoLock2Settings, analysis: SignalAnalysis | None = None) -> float:
        return settings.zero_center_tolerance

    def candidate_found_message(self, analysis: SignalAnalysis) -> str:
        return f"{self.control_label} candidate found: {self.analysis_summary(analysis)}"

    def no_candidate_message(self, attempt: int) -> str:
        return f"no {self.control_label} candidate; search offset attempt {attempt}"

    def search_exhausted_message(self) -> str:
        return f"{self.control_label} search exhausted; AutoLock2 stopped"

    def lost_message(self) -> str:
        return f"{self.control_label} lost after narrowing/centering; returning to last good scan range"

    def restore_amplitude_message(self) -> str:
        return f"restore previous Scan Amplitude after {self.control_label} loss"

    def center_message(self, center_error: float) -> str:
        return f"center {self.control_label}; center_error={center_error:+.3f}"

    def guard_not_ready_message(self, analysis: SignalAnalysis) -> str:
        return f"{self.control_label} is centered but guard is not ready: {self.analysis_summary(analysis)}"

    def ready_candidate_message(self, stable: int, total: int, analysis: SignalAnalysis) -> str:
        return f"ready candidate frame {stable}/{total}: {self.analysis_summary(analysis)}"

    @staticmethod
    def analysis_summary(analysis: SignalAnalysis) -> str:
        peak_text = f"{analysis.peak_fraction:.3f}" if analysis.peak_fraction is not None else "n/a"
        zero_text = f"{analysis.zero_fraction:.3f}" if analysis.zero_fraction is not None else "n/a"
        guard_text = f"{analysis.zero_to_peak_distance:.3f}" if analysis.zero_to_peak_distance is not None else "n/a"
        return (
            f"peak={peak_text}, zero={zero_text}, guard={guard_text}, "
            f"slope={analysis.zero_slope:.4f}/{analysis.zero_slope_threshold:.4f}, "
            f"confidence={analysis.confidence:.2f}"
        )


def analyze_signals(frame: AcquisitionFrame, settings: AutoLock2Settings) -> SignalAnalysis:
    transmission = list(frame.transmission)
    error = list(frame.error)
    n = min(len(transmission), len(error))
    if n < 8:
        return SignalAnalysis(
            peak_found=False,
            peak_fraction=None,
            peak_prominence=0.0,
            peak_threshold=0.0,
            transmission_noise=0.0,
            transmission_guard_ready=False,
            zero_fraction=None,
            zero_to_peak_distance=None,
            zero_found=False,
            zero_slope=0.0,
            zero_slope_threshold=0.0,
            error_ready=False,
            confidence=0.0,
            message="too few samples",
        )

    transmission = transmission[:n]
    error = error[:n]
    baseline = statistics.median(transmission)
    deviations = [abs(value - baseline) for value in transmission]
    transmission_noise = statistics.median(deviations) * 1.4826
    peak_index = max(range(n), key=lambda index: transmission[index])
    peak_value = transmission[peak_index]
    prominence = peak_value - baseline
    peak_threshold = max(
        settings.min_transmission_prominence,
        settings.transmission_peak_sigma * max(transmission_noise, 1e-9),
    )
    peak_found = prominence >= peak_threshold
    peak_fraction = peak_index / max(1, n - 1) if peak_found else None
    zero_fraction, zero_slope, zero_slope_threshold, zero_found = best_error_zero(error, settings, peak_fraction)
    zero_to_peak_distance = (
        abs(zero_fraction - peak_fraction)
        if zero_fraction is not None and peak_fraction is not None
        else None
    )
    transmission_guard_ready = (
        peak_found
        and zero_to_peak_distance is not None
        and zero_to_peak_distance <= settings.transmission_guard_tolerance
    )
    error_ready = zero_found and zero_fraction is not None and transmission_guard_ready
    slope_confidence = 0.0 if zero_slope_threshold <= 0 else min(1.0, zero_slope / (zero_slope_threshold * 2.0))
    peak_confidence = 0.0 if peak_threshold <= 0 else min(1.0, prominence / (peak_threshold * 2.0))
    confidence = min(slope_confidence, peak_confidence) if transmission_guard_ready else max(slope_confidence, peak_confidence) * 0.5
    peak_text = f"{peak_fraction:.3f}" if peak_fraction is not None else "n/a"
    zero_text = f"{zero_fraction:.3f}" if zero_fraction is not None else "n/a"
    guard_text = f"{zero_to_peak_distance:.3f}" if zero_to_peak_distance is not None else "n/a"
    message = (
        f"peak={peak_text}, prominence={prominence:.4f}/{peak_threshold:.4f}, "
        f"zero={zero_text}, slope={zero_slope:.4f}/{zero_slope_threshold:.4f}, "
        f"guard={guard_text}, confidence={confidence:.2f}"
    )
    return SignalAnalysis(
        peak_found=peak_found,
        peak_fraction=peak_fraction,
        peak_prominence=prominence,
        peak_threshold=peak_threshold,
        transmission_noise=transmission_noise,
        transmission_guard_ready=transmission_guard_ready,
        zero_fraction=zero_fraction,
        zero_to_peak_distance=zero_to_peak_distance,
        zero_found=zero_found,
        zero_slope=zero_slope,
        zero_slope_threshold=zero_slope_threshold,
        error_ready=error_ready,
        confidence=confidence,
        message=message,
    )


def best_error_zero(
    values: list[float],
    settings: AutoLock2Settings,
    protect_fraction: float | None = None,
) -> tuple[float | None, float, float, bool]:
    n = len(values)
    if n < 2:
        return None, 0.0, settings.min_error_slope, False
    diffs = [(values[index + 1] - values[index]) * (n - 1) for index in range(n - 1)]
    slope_noise = robust_noise(diffs)
    slope_threshold = max(
        settings.min_error_slope,
        settings.error_slope_sigma * max(slope_noise, 1e-12),
    )
    candidates: list[tuple[float, float, float]] = []
    for index in range(n - 1):
        a = values[index]
        b = values[index + 1]
        crosses = a == 0 or b == 0 or a * b < 0
        if not crosses:
            continue
        if a == 0:
            local = 0.0
        else:
            denom = abs(a) + abs(b)
            local = 0.0 if denom <= 1e-15 else abs(a) / denom
        fraction = (index + local) / max(1, n - 1)
        slope = abs((b - a) * (n - 1))
        center_preference = -abs(fraction - 0.5)
        candidates.append((slope, center_preference, fraction))
    if not candidates:
        return None, 0.0, slope_threshold, False
    if protect_fraction is not None:
        eligible = [candidate for candidate in candidates if candidate[0] >= slope_threshold]
        pool = eligible or candidates
        slope, _center_preference, fraction = min(
            pool,
            key=lambda item: (abs(item[2] - protect_fraction), -item[0]),
        )
        return fraction, slope, slope_threshold, slope >= slope_threshold
    slope, _center_preference, fraction = max(candidates, key=lambda item: (item[0], item[1]))
    return fraction, slope, slope_threshold, slope >= slope_threshold


def robust_noise(values: list[float]) -> float:
    if not values:
        return 0.0
    baseline = statistics.median(values)
    return statistics.median(abs(value - baseline) for value in values) * 1.4826
