from __future__ import annotations

from controllers.auto_lock2_settings import (
    AUTO_LOCK2_STRATEGY_ERROR,
    AUTO_LOCK2_STRATEGY_HYBRID,
    AUTO_LOCK2_STRATEGY_TRANSMISSION,
)
from controllers.auto_lock2_strategies.base import AutoLock2StrategyBase, SignalAnalysis
from controllers.auto_lock2_strategies.error_primary import ErrorPrimaryStrategy
from controllers.auto_lock2_strategies.hybrid import HybridStrategy
from controllers.auto_lock2_strategies.transmission_primary import TransmissionPrimaryStrategy


STRATEGY_CLASSES: dict[str, type[AutoLock2StrategyBase]] = {
    AUTO_LOCK2_STRATEGY_HYBRID: HybridStrategy,
    AUTO_LOCK2_STRATEGY_TRANSMISSION: TransmissionPrimaryStrategy,
    AUTO_LOCK2_STRATEGY_ERROR: ErrorPrimaryStrategy,
}


def create_auto_lock2_strategy(key: str) -> AutoLock2StrategyBase:
    strategy_class = STRATEGY_CLASSES.get(key, HybridStrategy)
    return strategy_class()


__all__ = [
    "AUTO_LOCK2_STRATEGY_ERROR",
    "AUTO_LOCK2_STRATEGY_HYBRID",
    "AUTO_LOCK2_STRATEGY_TRANSMISSION",
    "AutoLock2StrategyBase",
    "SignalAnalysis",
    "create_auto_lock2_strategy",
]
