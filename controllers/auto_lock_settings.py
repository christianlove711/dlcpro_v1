from __future__ import annotations

from dataclasses import dataclass


AUTO_LOCK_STRATEGY_HYBRID = "hybrid"
AUTO_LOCK_STRATEGY_TRANSMISSION = "transmission_primary"
AUTO_LOCK_STRATEGY_ERROR = "error_primary"


@dataclass(slots=True)
class AutoLockSettings:
    strategy: str = AUTO_LOCK_STRATEGY_TRANSMISSION
    search_frequency: float = 10.0
    wide_amplitude: float = 1.0
    min_amplitude: float = 0.18
    shrink_factor: float = 0.65
    offset_step: float = 0.05
    peak_center_tolerance: float = 0.10
    zero_center_tolerance: float = 0.06
    transmission_guard_tolerance: float = 0.08
    error_slope_sigma: float = 5.0
    min_error_slope: float = 0.02
    transmission_peak_sigma: float = 5.0
    min_transmission_prominence: float = 0.04
    stable_frames: int = 2
    max_offset_attempts: int = 80
    offset_correction_gain: float = 0.7
