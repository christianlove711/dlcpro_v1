from __future__ import annotations

from controllers.auto_lock_settings import (
    AUTO_LOCK_STRATEGY_ERROR,
    AUTO_LOCK_STRATEGY_HYBRID,
    AUTO_LOCK_STRATEGY_TRANSMISSION,
)
from controllers.auto_lock_strategies.base import AutoLockStrategyBase, SignalAnalysis
from controllers.auto_lock_strategies.error_primary import ErrorPrimaryStrategy
from controllers.auto_lock_strategies.hybrid import HybridStrategy
from controllers.auto_lock_strategies.transmission_primary import TransmissionPrimaryStrategy


STRATEGY_CLASSES: dict[str, type[AutoLockStrategyBase]] = {
    AUTO_LOCK_STRATEGY_HYBRID: HybridStrategy,
    AUTO_LOCK_STRATEGY_TRANSMISSION: TransmissionPrimaryStrategy,
    AUTO_LOCK_STRATEGY_ERROR: ErrorPrimaryStrategy,
}


def create_auto_lock_strategy(key: str) -> AutoLockStrategyBase:
    strategy_class = STRATEGY_CLASSES.get(key, HybridStrategy)
    return strategy_class()


__all__ = [
    "AUTO_LOCK_STRATEGY_ERROR",
    "AUTO_LOCK_STRATEGY_HYBRID",
    "AUTO_LOCK_STRATEGY_TRANSMISSION",
    "AutoLockStrategyBase",
    "SignalAnalysis",
    "create_auto_lock_strategy",
]
