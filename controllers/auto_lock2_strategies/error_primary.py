from __future__ import annotations

from controllers.auto_lock2_settings import AutoLock2Settings
from controllers.auto_lock2_strategies.base import AutoLock2StrategyBase, SignalAnalysis


class ErrorPrimaryStrategy(AutoLock2StrategyBase):
    key = "error_primary"
    text_key = "auto_lock2_strategy_error"
    control_label = "PDH error zero"

    def coarse_found(self, analysis: SignalAnalysis) -> bool:
        return analysis.error_ready

    def control_ready(self, analysis: SignalAnalysis) -> bool:
        return analysis.error_ready and analysis.zero_fraction is not None

    def control_fraction(self, analysis: SignalAnalysis) -> float | None:
        return analysis.zero_fraction if analysis.error_ready else None

    def guard_ready(self, analysis: SignalAnalysis) -> bool:
        return analysis.transmission_guard_ready

    def center_tolerance(self, settings: AutoLock2Settings, analysis: SignalAnalysis | None = None) -> float:
        return settings.zero_center_tolerance

    def candidate_found_message(self, analysis: SignalAnalysis) -> str:
        return f"protected PDH error-zero candidate found: {self.analysis_summary(analysis)}"

    def no_candidate_message(self, attempt: int) -> str:
        return f"no protected PDH error zero; search offset attempt {attempt}"

    def search_exhausted_message(self) -> str:
        return "protected PDH error-zero search exhausted; AutoLock2 stopped"
