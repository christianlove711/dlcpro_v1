from __future__ import annotations

import math

import pytest

from controllers.auto_lock_acquisition import (
    AcquisitionFrame,
    FpgaAcquisitionBackend,
    FpgaAcquisitionConfig,
    FpgaIntegrationPendingError,
)
from controllers.auto_lock_settings import (
    AUTO_LOCK_STRATEGY_ERROR,
    AUTO_LOCK_STRATEGY_HYBRID,
    AUTO_LOCK_STRATEGY_TRANSMISSION,
    AutoLockSettings,
)
from controllers.auto_lock_strategies import create_auto_lock_strategy


def _synthetic_frame(points: int = 1001) -> AcquisitionFrame:
    axis = tuple(index / (points - 1) for index in range(points))
    transmission = tuple(math.exp(-((value - 0.5) / 0.035) ** 2) for value in axis)
    error = tuple((value - 0.5) * math.exp(-((value - 0.5) / 0.07) ** 2) for value in axis)
    return AcquisitionFrame(
        time=axis,
        transmission=transmission,
        error=error,
        sample_rate=1_000_000.0,
    )


@pytest.mark.parametrize(
    "strategy_key",
    [
        AUTO_LOCK_STRATEGY_HYBRID,
        AUTO_LOCK_STRATEGY_TRANSMISSION,
        AUTO_LOCK_STRATEGY_ERROR,
    ],
)
def test_all_strategies_accept_clean_synchronized_signals(strategy_key: str) -> None:
    strategy = create_auto_lock_strategy(strategy_key)
    settings = AutoLockSettings(strategy=strategy_key)
    analysis = strategy.analyze(_synthetic_frame(), settings)
    assert analysis.peak_found
    assert analysis.zero_found
    assert analysis.transmission_guard_ready
    assert analysis.error_ready
    assert analysis.peak_fraction == pytest.approx(0.5, abs=0.005)
    assert analysis.zero_fraction == pytest.approx(0.5, abs=0.005)


def test_fpga_placeholder_validates_metadata_but_never_connects() -> None:
    config = FpgaAcquisitionConfig()
    config.validate()
    with pytest.raises(FpgaIntegrationPendingError):
        FpgaAcquisitionBackend(config).connect()


def test_fpga_channels_must_be_distinct() -> None:
    with pytest.raises(ValueError):
        FpgaAcquisitionConfig(transmission_channel=1, error_channel=1).validate()
