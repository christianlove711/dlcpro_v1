from __future__ import annotations

import math
from types import SimpleNamespace

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
from controllers.auto_lock_controller import AutoLockController
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


class _FastLockService:
    is_connected = True

    def __init__(self, snapshot: SimpleNamespace) -> None:
        self.snapshot = snapshot
        self.writes: list[tuple[str, float | bool]] = []

    def set_sc_frequency(self, value: float) -> SimpleNamespace:
        self.snapshot.sc_frequency = float(value)
        self.writes.append(("frequency", float(value)))
        return self.snapshot

    def set_sc_enabled(self, enabled: bool) -> SimpleNamespace:
        self.snapshot.sc_enabled = bool(enabled)
        self.writes.append(("scan_enabled", bool(enabled)))
        return self.snapshot

    def set_sc_amplitude(self, value: float) -> SimpleNamespace:
        self.snapshot.sc_amplitude = float(value)
        self.writes.append(("amplitude", float(value)))
        return self.snapshot

    def set_sc_offset(self, value: float) -> SimpleNamespace:
        self.snapshot.sc_offset = float(value)
        self.writes.append(("offset", float(value)))
        return self.snapshot

    def engage_falc1_configured_paths(self) -> SimpleNamespace:
        self.snapshot.sc_enabled = False
        # 与真实 service 一致：组合路径先 Main，读回后再 Unlim。
        self.snapshot.falc1.main.enabled = True
        self.writes.append(("falc_main", True))
        self.snapshot.falc1.unlim.enabled = True
        self.writes.append(("falc_unlim", True))
        return self.snapshot

    @staticmethod
    def format_error(error: Exception) -> str:
        return str(error)


class _FastLockOwner:
    language = "zh"

    def __init__(self) -> None:
        falc = SimpleNamespace(
            path_selection=3,
            main=SimpleNamespace(enabled=False),
            unlim=SimpleNamespace(enabled=False),
        )
        self.snapshot = SimpleNamespace(
            sc_enabled=False,
            sc_amplitude=0.5,
            sc_offset=0.0,
            sc_output_channel=50,
            sc_frequency=1.0,
            sc_signal_type=1,
            falc1=falc,
        )
        self.service = _FastLockService(self.snapshot)
        self.background_refresh_enabled = True
        self.operation_busy = False

    def submit_device_task(self, fn, on_success=None, **_kwargs) -> bool:
        snapshot = fn()
        if on_success is not None:
            on_success(snapshot)
        return True

    def publish_snapshot(self, snapshot) -> None:
        self.snapshot = snapshot

    def set_background_refresh_enabled(self, enabled: bool) -> None:
        self.background_refresh_enabled = enabled

    def set_operation_busy(self, busy: bool) -> None:
        self.operation_busy = busy


def test_fast_lock_start_writes_10_hz_before_enabling_scan() -> None:
    owner = _FastLockOwner()
    controller = AutoLockController(owner)
    controller._backend = object()

    controller.start()

    assert owner.service.writes[:3] == [
        ("frequency", 10.0),
        ("scan_enabled", True),
        ("amplitude", 1.0),
    ]
    assert controller._phase == "coarse_search"
    assert controller._frames_to_skip == 1


def test_fast_lock_centers_peak_narrows_below_point_two_and_engages_falc() -> None:
    owner = _FastLockOwner()
    controller = AutoLockController(owner)
    controller._backend = object()
    controller.start()
    frame = _synthetic_frame()

    for _ in range(50):
        controller._handle_frame(frame)
        if not controller.is_running:
            break

    assert not controller.is_running
    assert controller._phase == "locked"
    assert owner.snapshot.sc_amplitude == pytest.approx(0.18)
    assert owner.snapshot.sc_amplitude < 0.2
    assert not owner.snapshot.sc_enabled
    assert owner.snapshot.falc1.main.enabled
    assert owner.snapshot.falc1.unlim.enabled
    assert owner.service.writes[-2:] == [("falc_main", True), ("falc_unlim", True)]
