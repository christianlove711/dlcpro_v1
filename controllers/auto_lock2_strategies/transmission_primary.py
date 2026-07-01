from __future__ import annotations

from controllers.auto_lock2_settings import AutoLock2Settings
from controllers.auto_lock2_strategies.base import AutoLock2StrategyBase, SignalAnalysis


class TransmissionPrimaryStrategy(AutoLock2StrategyBase):
    key = "transmission_primary"
    text_key = "auto_lock2_strategy_transmission"
    control_label = "transmission peak"

    def coarse_found(self, analysis: SignalAnalysis) -> bool:
        return analysis.peak_found

    def control_ready(self, analysis: SignalAnalysis) -> bool:
        return analysis.peak_found and analysis.peak_fraction is not None

    def control_fraction(self, analysis: SignalAnalysis) -> float | None:
        return analysis.peak_fraction if analysis.peak_found else None

    def guard_ready(self, analysis: SignalAnalysis) -> bool:
        return analysis.error_ready

    def center_tolerance(self, settings: AutoLock2Settings, analysis: SignalAnalysis | None = None) -> float:
        return settings.peak_center_tolerance

    def candidate_found_message(self, analysis: SignalAnalysis) -> str:
        return f"transmission peak candidate found: {self.analysis_summary(analysis)}"

    def no_candidate_message(self, attempt: int) -> str:
        return f"no transmission peak; search offset attempt {attempt}"

    def search_exhausted_message(self) -> str:
        return "transmission peak search exhausted; AutoLock2 stopped"

    def guard_not_ready_message(self, analysis: SignalAnalysis) -> str:
        return "transmission peak is centered; waiting for valid PDH error zero guard: " + self.analysis_summary(analysis)
