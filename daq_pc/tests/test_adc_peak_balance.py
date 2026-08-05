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
        self.assertIn("0.050000", controller.manual_advice)
        self.assertIn("正向试探", controller.manual_advice)

        controller.engine.sync(0.05, 1.2)
        improved = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.13,
        )
        controller._observe(improved)
        self.assertIn("继续同方向", controller.manual_advice)
        self.assertIn("0.100000", controller.manual_advice)

        controller.engine.sync(0.10, 1.2)
        worsened = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.16,
        )
        controller._observe(worsened)
        self.assertIn("反向并减小步长", controller.manual_advice)
        self.assertIn("0.075000", controller.manual_advice)
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
            PeakBalanceSettings(target_amplitude=0.2),
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

    def test_configurable_amplitude_stages_select_all_control_limits(self):
        engine = PeakBalanceEngine(self.settings)
        engine.start(0.0, 4.0)
        expected = (
            (4.0, "宽扫", 0.20, 0.1, 0.70, 1),
            (1.5, "中扫", 0.12, 0.05, 0.75, 2),
            (0.75, "细扫", 0.08, 0.01, 0.75, 2),
            (0.4, "窄扫", 0.06, 0.001, 0.80, 2),
            (0.2, "最终验收", 0.05, 0.001, None, 3),
        )
        for amplitude, name, tolerance, step, shrink, windows in expected:
            engine.sync(0.0, amplitude)
            stage = engine.current_stage
            self.assertEqual(stage.name, name)
            self.assertAlmostEqual(stage.balance_tolerance, tolerance)
            self.assertAlmostEqual(stage.offset_step, step)
            self.assertEqual(stage.shrink_ratio, shrink)
            self.assertEqual(stage.stable_windows, windows)

    def test_each_stage_shrinks_after_its_own_independent_window_count(self):
        settings = PeakBalanceSettings(target_amplitude=0.2)
        engine = PeakBalanceEngine(settings)
        engine.start(0.0, 5.0)
        valid = PeakObservation(
            True, "00模有效", prominence=800.0, width_seconds=0.002,
            snr=20.0, balance_error=0.01,
        )
        for amplitude, windows, target in (
            (5.0, 1, 3.5), (1.5, 2, 1.125),
            (0.75, 2, 0.5625), (0.4, 2, 0.32),
        ):
            engine.sync(0.0, amplitude)
            engine.state = "center"
            engine.stable_count = 0
            for _ in range(windows):
                action = engine.update(valid)
            self.assertEqual(action.kind, "amplitude")
            self.assertAlmostEqual(float(action.value), target)

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

    def test_initial_missing_peak_expands_from_device_start_amplitude(self):
        settings = PeakBalanceSettings(
            offset_step=0.1,
            target_amplitude=0.2,
            max_search_amplitude_factor=2.0,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(0.0, 1.0)
        missing = PeakObservation(False, "未找到足够的00模穿越峰")
        first = engine.update(missing)
        self.assertEqual(first.kind, "none")
        second = engine.update(missing)
        self.assertEqual(second.kind, "amplitude")
        self.assertAlmostEqual(second.value, 1.25)
        engine.sync(0.0, float(second.value))
        engine.update(missing)
        fourth = engine.update(missing)
        self.assertEqual(fourth.kind, "amplitude")
        self.assertLessEqual(float(fourth.value), 2.0)

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

    def test_wrong_offset_trial_restores_best_and_reverses(self):
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
        self.assertLess(float(reverse.value), engine.best_offset)
        self.assertIn("反向", reverse.reason)

    def test_two_neutral_windows_reverse_against_fixed_reference(self):
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
        self.assertLess(float(reverse.value), engine.best_offset)

    def test_single_offset_boundary_reverses_from_best(self):
        settings = PeakBalanceSettings(
            max_offset_deviation=0.05, offset_step=0.05,
            min_offset_step=0.001,
        )
        engine = PeakBalanceEngine(settings)
        engine.start(0.0, 1.2)
        engine.set_offset_step(0.05)
        first = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.20
        ))
        engine.sync(float(first.value), 1.2)
        boundary_recovery = engine.update(PeakObservation(
            True, "00模有效", balance_error=0.15
        ))
        self.assertEqual(boundary_recovery.kind, "offset")
        self.assertLess(float(boundary_recovery.value), engine.best_offset)
        self.assertIn("安全边界", boundary_recovery.reason)

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
        self.assertEqual(controller.required_cycles, 4.0)
        controller.stop()

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

    def test_write_discards_settle_cycles_before_four_cycle_window(self):
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
        self.assertEqual(controller.required_cycles, 4.0)
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
        self.assertIn("直至最终目标", controller.manual_advice)
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
        self.assertAlmostEqual(session.amplitude_writes[0], 0.9)
        controller.stop()

    def test_control_mode_executes_configured_coarse_amplitude_shrink(self):
        cavity = VirtualCavity()
        ring = _FrameRing(_shifted_history(cavity, 0))
        session = _FakeDlcSession()
        session._snapshot.sc_amplitude = 5.0
        controller = AdcPeakBalanceController(ring, session, lambda: True)
        controller.start(self.settings, observe_only=False)
        controller.engine.state = "center"
        ring.frame = cavity.history(0.0, 5.0)
        ring.frame.bin_indices += 10_000
        controller.available_after = 0.0
        controller._tick()
        self.assertEqual(session.offset_writes, [])
        self.assertEqual(len(session.amplitude_writes), 1)
        self.assertAlmostEqual(session.amplitude_writes[0], 3.5)
        self.assertFalse(controller.pending_write)
        self.assertAlmostEqual(controller.engine.current_amplitude, 3.5)
        self.assertGreater(controller.available_after, 0.0)
        controller.stop()


if __name__ == "__main__":
    unittest.main()
