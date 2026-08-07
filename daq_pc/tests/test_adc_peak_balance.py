import os
import unittest
from unittest import mock
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from daq_pc.adc_peak_balance_algorithm import (
    PeakBalanceEngine,
    PeakBalanceSettings,
    PeakObservation,
    analyze_carrier,
)
from daq_pc.adc_peak_balance_sim import VirtualCavity, run_virtual_lock
from daq_pc.adc_peak_balance_controller import AdcPeakBalanceController
from daq_pc.daq_udp_dual import DualSampleRingBuffer


class _FakeDlcSession(QObject):
    write_snapshot_changed = Signal(object)
    falc_engaged = Signal(object)
    connection_changed = Signal(bool, str)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.is_connected = True
        self.offset_writes = []
        self.amplitude_writes = []
        self.frequency_writes = []
        self.scan_writes = []
        self._snapshot = SimpleNamespace(
            sc_enabled=True,
            sc_frequency=1.0,
            sc_signal_type=1,
            sc_output_channel=50,
            sc_unit="V",
            sc_offset=0.0,
            sc_amplitude=1.2,
        )

    def snapshot(self):
        return self._snapshot

    def set_scan_offset(self, value):
        self.offset_writes.append(float(value))
        self._snapshot.sc_offset = float(value)
        self.write_snapshot_changed.emit(self._snapshot)

    def set_scan_amplitude(self, value):
        self.amplitude_writes.append(float(value))
        self._snapshot.sc_amplitude = float(value)
        self.write_snapshot_changed.emit(self._snapshot)

    def set_scan_frequency(self, value):
        self.frequency_writes.append(float(value))
        self._snapshot.sc_frequency = float(value)
        self.write_snapshot_changed.emit(self._snapshot)

    def set_scan_enabled(self, enabled):
        self.scan_writes.append(bool(enabled))
        self._snapshot.sc_enabled = bool(enabled)
        self.write_snapshot_changed.emit(self._snapshot)

    def engage_configured_falc(self):
        self._snapshot.sc_enabled = False
        self._snapshot.falc1 = SimpleNamespace(
            path_selection=3,
            main=SimpleNamespace(enabled=True, lock_state=True),
            unlim=SimpleNamespace(enabled=True, lock_state=True),
        )
        self.falc_engaged.emit(self._snapshot)


class _FrameRing:
    HISTORY_SECONDS = 20.0

    def __init__(self, frame):
        self.frame = frame

    def raw_history(self, _seconds=None):
        return self.frame


def _shifted_history(cavity, first_bin):
    frame = cavity.history(0.0, 1.2)
    frame.bin_indices = frame.bin_indices + int(first_bin)
    return frame


class AdcPeakBalanceAlgorithmTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.settings = PeakBalanceSettings(
            min_prominence_codes=40,
            max_offset_deviation=0.5,
            offset_step=0.03,
            search_frequency_hz=1.0,
            initial_search_amplitude=1.2,
        )

    def test_raw_code_carrier_is_selected_over_low_sidebands(self):
        cavity = VirtualCavity(sideband_fraction=0.18)
        centered = analyze_carrier(
            cavity.history(0.0, 1.2), self.settings, 1.0
        )
        displaced = analyze_carrier(
            cavity.history(0.18, 1.2), self.settings, 1.0
        )
        self.assertTrue(centered.valid, centered.reason)
        self.assertGreater(centered.dominance_ratio, 2.0)
        self.assertLess(centered.balance_error, 0.02)
        self.assertTrue(displaced.valid, displaced.reason)
        self.assertGreater(displaced.balance_error, 0.20)
        self.assertAlmostEqual(displaced.measured_period, 1.0, delta=0.10)

    def test_negative_peak_and_dynamic_frequency(self):
        cavity = VirtualCavity(frequency_hz=0.5, polarity=-1)
        observation = analyze_carrier(
            cavity.history(0.0, 1.2), self.settings, 0.5
        )
        self.assertTrue(observation.valid, observation.reason)
        self.assertEqual(observation.polarity, "negative")
        self.assertAlmostEqual(observation.measured_period, 2.0, delta=0.20)

    def test_adc_gap_invalidates_entire_control_window(self):
        cavity = VirtualCavity()
        observation = analyze_carrier(
            cavity.history(0.0, 1.2, gap_slice=slice(100, 120)),
            self.settings, 1.0,
        )
        self.assertFalse(observation.valid)
        self.assertIn("索引空洞", observation.reason)

    def test_raw_history_preserves_adc_codes_absolute_bins_and_gaps(self):
        ring = DualSampleRingBuffer(capacity=32)
        first = np.array([[120, -30], [450, -80]], dtype="<i2")
        after_gap = np.array([[-320, 900]], dtype="<i2")

        ring.append_packet(0, 1, 1_000, first.tobytes())
        ring.append_packet(4, 1, 1_000, after_gap.tobytes())
        history = ring.raw_history()

        np.testing.assert_array_equal(history.bin_indices, [0, 1, 2, 3, 4])
        np.testing.assert_array_equal(history.valid, [True, True, False, False, True])
        np.testing.assert_array_equal(history.minimum_a, [120, 450, 0, 0, -320])
        np.testing.assert_array_equal(history.maximum_b, [-30, -80, 0, 0, 900])
        self.assertEqual(history.sample_rate_hz, 1_000)
        self.assertEqual(history.bin_seconds, 0.001)

    def test_equal_strength_sidebands_are_rejected_as_ambiguous(self):
        cavity = VirtualCavity(sideband_fraction=1.0)
        observation = analyze_carrier(
            cavity.history(0.0, 1.2), self.settings, 1.0
        )
        self.assertFalse(observation.valid)
        self.assertEqual(observation.reason, "00模候选不唯一")

    def test_offset_recovery_precedes_amplitude_expansion(self):
        engine = PeakBalanceEngine(self.settings)
        engine.start(0.0, 1.0)
        engine.state = "track"
        engine.finalized = True
        engine.current_amplitude = 0.4
        engine.last_good_amplitude = 0.8
        missing = PeakObservation(False, "未找到足够的00模穿越峰")
        actions = []
        expected_offsets = [0.02, -0.02, 0.04, -0.04]
        for _ in range(4):
            action = engine.update(missing)
            actions.append(action)
            self.assertEqual(action.kind, "offset")
            self.assertAlmostEqual(action.value, expected_offsets[len(actions) - 1])
            engine.sync(float(action.value), 0.4)
        fifth = engine.update(missing)
        self.assertEqual(fifth.kind, "amplitude")
        self.assertEqual(fifth.state, "restore_amplitude")

    def test_virtual_lock_centers_shrinks_and_tracks_drift(self):
        trace = run_virtual_lock(120, drift_per_step=0.0002)
        self.assertTrue(trace)
        self.assertNotIn("ambiguous", {row["state"] for row in trace})
        self.assertLess(trace[-1]["amplitude"], 1.2)
        self.assertLessEqual(abs(
            trace[-1]["offset"] - trace[-1]["carrier_position"]
        ), 0.04)
        valid_tail = [
            row for row in trace[-20:] if row["valid"]
        ]
        self.assertTrue(valid_tail)
        self.assertLess(min(row["balance_error"] for row in valid_tail), 0.12)

    def test_frequency_change_rebuilds_period_without_sideband_lock(self):
        trace = run_virtual_lock(
            120, drift_per_step=0.0001, frequency_change_at=50
        )
        self.assertEqual(trace[-1]["frequency_hz"], 0.5)
        self.assertNotIn("ambiguous", {row["state"] for row in trace})
        self.assertIn(
            trace[-1]["state"],
            {"center", "track", "local_recover", "restore_amplitude", "refine"},
        )

    def test_observe_mode_never_writes_and_never_reuses_same_bins(self):
        cavity = VirtualCavity()
        ring = _FrameRing(_shifted_history(cavity, 0))
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(ring, session, lambda: True)
        controller.start(self.settings, observe_only=True)

        ring.frame = _shifted_history(cavity, 10_000)
        controller.available_after = 0.0
        controller._tick()
        self.assertEqual(controller.engine.stable_count, 1)
        consumed_end = controller.gate_bin

        # Force a timer tick without adding data. The same window must not be
        # counted as the second stable confirmation.
        controller.available_after = 0.0
        controller._tick()
        self.assertEqual(controller.engine.stable_count, 1)
        self.assertEqual(controller.gate_bin, consumed_end)
        self.assertEqual(session.offset_writes, [])
        self.assertEqual(session.amplitude_writes, [])
        controller.stop()

    def test_observe_mode_gives_bounded_manual_offset_directions(self):
        cavity = VirtualCavity()
        ring = _FrameRing(_shifted_history(cavity, 0))
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(ring, session, lambda: True)
        controller.start(self.settings, observe_only=True)

        first = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.20,
        )
        controller._observe(first)
        self.assertIn("0.030000", controller.manual_advice)
        self.assertIn("正向试探", controller.manual_advice)

        controller.engine.sync(0.03, 1.2)
        improved = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.13,
        )
        controller._observe(improved)
        self.assertIn("继续同方向", controller.manual_advice)
        self.assertIn("0.060000", controller.manual_advice)

        controller.engine.sync(0.06, 1.2)
        worsened = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.16,
        )
        controller._observe(worsened)
        self.assertIn("反向并减小步长", controller.manual_advice)
        self.assertIn("0.045000", controller.manual_advice)
        self.assertEqual(session.offset_writes, [])
        self.assertEqual(session.amplitude_writes, [])
        controller.stop()

    def test_falc_engagement_uses_configured_paths_and_finishes(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.running = True
        controller.auto_engage_falc = True
        controller._engage_falc()
        self.assertTrue(controller.falc_engaged)
        self.assertFalse(controller.running)
        self.assertFalse(session.snapshot().sc_enabled)
        self.assertTrue(session.snapshot().falc1.main.enabled)
        self.assertTrue(session.snapshot().falc1.unlim.enabled)

    def test_final_three_independent_windows_automatically_engage_falc(self):
        cavity = VirtualCavity()
        ring = _FrameRing(_shifted_history(cavity, 0))
        session = _FakeDlcSession()
        session._snapshot.sc_amplitude = 0.2
        session._snapshot.falc1 = SimpleNamespace(
            path_selection=3,
            main=SimpleNamespace(enabled=False, lock_state=False),
            unlim=SimpleNamespace(enabled=False, lock_state=False),
        )
        controller = AdcPeakBalanceController(ring, session, lambda: True)
        controller.start(
            PeakBalanceSettings(
                target_amplitude=0.2, initial_search_amplitude=0.2,
            ),
            observe_only=False,
            auto_engage_falc=True,
        )
        controller.engine.state = "center"
        valid = PeakObservation(
            True, "00模有效", prominence=800.0,
            second_prominence=100.0, dominance_ratio=8.0,
            width_seconds=0.002, snr=20.0, balance_error=0.04,
        )
        with mock.patch(
            "daq_pc.adc_peak_balance_controller.analyze_carrier",
            return_value=valid,
        ):
            for index in range(3):
                ring.frame = _shifted_history(cavity, (index + 1) * 10_000)
                controller.available_after = 0.0
                controller._tick()
        self.assertTrue(controller.falc_engaged)
        self.assertFalse(controller.running)
        self.assertFalse(session.snapshot().sc_enabled)

    def test_final_pass_without_auto_falc_stops_adjusting_and_keeps_scan(self):
        cavity = VirtualCavity()
        ring = _FrameRing(_shifted_history(cavity, 0))
        session = _FakeDlcSession()
        session._snapshot.sc_amplitude = 0.2
        controller = AdcPeakBalanceController(ring, session, lambda: True)
        controller.start(
            PeakBalanceSettings(
                target_amplitude=0.2, search_frequency_hz=1.0,
                initial_search_amplitude=0.2,
            ),
            observe_only=False,
            auto_engage_falc=False,
        )
        controller.engine.state = "center"
        valid = PeakObservation(
            True, "00模有效", prominence=800.0,
            second_prominence=100.0, dominance_ratio=8.0,
            width_seconds=0.002, snr=20.0, balance_error=0.04,
        )
        with mock.patch(
            "daq_pc.adc_peak_balance_controller.analyze_carrier",
            return_value=valid,
        ):
            for index in range(3):
                ring.frame = _shifted_history(cavity, (index + 1) * 10_000)
                controller.available_after = 0.0
                controller._tick()
        self.assertFalse(controller.running)
        self.assertFalse(controller.falc_engaged)
        self.assertTrue(session.snapshot().sc_enabled)
        self.assertEqual(session.offset_writes, [])
        self.assertEqual(session.amplitude_writes, [])
        self.assertIn("停止自动调节", controller.manual_advice)

    def test_automatic_scan_write_requires_matching_device_readback(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.running = True
        controller.pending_write = True
        controller.pending_kind = "offset"
        controller.pending_value = 0.25
        session._snapshot.sc_offset = 0.20
        controller._write_completed(session._snapshot)
        self.assertFalse(controller.running)
        self.assertFalse(controller.pending_write)

    def test_observe_mode_ignores_shared_manual_write_completion(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        engine = PeakBalanceEngine(self.settings)
        engine.start(0.0, 1.2)
        controller.engine = engine
        controller.running = True
        controller.observe_only = True
        session._snapshot.sc_offset = 0.1
        controller._write_completed(session._snapshot)
        self.assertEqual(engine.current_offset, 0.0)

    def test_two_level_strategy_selects_search_and_final_limits(self):
        engine = PeakBalanceEngine(self.settings)
        engine.start(0.0, 4.0)
        expected = (
            (4.0, "快速寻峰", 0.08, 0.03, 0.05, 2),
            (1.5, "快速寻峰", 0.08, 0.03, 0.2 / 1.5, 2),
            (0.4, "快速寻峰", 0.08, 0.03, 0.5, 2),
            (0.2, "最终锁定", 0.05, 0.001, None, 3),
        )
        for amplitude, name, tolerance, step, shrink, windows in expected:
            engine.sync(0.0, amplitude)
            stage = engine.current_stage
            self.assertEqual(stage.name, name)
            self.assertAlmostEqual(stage.balance_tolerance, tolerance)
            self.assertAlmostEqual(stage.offset_step, step)
            self.assertEqual(stage.shrink_ratio, shrink)
            self.assertEqual(stage.stable_windows, windows)

    def test_search_shrinks_directly_to_final_after_two_windows(self):
        settings = PeakBalanceSettings(target_amplitude=0.2)
        engine = PeakBalanceEngine(settings)
        engine.start(0.0, 1.2)
        valid = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.01,
        )
        engine.state = "center"
        self.assertEqual(engine.update(valid).kind, "none")
        action = engine.update(valid)
        self.assertEqual(action.kind, "amplitude")
        self.assertAlmostEqual(float(action.value), 0.2)
        self.assertEqual(action.state, "final_shrink")

        engine.sync(0.0, 0.2)
        engine.state = "center"
        engine.stable_count = 0
        for _ in range(3):
            action = engine.update(valid)
        self.assertEqual(action.kind, "none")
        self.assertTrue(engine.finalized)

    def test_final_amplitude_and_minimum_offset_step_are_hard_limits(self):
        settings = PeakBalanceSettings(
            offset_step=0.1,
            min_offset_step=0.001,
            target_amplitude=0.2,
            balance_tolerance=0.05,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(0.0, 4.0)
        engine.sync(0.0, 0.2)
        engine.state = "center"
        engine.step_size = 0.001
        valid = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.04,
        )
        for _ in range(settings.stable_windows):
            action = engine.update(valid)
        self.assertTrue(engine.finalized)
        self.assertEqual(action.kind, "none")
        self.assertEqual(action.state, "track")
        self.assertAlmostEqual(engine.amplitude_floor, 0.2)

        engine.finalized = False
        engine.state = "center"
        engine.previous_error = 0.01
        worse = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.20,
        )
        engine.update(worse)
        self.assertGreaterEqual(engine.step_size, 0.001)

    def test_theoretical_prediction_uses_origin_not_probe_offset(self):
        settings = PeakBalanceSettings(
            offset_step=0.05, prediction_gain=0.8,
            target_amplitude=0.2,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(65.0, 1.2)
        baseline = PeakObservation(True, "00模有效", balance_error=0.20)
        probe = engine.update(baseline)
        self.assertAlmostEqual(float(probe.value), 65.05)
        engine.sync(float(probe.value), 1.2)

        improved = PeakObservation(True, "00模有效", balance_error=0.12)
        predicted = engine.update(improved)
        # D = A/2*E = 0.12 V; 0.8D is applied from 65.000, not 65.050.
        self.assertAlmostEqual(float(predicted.value), 65.096)
        self.assertEqual(predicted.state, "search_verify")

    def test_model_residual_correction_prepares_direct_final_shrink(self):
        settings = PeakBalanceSettings(
            offset_step=0.05, prediction_gain=0.8,
            target_amplitude=0.2, search_windows=2,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(0.0, 1.2)
        first = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.20
        ))
        engine.sync(float(first.value), 1.2)
        predicted = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.25
        ))
        engine.sync(float(predicted.value), 1.2)
        correction = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.12
        ))
        self.assertEqual(correction.state, "search_model_correct")
        self.assertAlmostEqual(
            float(correction.value), float(predicted.value) - 0.0576
        )

    def test_two_sub_eight_percent_windows_shrink_without_more_offset_writes(self):
        settings = PeakBalanceSettings(
            offset_step=0.05, prediction_gain=0.8,
            target_amplitude=0.2, search_tolerance=0.08,
            search_windows=2,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(66.049572, 2.370071)
        probe = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.52
        ))
        engine.sync(float(probe.value), 2.370071)
        predicted = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.4727
        ))
        engine.sync(float(predicted.value), 2.370071)

        first_good = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.0631
        ))
        self.assertEqual(first_good.kind, "none")
        self.assertEqual(first_good.state, "search_accept")
        second_good = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.0651
        ))
        self.assertEqual(second_good.kind, "amplitude")
        self.assertEqual(second_good.state, "final_shrink")
        self.assertAlmostEqual(float(second_good.value), 0.2)

    def test_final_local_search_uses_exact_one_millivolt_grid(self):
        settings = PeakBalanceSettings(
            target_amplitude=0.2, min_offset_step=0.001,
            final_local_max_distance=0.005,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(65.0, 0.2)
        engine.state = "final_verify"
        observation = PeakObservation(
            True, "00模有效", balance_error=0.10
        )
        action = engine.update(observation)
        values = [float(action.value)]
        engine.sync(values[-1], 0.2)
        for error in (0.09,) * 9:
            action = engine.update(PeakObservation(
                True, "00模有效", balance_error=error
            ))
            values.append(float(action.value))
            engine.sync(values[-1], 0.2)
        self.assertEqual(values, [
            65.001, 64.999, 65.002, 64.998, 65.003,
            64.997, 65.004, 64.996, 65.005, 64.995,
        ])
        self.assertTrue(all(
            abs(value - 65.0) <= 0.005 + 1e-12 for value in values
        ))

    def test_starting_at_final_amplitude_never_uses_theoretical_jump(self):
        settings = PeakBalanceSettings(
            target_amplitude=0.2, min_offset_step=0.001,
            final_local_max_distance=0.005,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(65.8, 0.2)
        action = engine.update(PeakObservation(
            True, "00模有效", prominence=800.0,
            width_seconds=0.01, balance_error=0.1477,
        ))
        self.assertEqual(action.kind, "offset")
        self.assertEqual(action.state, "final_local_search")
        self.assertAlmostEqual(float(action.value), 65.801)
        self.assertNotIn("理论", action.reason)

    def test_final_amplitude_ambiguous_start_uses_one_millivolt_search(self):
        settings = PeakBalanceSettings(
            target_amplitude=0.2, min_offset_step=0.001,
            final_local_max_distance=0.005,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(65.8, 0.2)
        ambiguous = PeakObservation(False, "00模候选不唯一")
        first = engine.update(ambiguous)
        self.assertEqual(first.state, "startup_offset_search")
        self.assertAlmostEqual(float(first.value), 65.801)
        engine.sync(float(first.value), 0.2)
        second = engine.update(ambiguous)
        self.assertAlmostEqual(float(second.value), 65.799)
        self.assertAlmostEqual(engine.current_amplitude, 0.2)

    def test_final_amplitude_invalid_period_start_uses_one_millivolt_search(self):
        engine = PeakBalanceEngine(PeakBalanceSettings(target_amplitude=0.2))
        engine.start(65.8, 0.2)
        action = engine.update(PeakObservation(
            False, "峰周期与DLC pro扫描频率不一致"
        ))
        self.assertEqual(action.kind, "offset")
        self.assertEqual(action.state, "startup_offset_search")
        self.assertAlmostEqual(float(action.value), 65.801)

    def test_final_amplitude_start_escalates_from_millivolt_to_ten_millivolt_search(self):
        settings = PeakBalanceSettings(
            target_amplitude=0.2,
            final_local_max_distance=0.002,
            max_offset_deviation=0.03,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(65.8, 0.2)
        invalid = PeakObservation(False, "未找到足够的00模穿越峰")
        self.assertEqual(engine.update(invalid).kind, "none")

        values = []
        for _ in range(5):
            action = engine.update(invalid)
            values.append(float(action.value))
            engine.sync(float(action.value), 0.2)

        self.assertEqual(
            [round(value, 6) for value in values],
            [65.801, 65.799, 65.802, 65.798, 65.81],
        )
        self.assertEqual(action.state, "final_local_search")
        self.assertIn("改用0.010 V步长", action.reason)

    def test_invalid_final_grid_candidate_advances_without_restoring_amplitude(self):
        settings = PeakBalanceSettings(target_amplitude=0.2)
        engine = PeakBalanceEngine(settings)
        engine.start(65.8, 0.2)
        first = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.10
        ))
        engine.sync(float(first.value), 0.2)
        next_action = engine.update(PeakObservation(
            False, "00模候选不唯一"
        ))
        self.assertEqual(next_action.kind, "offset")
        self.assertEqual(next_action.state, "final_local_search")
        self.assertAlmostEqual(float(next_action.value), 65.799)
        self.assertAlmostEqual(engine.current_amplitude, 0.2)

    def test_first_final_window_ambiguous_starts_millivolt_search_without_widening(self):
        engine = PeakBalanceEngine(PeakBalanceSettings(target_amplitude=0.2))
        engine.start(64.3, 2.5)
        engine.state = "final_shrink"
        engine.sync(64.3, 0.2)
        engine.reset_after_amplitude_change()

        action = engine.update(PeakObservation(False, "00模候选不唯一"))

        self.assertEqual(action.kind, "offset")
        self.assertEqual(action.state, "final_local_search")
        self.assertAlmostEqual(float(action.value), 64.301)
        self.assertAlmostEqual(engine.current_amplitude, 0.2)
        self.assertIn("保持Amplitude=0.200000 Vpp", action.reason)

    def test_large_final_error_starts_millivolt_search_without_widening(self):
        engine = PeakBalanceEngine(PeakBalanceSettings(target_amplitude=0.2))
        engine.start(64.3, 2.5)
        engine.state = "final_shrink"
        engine.sync(64.3, 0.2)
        engine.reset_after_amplitude_change()

        action = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.6255
        ))

        self.assertEqual(action.kind, "offset")
        self.assertEqual(action.state, "final_local_search")
        self.assertAlmostEqual(float(action.value), 64.301)
        self.assertAlmostEqual(engine.current_amplitude, 0.2)
        self.assertNotEqual(action.kind, "amplitude")

    def test_failed_millivolt_grid_escalates_to_ten_millivolt_offset_search(self):
        settings = PeakBalanceSettings(
            target_amplitude=0.2,
            min_offset_step=0.001,
            final_local_max_distance=0.002,
            final_fallback_step=0.01,
            max_offset_deviation=0.03,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(64.0, 2.5)
        engine.state = "final_shrink"
        engine.sync(64.0, 0.2)
        engine.reset_after_amplitude_change()
        invalid = PeakObservation(False, "峰周期与DLC pro扫描频率不一致")

        values = []
        for _ in range(5):
            action = engine.update(invalid)
            values.append(float(action.value))
            engine.sync(float(action.value), 0.2)

        self.assertEqual(values, [64.001, 63.999, 64.002, 63.998, 64.01])
        self.assertEqual(action.state, "final_local_search")
        self.assertIn("改用0.010 V步长", action.reason)
        self.assertAlmostEqual(engine.current_amplitude, 0.2)

        next_action = engine.update(invalid)
        self.assertAlmostEqual(float(next_action.value), 63.99)
        self.assertNotEqual(next_action.kind, "amplitude")

    def test_default_final_search_uses_exact_requested_two_ranges(self):
        settings = PeakBalanceSettings(target_amplitude=0.2)
        self.assertAlmostEqual(settings.final_local_max_distance, 0.009)
        self.assertAlmostEqual(settings.final_fallback_max_distance, 0.09)
        engine = PeakBalanceEngine(settings)
        engine.start(64.0, 2.5)
        engine.state = "final_shrink"
        engine.sync(64.0, 0.2)
        engine.reset_after_amplitude_change()
        invalid = PeakObservation(False, "峰周期与DLC pro扫描频率不一致")

        actions = []
        for _ in range(36):
            action = engine.update(invalid)
            self.assertEqual(action.kind, "offset")
            actions.append(round(float(action.value) - 64.0, 6))
            engine.sync(float(action.value), 0.2)

        expected_fine = [
            signed
            for index in range(1, 10)
            for signed in (index / 1000.0, -index / 1000.0)
        ]
        expected_fallback = [
            signed
            for index in range(1, 10)
            for signed in (index / 100.0, -index / 100.0)
        ]
        self.assertEqual(actions, expected_fine + expected_fallback)

        stopped = engine.update(invalid)
        self.assertEqual(stopped.kind, "stop")
        self.assertAlmostEqual(engine.current_amplitude, 0.2)
        self.assertIn("±0.090 V", stopped.reason)

    def test_controller_rejects_current_scan_output(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        session._snapshot.sc_output_channel = 51
        session._snapshot.sc_unit = "mA"
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        with self.assertRaisesRegex(RuntimeError, "PC Voltage"):
            controller.start(self.settings, observe_only=True)

    def test_initial_missing_peak_searches_offset_both_sides_without_amplitude(self):
        settings = PeakBalanceSettings(
            offset_step=0.1,
            target_amplitude=0.2,
            max_offset_deviation=0.25,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(66.0, 2.5)
        missing = PeakObservation(False, "未找到足够的00模穿越峰")
        first = engine.update(missing)
        self.assertEqual(first.kind, "none")
        actions = []
        for _ in range(6):
            action = engine.update(missing)
            actions.append(action)
            self.assertEqual(action.kind, "offset")
            engine.sync(float(action.value), 2.5)
        self.assertEqual([float(action.value) for action in actions], [
            67.0, 65.0, 68.0, 64.0, 69.0, 63.0,
        ])
        self.assertAlmostEqual(engine.current_amplitude, 2.5)

    def test_startup_offset_search_enters_fast_centering_as_soon_as_peak_appears(self):
        settings = PeakBalanceSettings(
            offset_step=0.1, max_offset_deviation=0.5,
            target_amplitude=0.2,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(66.0, 2.5)
        missing = PeakObservation(False, "未找到足够的00模穿越峰")
        engine.update(missing)
        search = engine.update(missing)
        engine.sync(float(search.value), 2.5)
        found = engine.update(PeakObservation(
            True, "00模有效", prominence=800.0,
            width_seconds=0.002, balance_error=0.20,
        ))
        self.assertEqual(found.kind, "offset")
        self.assertEqual(found.state, "search_direction_probe")
        self.assertAlmostEqual(engine.current_amplitude, 2.5)
        self.assertAlmostEqual(engine.start_offset, float(search.value))

    def test_initial_ambiguous_peak_uses_symmetric_recovery_without_stopping(self):
        engine = PeakBalanceEngine(self.settings)
        engine.start(0.0, 1.2)
        ambiguous = PeakObservation(False, "00模候选不唯一")
        actions = []
        for _ in range(4):
            action = engine.update(ambiguous)
            actions.append(action)
            self.assertEqual(action.kind, "offset")
            engine.sync(float(action.value), 1.2)
        self.assertEqual([round(float(row.value), 6) for row in actions], [
            0.06, -0.06, 0.12, -0.12,
        ])
        self.assertNotIn("ambiguous", {row.state for row in actions})

    def test_wrong_direction_probe_jumps_from_origin_in_reverse_direction(self):
        engine = PeakBalanceEngine(self.settings)
        engine.start(0.0, 1.2)
        engine.set_offset_step(0.05)
        baseline = PeakObservation(True, "00模有效", balance_error=0.20)
        first = engine.update(baseline)
        self.assertEqual(first.kind, "offset")
        engine.sync(float(first.value), 1.2)
        worse = PeakObservation(True, "00模有效", balance_error=0.23)
        reverse = engine.update(worse)
        self.assertEqual(reverse.kind, "offset")
        expected = -0.8 * 0.5 * 1.2 * 0.20
        self.assertAlmostEqual(float(reverse.value), expected)
        self.assertIn("方向=-", reverse.reason)

    def test_two_neutral_probe_windows_enter_bounded_legacy_fallback(self):
        engine = PeakBalanceEngine(self.settings)
        engine.start(0.0, 1.2)
        engine.set_offset_step(0.05)
        first = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.20
        ))
        engine.sync(float(first.value), 1.2)
        wait = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.198
        ))
        self.assertEqual(wait.kind, "none")
        reverse = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.199
        ))
        self.assertEqual(reverse.kind, "offset")
        self.assertEqual(reverse.state, "probe")
        self.assertLessEqual(abs(float(reverse.value)), 0.5)

    def test_theoretical_jump_is_not_clipped_by_fine_search_deviation(self):
        settings = PeakBalanceSettings(
            max_offset_deviation=0.5, offset_step=0.05,
            prediction_gain=0.8,
            min_offset_step=0.001,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(65.804967, 2.5)
        first = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.708
        ))
        engine.sync(float(first.value), 2.5)
        predicted = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.668
        ))
        # D=2.5/2*0.708=0.885 V, so 0.8D=0.708 V.  This deliberately
        # exceeds the ±0.5 V fine-search window and must still jump directly.
        self.assertAlmostEqual(float(predicted.value), 66.512967)
        self.assertEqual(predicted.state, "search_verify")

        engine.sync(float(predicted.value), 2.5)
        full = engine.update(PeakObservation(False, "00模候选不唯一"))
        self.assertAlmostEqual(float(full.value), 66.689967)
        self.assertEqual(full.state, "search_verify")
        self.assertIn("1.00×完整理论距离", full.reason)

    def test_tracking_drift_rebases_obsolete_historical_best(self):
        engine = PeakBalanceEngine(self.settings)
        engine.start(0.0, 0.2)
        engine.state = "track"
        engine.finalized = True
        engine.best_offset = 0.0
        engine.best_error = 0.001
        engine.sync(0.20, 0.2)
        drifted = PeakObservation(True, "00模有效", balance_error=0.20)
        self.assertEqual(engine.update(drifted).kind, "none")
        action = engine.update(drifted)
        self.assertEqual(action.kind, "offset")
        self.assertAlmostEqual(engine.best_offset, 0.20)
        self.assertGreater(float(action.value), 0.19)

    def test_control_mode_enables_scan_before_analysis(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        session._snapshot.sc_enabled = False
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(self.settings, observe_only=False)
        self.assertEqual(session.scan_writes, [True])
        self.assertTrue(session.snapshot().sc_enabled)
        self.assertTrue(controller.running)
        self.assertIsNotNone(controller.engine)
        self.assertEqual(controller.required_cycles, 2.0)
        controller.stop()

    def test_control_mode_switches_to_ten_hz_with_readback_before_analysis(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(PeakBalanceSettings(), observe_only=False)
        self.assertEqual(session.frequency_writes, [10.0])
        self.assertEqual(controller.scan_frequency, 10.0)
        self.assertTrue(controller.running)
        self.assertIsNotNone(controller.engine)
        controller.stop()

    def test_control_mode_initializes_amplitude_to_two_point_five_before_analysis(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        session._snapshot.sc_amplitude = 0.2
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(PeakBalanceSettings(), observe_only=False)
        self.assertEqual(session.amplitude_writes, [2.5])
        self.assertAlmostEqual(controller.engine.current_amplitude, 2.5)
        self.assertAlmostEqual(controller.start_amplitude, 2.5)
        controller.restore_start_values()
        self.assertEqual(session.amplitude_writes, [2.5, 0.2])

    def test_quantized_frequency_readback_is_accepted(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        session._snapshot.sc_frequency = 0.500052

        def quantized_frequency(value):
            session.frequency_writes.append(float(value))
            session._snapshot.sc_frequency = float(value) + 0.00005
            session.write_snapshot_changed.emit(session._snapshot)

        session.set_scan_frequency = quantized_frequency
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(
            PeakBalanceSettings(search_frequency_hz=5.0), observe_only=False
        )
        self.assertEqual(session.frequency_writes, [5.0])
        self.assertAlmostEqual(controller.scan_frequency, 5.00005)
        self.assertTrue(controller.running)
        self.assertIsNotNone(controller.engine)
        controller.stop()

    def test_frequency_already_within_device_resolution_is_not_rewritten(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        session._snapshot.sc_frequency = 0.999947
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(
            PeakBalanceSettings(search_frequency_hz=1.0), observe_only=False
        )
        self.assertEqual(session.frequency_writes, [])
        self.assertAlmostEqual(controller.scan_frequency, 0.999947)
        self.assertTrue(controller.running)
        controller.stop()

    def test_material_frequency_readback_error_still_blocks_start(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()

        def rejected_frequency(value):
            session.frequency_writes.append(float(value))
            session._snapshot.sc_frequency = float(value) + 0.02
            session.write_snapshot_changed.emit(session._snapshot)

        session.set_scan_frequency = rejected_frequency
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(
            PeakBalanceSettings(search_frequency_hz=5.0), observe_only=False
        )
        self.assertFalse(controller.running)
        self.assertIsNone(controller.engine)

    def test_restore_start_values_also_restores_original_frequency(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(PeakBalanceSettings(), observe_only=False)
        controller.restore_start_values()
        self.assertEqual(session.frequency_writes, [10.0, 1.0])
        self.assertEqual(session.amplitude_writes, [2.5, 1.2])
        self.assertAlmostEqual(session.snapshot().sc_frequency, 1.0)

    def test_observe_mode_does_not_auto_enable_scan(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        session._snapshot.sc_enabled = False
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        with self.assertRaisesRegex(RuntimeError, "观察模式禁止写入"):
            controller.start(self.settings, observe_only=True)
        self.assertEqual(session.scan_writes, [])

    def test_failed_scan_enable_never_starts_offset_control(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        session._snapshot.sc_enabled = False

        def reject_scan(_enabled):
            session.scan_writes.append(True)
            session.write_snapshot_changed.emit(session._snapshot)

        session.set_scan_enabled = reject_scan
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(self.settings, observe_only=False)
        self.assertFalse(controller.running)
        self.assertEqual(session.offset_writes, [])
        self.assertEqual(session.amplitude_writes, [])

    def test_write_discards_one_settle_cycle_before_two_cycle_window(self):
        cavity = VirtualCavity()
        ring = _FrameRing(_shifted_history(cavity, 0))
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(ring, session, lambda: True)
        controller.start(self.settings, observe_only=False)
        controller._submit_action(SimpleNamespace(
            kind="offset", value=0.05, reason="测试写入", state="center"
        ))
        self.assertTrue(controller.settle_pending)
        self.assertEqual(controller.settle_kind, "Offset")
        ring.frame = _shifted_history(cavity, 20_000)
        controller.settle_until = 0.0
        controller.available_after = 0.0
        controller._tick()
        self.assertFalse(controller.settle_pending)
        self.assertEqual(controller.required_cycles, 2.0)
        self.assertEqual(controller.gate_bin, int(ring.frame.bin_indices[-1]))
        controller.stop()

    def test_automatic_action_log_contains_balance_evidence(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(self.settings, observe_only=False)
        messages = []
        controller.log_message.connect(messages.append)
        observation = PeakObservation(
            True, "00模有效", delta_t1=0.21, delta_t2=0.29,
            balance_error=0.16,
        )
        controller._log_decision(observation, SimpleNamespace(
            kind="offset", value=0.05, reason="方向试探", state="probe"
        ))
        text = "\n".join(messages)
        self.assertIn("不均匀度=16.00%", text)
        self.assertIn("Δt1=0.210000s", text)
        self.assertIn("方向试探", text)
        controller.stop()

    def test_observe_mode_makes_shrink_the_required_next_step(self):
        cavity = VirtualCavity()
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(
            _FrameRing(_shifted_history(cavity, 0)), session, lambda: True
        )
        controller.start(self.settings, observe_only=True)
        valid = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.01,
        )
        for _ in range(self.settings.stable_windows):
            controller._observe(valid)
        self.assertIn("下一步进入缩幅", controller.manual_advice)
        self.assertIn("一步进入最终幅度", controller.manual_advice)
        controller.stop()

    def test_control_mode_waits_for_independent_stage_windows_then_writes(self):
        cavity = VirtualCavity()
        ring = _FrameRing(_shifted_history(cavity, 0))
        session = _FakeDlcSession()
        controller = AdcPeakBalanceController(ring, session, lambda: True)
        controller.start(self.settings, observe_only=False)

        ring.frame = _shifted_history(cavity, 10_000)
        controller.available_after = 0.0
        controller._tick()
        self.assertEqual(session.offset_writes, [])
        self.assertEqual(session.amplitude_writes, [])
        ring.frame = _shifted_history(cavity, 20_000)
        controller.available_after = 0.0
        controller._tick()
        self.assertEqual(session.offset_writes, [])
        self.assertEqual(len(session.amplitude_writes), 1)
        self.assertAlmostEqual(session.amplitude_writes[0], 0.2)
        controller.stop()

    def test_control_mode_executes_direct_final_amplitude_shrink(self):
        cavity = VirtualCavity()
        ring = _FrameRing(_shifted_history(cavity, 0))
        session = _FakeDlcSession()
        session._snapshot.sc_amplitude = 5.0
        controller = AdcPeakBalanceController(ring, session, lambda: True)
        controller.start(PeakBalanceSettings(
            min_prominence_codes=40,
            max_offset_deviation=0.5,
            offset_step=0.03,
            search_frequency_hz=1.0,
            initial_search_amplitude=5.0,
        ), observe_only=False)
        controller.engine.state = "center"
        ring.frame = cavity.history(0.0, 5.0)
        ring.frame.bin_indices += 10_000
        for _ in range(2):
            controller.available_after = 0.0
            controller._tick()
            ring.frame.bin_indices += 10_000
        self.assertEqual(session.offset_writes, [])
        self.assertEqual(len(session.amplitude_writes), 1)
        self.assertAlmostEqual(session.amplitude_writes[0], 0.2)
        self.assertFalse(controller.pending_write)
        self.assertAlmostEqual(controller.engine.current_amplitude, 0.2)
        self.assertGreater(controller.available_after, 0.0)
        controller.stop()


if __name__ == "__main__":
    unittest.main()
