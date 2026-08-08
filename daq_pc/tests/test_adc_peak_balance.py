"""Contract tests for the two-stage ADC 00-mode auto-lock algorithm."""
from __future__ import annotations

import csv
import json
from dataclasses import fields
from types import SimpleNamespace

import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication, QObject, Signal

from daq_pc.adc_peak_balance_algorithm import (
    CarrierFingerprint,
    PeakBalanceEngine,
    PeakBalanceSettings,
    PeakObservation,
    analyze_carrier,
)
from daq_pc.adc_peak_balance_controller import (
    AdcPeakBalanceController,
    _AutoLockCsvSession,
)
from daq_pc.adc_peak_balance_sim import VirtualCavity, run_virtual_lock

_CORE_APP = None


class _ControllerSession(QObject):
    write_snapshot_changed = Signal(object)
    falc_engaged = Signal(object)
    connection_changed = Signal(bool, str)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.is_connected = True
        self.engage_calls = 0
        self._snapshot = SimpleNamespace(
            sc_frequency=1.0, sc_enabled=True, sc_signal_type=1,
            sc_offset=64.0, sc_amplitude=0.2, sc_unit="V",
        )

    def snapshot(self):
        return self._snapshot

    def engage_configured_falc(self):
        self.engage_calls += 1


class _ControllerRing:
    HISTORY_SECONDS = 10.0

    @staticmethod
    def raw_history(_seconds):
        return SimpleNamespace(bin_indices=np.asarray([0, 1], dtype=np.int64))


def _ready_controller(settings: PeakBalanceSettings):
    global _CORE_APP
    _CORE_APP = QCoreApplication.instance() or QCoreApplication([])
    session = _ControllerSession()
    controller = AdcPeakBalanceController(_ControllerRing(), session, lambda: True)
    controller.settings = settings
    controller.engine = PeakBalanceEngine(settings)
    controller.engine.start(64.0, 0.2)
    controller.running = True
    controller.observe_only = False
    controller.scan_frequency = 1.0
    controller.start_offset = 64.0
    controller.start_amplitude = 0.2
    controller.available_after = 0.0
    return controller, session


def observation(error: float, *, valid: bool = True, code: str = "VALID",
                prominence: float = 1000.0) -> PeakObservation:
    return PeakObservation(
        valid, "有效" if valid else "无效", code,
        prominence=prominence, second_prominence=5.0,
        dominance_ratio=200.0, snr=100.0, expected_period=1.0,
        measured_period=1.0, period_error=0.0,
        delta_t1=0.5 * (1.0 + error),
        delta_t2=0.5 * (1.0 - error),
        signed_error=error, balance_error=abs(error),
    )


def no_peak() -> PeakObservation:
    return PeakObservation(False, "未找到足够的00模穿越峰", "NO_PEAK")


def test_settings_are_exactly_the_21_visible_parameters():
    names = [item.name for item in fields(PeakBalanceSettings)]
    assert names == [
        "channel", "polarity", "min_prominence_codes", "noise_sigma",
        "main_family_ratio", "period_tolerance", "narrow_main_height_ratio",
        "invalid_retry_windows", "search_frequency_hz",
        "initial_search_amplitude", "initial_offset_search_step",
        "wide_probe_step", "wide_shrink_tolerance", "wide_confirm_windows",
        "wide_model_corrections", "final_amplitude", "final_coarse_step",
        "final_fine_step", "final_max_offset_deviation",
        "final_balance_tolerance", "falc_confirm_windows",
    ]
    package = PeakBalanceSettings()
    assert package.search_frequency_hz == 10.0
    assert package.initial_search_amplitude == 2.5
    assert package.main_family_ratio == 5.0
    assert package.final_amplitude == 0.2
    assert package.final_coarse_step == 0.01
    assert package.final_fine_step == 0.001
    assert package.final_max_offset_deviation == 0.09
    assert package.final_balance_tolerance == 0.05


@pytest.mark.parametrize("deleted", [
    "prediction_gain", "max_search_amplitude_factor", "shrink_ratio",
    "final_local_max_distance", "coarse_boundary",
])
def test_deleted_legacy_settings_are_not_silently_accepted(deleted):
    with pytest.raises(TypeError):
        PeakBalanceSettings(**{deleted: 1.0})


def test_100_to_1_carrier_is_selected_over_sidebands():
    cavity = VirtualCavity(sideband_fraction=0.01)
    settings = PeakBalanceSettings(min_prominence_codes=40)
    result = analyze_carrier(cavity.history(0.12, 1.2), settings, 1.0)
    assert result.valid
    assert result.family_count >= 1
    assert result.dominance_ratio >= settings.main_family_ratio
    assert result.prominence > 20 * max(result.second_prominence, 1.0)


def test_broad_repeated_maxima_are_one_physical_crossing_family():
    cavity = VirtualCavity(linewidth=0.05, sideband_fraction=0.01)
    result = analyze_carrier(
        cavity.history(0.0, 0.2, cycles=2.2),
        PeakBalanceSettings(min_prominence_codes=40), 1.0,
    )
    assert result.valid
    assert result.peak_count == 4
    assert result.family_count == 1


def test_analysis_uses_exactly_two_periods_even_with_fifth_edge_crossing():
    cavity = VirtualCavity(sideband_fraction=0.01)
    result = analyze_carrier(
        cavity.history(0.0, 1.2, cycles=3.0),
        PeakBalanceSettings(min_prominence_codes=40), 1.0,
    )
    assert result.valid
    assert len(result.peak_times) == 4
    assert max(result.peak_times) < 2.0


def test_period_jitter_is_quantified_and_checked_by_user_tolerance():
    cavity = VirtualCavity(frequency_hz=0.88, sideband_fraction=0.01)
    result = analyze_carrier(
        cavity.history(0.0, 1.2),
        PeakBalanceSettings(min_prominence_codes=40, period_tolerance=0.10),
        1.0,
    )
    assert not result.valid
    assert result.reason_code == "PERIOD_MISMATCH"


def test_adc_hole_is_invalid_with_reason_code():
    cavity = VirtualCavity(sideband_fraction=0.01)
    result = analyze_carrier(
        cavity.history(0.0, 1.2, gap_slice=slice(50, 51)),
        PeakBalanceSettings(min_prominence_codes=40), 1.0,
    )
    assert not result.valid
    assert result.reason_code == "DATA_GAP"


def test_narrow_carrier_must_retain_configured_wide_height_fraction():
    settings = PeakBalanceSettings(narrow_main_height_ratio=0.05)
    cavity = VirtualCavity(sideband_fraction=0.01, carrier_height_codes=900)
    history = cavity.history(0.0, 0.2)
    fingerprint = CarrierFingerprint(20_000.0, 0.01, "positive")
    result = analyze_carrier(history, settings, 1.0, fingerprint)
    assert not result.valid
    assert result.reason_code == "REFERENCE_TOO_WEAK"


def test_all_non_missing_invalid_windows_hold_offset_then_stop():
    settings = PeakBalanceSettings(invalid_retry_windows=3)
    engine = PeakBalanceEngine(settings)
    engine.start(64.0, 2.5)
    bad = PeakObservation(False, "周期错误", "PERIOD_MISMATCH")
    actions = [engine.update(bad) for _ in range(4)]
    assert [item.kind for item in actions] == ["none", "none", "none", "stop"]
    assert all(item.value is None for item in actions)


def test_wide_true_no_peak_searches_plus_minus_expanding_at_one_volt():
    engine = PeakBalanceEngine(PeakBalanceSettings(initial_offset_search_step=1.0))
    engine.start(64.0, 2.5)
    assert engine.update(no_peak()).kind == "none"
    first = engine.update(no_peak())
    assert first.kind == "offset" and first.value == pytest.approx(65.0)
    engine.sync(first.value, 2.5)
    assert engine.update(no_peak()).kind == "none"
    second = engine.update(no_peak())
    assert second.kind == "offset" and second.value == pytest.approx(63.0)


def test_wide_probe_jumps_full_theoretical_distance_from_probe_origin():
    settings = PeakBalanceSettings(wide_probe_step=0.05)
    engine = PeakBalanceEngine(settings)
    engine.start(64.0, 2.5)
    probe = engine.update(observation(0.20))
    assert probe.value == pytest.approx(64.05)
    engine.sync(probe.value, 2.5)
    jump = engine.update(observation(0.15))
    assert jump.state == "wide_jump"
    assert jump.value == pytest.approx(64.0 + 0.5 * 2.5 * 0.20)


def test_wide_pass_stops_offset_and_shrinks_directly_after_configured_windows():
    engine = PeakBalanceEngine(PeakBalanceSettings(wide_confirm_windows=2))
    engine.start(64.0, 2.5)
    first = engine.update(observation(0.07))
    second = engine.update(observation(0.06))
    assert first.kind == "none"
    assert second.kind == "amplitude"
    assert second.value == pytest.approx(0.2)


def test_starting_at_final_amplitude_never_uses_theoretical_distance():
    settings = PeakBalanceSettings(final_amplitude=0.2)
    engine = PeakBalanceEngine(settings)
    engine.start(64.0, 0.2)
    action = engine.update(observation(0.30))
    assert action.state == "final_adjust"
    assert action.value == pytest.approx(64.01)
    assert abs(action.value - 64.0) != pytest.approx(0.5 * 0.2 * 0.30)


def test_final_worse_coarse_probe_restores_best_and_reverses_at_fine_step():
    engine = PeakBalanceEngine(PeakBalanceSettings())
    engine.start(64.0, 0.2)
    coarse = engine.update(observation(0.30))
    engine.sync(coarse.value, 0.2)
    fine = engine.update(observation(0.36))
    assert engine.step_size == pytest.approx(0.001)
    assert fine.value == pytest.approx(63.999)


def test_final_two_missing_windows_reacquire_symmetrically_without_widening():
    engine = PeakBalanceEngine(PeakBalanceSettings())
    engine.start(64.0, 0.2)
    assert engine.update(no_peak()).kind == "none"
    plus = engine.update(no_peak())
    assert plus.kind == "offset" and plus.value == pytest.approx(64.01)
    engine.sync(plus.value, 0.2)
    minus = engine.update(no_peak())
    assert minus.kind == "offset" and minus.value == pytest.approx(63.99)
    assert engine.current_amplitude == pytest.approx(0.2)


def test_final_offset_is_clamped_to_entry_plus_minus_009():
    engine = PeakBalanceEngine(PeakBalanceSettings(final_max_offset_deviation=0.09))
    engine.start(64.0, 0.2)
    low, high = engine.offset_limits
    assert (low, high) == pytest.approx((63.91, 64.09))


def test_falc_confirmation_count_is_user_configurable():
    engine = PeakBalanceEngine(PeakBalanceSettings(falc_confirm_windows=3))
    engine.start(64.0, 0.2)
    states = [engine.update(observation(0.03)).state for _ in range(3)]
    assert states == ["final_confirm", "final_confirm", "track"]
    assert engine.finalized


def test_controller_without_falc_stops_on_first_valid_final_pass(monkeypatch):
    settings = PeakBalanceSettings(falc_confirm_windows=3)
    controller, session = _ready_controller(settings)
    controller.auto_engage_falc = False
    stopped = []
    controller.stopped.connect(stopped.append)
    monkeypatch.setattr(
        "daq_pc.adc_peak_balance_controller.analyze_carrier",
        lambda *_args, **_kwargs: observation(0.03),
    )
    controller._tick()
    assert not controller.running
    assert controller.engine.finalized
    assert session.engage_calls == 0
    assert stopped and "未勾选自动使能FALC" in stopped[-1]


def test_controller_with_falc_waits_configured_windows(monkeypatch):
    settings = PeakBalanceSettings(falc_confirm_windows=3)
    controller, session = _ready_controller(settings)
    controller.auto_engage_falc = True
    monkeypatch.setattr(
        "daq_pc.adc_peak_balance_controller.analyze_carrier",
        lambda *_args, **_kwargs: observation(0.03),
    )
    for _ in range(2):
        controller.available_after = 0.0
        controller._tick()
        assert session.engage_calls == 0
    controller.available_after = 0.0
    controller._tick()
    assert session.engage_calls == 1
    assert controller.pending_kind == "falc"


def test_virtual_cavity_reaches_final_amplitude_without_restore_or_grid_states():
    trace = run_virtual_lock(iterations=20)
    assert any(row["amplitude"] == pytest.approx(0.2) for row in trace)
    assert trace[-1]["state"] == "track"
    forbidden = {"legacy_restore", "final_local_search", "restore_amplitude"}
    assert not forbidden.intersection(row["state"] for row in trace)


def test_quantized_frequency_readback_uses_device_resolution_tolerance():
    assert AdcPeakBalanceController._frequency_matches(5.00005, 5.0)
    assert AdcPeakBalanceController._frequency_matches(0.999947, 1.0)
    assert not AdcPeakBalanceController._frequency_matches(1.01, 1.0)


def test_csv_session_contains_only_four_event_types_and_finalizes(tmp_path):
    session = _AutoLockCsvSession(
        tmp_path, mode="auto", settings=PeakBalanceSettings().as_dict(),
        device_start={"frequency_hz": 1.0, "amplitude_vpp": 2.5, "offset_v": 64.0},
    )
    session.write("MEASURE", state="wide_confirm", valid=1, balance_error=0.04)
    session.write("WRITE", write_kind="amplitude", requested_value=0.2,
                  readback_value=0.2, write_ok=1)
    path = session.finish("locked", "测试完成")
    assert path.exists() and not path.name.endswith("partial.csv")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["event"] for row in rows] == ["START", "MEASURE", "WRITE", "END"]
    assert len(json.loads(rows[0]["settings_json"])) == 21
