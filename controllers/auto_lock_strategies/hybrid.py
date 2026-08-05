from __future__ import annotations

from controllers.auto_lock_settings import AutoLockSettings
from controllers.auto_lock_strategies.base import AutoLockStrategyBase, SignalAnalysis


class HybridStrategy(AutoLockStrategyBase):
    key = "hybrid"
    text_key = "auto_lock_strategy_hybrid"
    control_label = "PDH error zero after transmission peak"

    def coarse_found(self, analysis: SignalAnalysis) -> bool:
        return analysis.peak_found

    def control_ready(self, analysis: SignalAnalysis) -> bool:
        return analysis.error_ready or analysis.peak_found

    def control_fraction(self, analysis: SignalAnalysis) -> float | None:
        if analysis.error_ready:
            return analysis.zero_fraction
        return analysis.peak_fraction if analysis.peak_found else None

    def guard_ready(self, analysis: SignalAnalysis) -> bool:
        return analysis.transmission_guard_ready

    def center_tolerance(self, settings: AutoLockSettings, analysis: SignalAnalysis | None = None) -> float:
        if analysis is not None and not analysis.error_ready and analysis.peak_found:
            return settings.peak_center_tolerance
        return settings.zero_center_tolerance

    def candidate_found_message(self, analysis: SignalAnalysis) -> str:
        return f"transmission peak found; switch to PDH error-zero fine tuning: {self.analysis_summary(analysis)}"

    def no_candidate_message(self, attempt: int) -> str:
        return f"no transmission peak; search offset attempt {attempt}"

    def search_exhausted_message(self) -> str:
        return "transmission peak search exhausted; AutoLock stopped"

    def lost_message(self) -> str:
        return "PDH error zero or transmission guard lost during hybrid fine tuning; returning to last good scan range"
