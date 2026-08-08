from __future__ import annotations

import csv
import os
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import h5py
from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import (
    QAbstractSpinBox, QApplication, QFileDialog, QLabel, QMessageBox,
)

from daq_pc.unified_daq_gui import (
    AcquisitionStarter,
    CsvRecorder,
    EnvelopePlot,
    Hdf5Recorder,
    MainWindow,
    ScopeWindow,
    ad9269_config_channel_swap,
)
from daq_pc.dlcpro_settings_dialog import (
    DlcProSettingsDialog,
    DlcScanSession,
    RecordingOptionsDialog,
)
from daq_pc.scan_control_window import (
    DlcScanControlWindow, PositiveFrequencySpinBox,
)
from dlcpro_service import ConnectionSettings
from daq_pc.daq_udp_dual import DualSampleRingBuffer
from daq_pc.daq_protocol_v2 import CONFIG_CHANNEL_SWAP, Command
from daq_pc.adc_peak_balance_window import ParameterHelpDialog


class FakeFpgaProgrammer(QObject):
    progress = Signal(int, str)
    output = Signal(str)
    program_succeeded = Signal(str)
    program_failed = Signal(str)
    finished = Signal()

    def __init__(self, _vivado, _script, bitstream, parent=None):
        super().__init__(parent)
        self.bitstream = Path(bitstream)
        self.running = False

    def start(self):
        self.running = True
        self.progress.emit(60, "正在配置FPGA")
        self.program_succeeded.emit(str(self.bitstream))
        self.running = False
        self.finished.emit()

    def isRunning(self):
        return self.running

    def cancel(self):
        self.running = False


class UnifiedGuiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.settings = QSettings(
            os.path.join(self.tempdir.name, "gui.ini"),
            QSettings.IniFormat,
        )
        self.settings.clear()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_final_gui_is_ad9269_only_and_network_rates_are_bounded(self):
        window = MainWindow(preset_model=0, settings=self.settings)
        self.assertEqual(window.board_ip.text(), "192.168.20.2")
        self.assertEqual(window.window_samples.value(), 2_000)
        self.assertEqual(window.model.currentData(), 1)
        self.assertFalse(window.model.isEnabled())
        self.assertEqual(window.rate.count(), 3)
        self.assertEqual(window.rate.currentData(), 10_000_000)
        self.assertEqual(
            [window.rate.itemData(index) for index in range(window.rate.count())],
            [5_000_000, 10_000_000, 20_000_000],
        )
        self.assertFalse(window.jumbo.isChecked())
        self.assertTrue(window.channel_swap.isEnabled())
        self.assertEqual(
            [
                window.record_content.itemData(index)
                for index in range(window.record_content.count())
            ],
            [
                RecordingOptionsDialog.WAVEFORM_ONLY,
                RecordingOptionsDialog.WITH_DLCPRO,
            ],
        )
        self.assertTrue(window.record_content.isEnabled())
        self.assertFalse(hasattr(window, "dlc_settings_button"))
        self.assertTrue(hasattr(window, "dlc_status_label"))
        self.assertIsNot(window.scope_a_button, window.scope_b_button)
        self.assertEqual(window.scope_a_button.text(), "打开通道 A")
        self.assertEqual(window.scope_b_button.text(), "打开通道 B")
        self.assertGreaterEqual(window.scope_a_button.minimumWidth(), 150)
        self.assertGreaterEqual(window.scope_b_button.minimumWidth(), 150)
        self.assertLessEqual(window.record_path_button.maximumWidth(), 220)
        record_path_index = window.action_card.layout().indexOf(
            window.record_path_button
        )
        record_button_index = window.action_card.layout().indexOf(
            window.record_button
        )
        scope_b_index = window.action_card.layout().indexOf(
            window.scope_b_button
        )
        self.assertEqual(
            window.action_card.layout().getItemPosition(record_path_index)[2:],
            (1, 1),
        )
        self.assertEqual(
            window.action_card.layout().getItemPosition(record_button_index)[1],
            window.action_card.layout().getItemPosition(scope_b_index)[1],
        )
        self.assertTrue(window.fpga_card.isAncestorOf(window.fpga_select_button))
        self.assertTrue(window.fpga_card.isAncestorOf(window.fpga_program_button))
        self.assertFalse(window.action_card.isAncestorOf(window.fpga_select_button))
        self.assertGreaterEqual(window.channel_swap.minimumWidth(), 230)
        self.assertGreaterEqual(window.jumbo.minimumWidth(), 390)
        window.close()

    def test_csv_writer_uses_frame_data_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "capture.csv")
            recorder = CsvRecorder(path)
            recorder.append((1.5, 7, 5_000_000,
                             np.array([1, 2], np.int16),
                             np.array([3, 4], np.int16),
                             np.array([True, False])))
            recorder.close()
            with open(path, newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[1][1:3], ["7", "5000000"])

    def test_high_speed_recorder_spools_complete_udp_packets(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = os.path.join(directory, "capture.plraw")
            output = os.path.join(directory, "capture.csv")
            recorder = CsvRecorder(spool)
            pairs_per_packet = 64
            for packet_index in range(100):
                a = np.arange(pairs_per_packet, dtype=np.int16) + packet_index
                b = -a
                payload = np.column_stack((a, b)).astype("<i2").tobytes()
                packet = SimpleNamespace(
                    sample_pair_count=pairs_per_packet,
                    channel_mask=3,
                    payload=memoryview(payload),
                    stream_id=9,
                    sample_rate_hz=20_000_000,
                    first_sample_pair=10_000 + packet_index * pairs_per_packet,
                )
                self.assertTrue(recorder.append_packet(1.5, packet))
            recorder.close(finalize=False)
            self.assertEqual(recorder.dropped_samples, 0)
            self.assertEqual(recorder.written_samples, 6_400)
            recorder.export_csv(output)
            with open(output, newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(len(rows), 6_401)
            self.assertEqual(rows[1][3], "10000")
            self.assertEqual(rows[-1][3], str(10_000 + 6_399))

    def test_single_channel_recording_halves_payload_and_csv_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = os.path.join(directory, "capture_a.plraw")
            output = os.path.join(directory, "capture_a.csv")
            recorder = CsvRecorder(spool, channel_mask=1)
            a = np.array([10, 20, 30], dtype=np.int16)
            b = np.array([-10, -20, -30], dtype=np.int16)
            packet = SimpleNamespace(
                sample_pair_count=3,
                channel_mask=3,
                payload=np.column_stack((a, b)).astype("<i2").tobytes(),
                stream_id=2,
                sample_rate_hz=5_000_000,
                first_sample_pair=100,
            )
            self.assertTrue(recorder.append_packet(1.0, packet))
            recorder.close(finalize=False)
            recorder.export_csv(output)
            with open(output, newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(
                rows[0],
                ["host_time_s", "stream_id", "sample_rate_hz",
                 "sample_offset", "channel_a", "valid"],
            )
            self.assertEqual([row[4] for row in rows[1:]], ["10", "20", "30"])

    def test_combined_recording_can_export_separate_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            spool = os.path.join(directory, "capture.plraw")
            output_a = os.path.join(directory, "capture_A.csv")
            output_b = os.path.join(directory, "capture_B.csv")
            recorder = CsvRecorder(spool, channel_mask=3)
            recorder.append((
                1.0, 3, 5_000_000,
                np.array([1, 2], np.int16),
                np.array([7, 8], np.int16),
                np.array([True, True]),
            ))
            recorder.close(finalize=False)
            recorder.export_csv(output_a, export_mask=1)
            recorder.export_csv(output_b, export_mask=2)
            with open(output_a, newline="", encoding="utf-8-sig") as handle:
                rows_a = list(csv.reader(handle))
            with open(output_b, newline="", encoding="utf-8-sig") as handle:
                rows_b = list(csv.reader(handle))
            self.assertEqual(rows_a[0][-2], "channel_a")
            self.assertEqual(rows_b[0][-2], "channel_b")
            self.assertEqual([row[-2] for row in rows_a[1:]], ["1", "2"])
            self.assertEqual([row[-2] for row in rows_b[1:]], ["7", "8"])

    def test_hdf5_recorder_saves_voltage_indices_features_and_dlc_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = os.path.join(directory, "capture.h5")
            snapshot = SimpleNamespace(
                sc_enabled=True,
                sc_offset=1.25,
                sc_amplitude=0.5,
                sc_frequency=12.0,
                sc_output_channel=50,
                sc_signal_type=1,
                sc_unit="V",
            )
            recorder = Hdf5Recorder(
                destination,
                channel="B",
                record_rate_hz=1_000_000,
                snapshot_provider=lambda: snapshot,
                include_dlcpro=True,
            )
            a = np.arange(20, dtype=np.int16)
            b = -a
            packet = SimpleNamespace(
                sample_pair_count=20,
                channel_mask=3,
                payload=np.column_stack((a, b)).astype("<i2").tobytes(),
                stream_id=3,
                sample_rate_hz=5_000_000,
                first_sample_pair=100,
            )
            self.assertTrue(recorder.append_packet(10.0, packet))
            recorder.update_quality({
                "network_packet_loss": 2,
                "pl_sample_gap": 7,
                "index_gap_events": 1,
            })
            recorder.close()
            with h5py.File(destination, "r") as handle:
                np.testing.assert_array_equal(
                    handle["samples/sample_index"][:],
                    np.array([100, 105, 110, 115], dtype=np.uint64),
                )
                np.testing.assert_array_equal(
                    handle["samples/raw_code"][:],
                    np.array([0, -5, -10, -15], dtype=np.int16),
                )
                self.assertEqual(handle["features/peak_to_peak_v"].shape, (1,))
                self.assertEqual(handle["dlcpro/scan_offset"][0], 1.25)
                self.assertEqual(handle["dlcpro/scan_amplitude"][0], 0.5)
                self.assertEqual(handle["dlcpro/scan_unit"].asstr()[0], "V")
                self.assertEqual(
                    handle["quality"].attrs["network_packets_lost"], 2
                )
                self.assertTrue(handle.attrs["dlcpro_metadata_available"])
                self.assertTrue(handle.attrs["dlcpro_metadata_complete"])

    def test_waveform_only_hdf5_has_no_dlcpro_group(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = os.path.join(directory, "waveform_only.h5")
            recorder = Hdf5Recorder(destination, channel="A")
            packet = SimpleNamespace(
                sample_pair_count=2,
                channel_mask=3,
                payload=np.array([[1, 2], [3, 4]], dtype="<i2").tobytes(),
                stream_id=1,
                sample_rate_hz=5_000_000,
                first_sample_pair=0,
            )
            recorder.append_packet(1.0, packet)
            recorder.close()
            with h5py.File(destination, "r") as handle:
                self.assertEqual(handle.attrs["recording_mode"], "waveform_only")
                self.assertFalse(handle.attrs["dlcpro_metadata_enabled"])
                self.assertNotIn("dlcpro", handle)

    def test_hdf5_reports_gaps_from_the_recorded_sample_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = os.path.join(directory, "gaps.h5")
            recorder = Hdf5Recorder(
                destination, channel="A", record_rate_hz=100_000
            )
            payload = np.zeros((100, 2), dtype="<i2").tobytes()
            for first_sample in (0, 100, 350):
                self.assertTrue(recorder.append_packet(1.0, SimpleNamespace(
                    sample_pair_count=100,
                    channel_mask=3,
                    payload=payload,
                    stream_id=1,
                    sample_rate_hz=1_000_000,
                    first_sample_pair=first_sample,
                )))
            recorder.close()
            with h5py.File(destination, "r") as handle:
                quality = handle["quality"].attrs
                self.assertEqual(quality["recorded_index_gap_events"], 1)
                self.assertEqual(quality["recorded_index_missing_samples"], 150)

    def test_dlcpro_interruption_marks_combined_file_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = os.path.join(directory, "interrupted.h5")
            snapshot = SimpleNamespace(
                sc_enabled=True, sc_offset=0.0, sc_amplitude=1.0,
                sc_frequency=10.0, sc_output_channel=50,
                sc_signal_type=0, sc_unit="V",
            )
            recorder = Hdf5Recorder(
                destination,
                channel="A",
                snapshot_provider=lambda: snapshot,
                include_dlcpro=True,
            )
            packet = SimpleNamespace(
                sample_pair_count=2,
                channel_mask=3,
                payload=np.array([[1, 2], [3, 4]], dtype="<i2").tobytes(),
                stream_id=1,
                sample_rate_hz=5_000_000,
                first_sample_pair=0,
            )
            recorder.append_packet(1.0, packet)
            recorder.mark_dlcpro_incomplete("连接中断")
            recorder.close()
            with h5py.File(destination, "r") as handle:
                self.assertFalse(handle.attrs["dlcpro_metadata_complete"])
                self.assertEqual(
                    handle.attrs["dlcpro_metadata_interruption"], "连接中断"
                )

    def test_standalone_dlc_session_connects_and_writes_scan_values(self):
        snapshot = SimpleNamespace(
            sc_enabled=True, sc_offset=0.0, sc_amplitude=1.0,
            sc_frequency=10.0, sc_output_channel=50,
            sc_signal_type=0, sc_unit="V",
        )

        class FakeService:
            def __init__(self):
                self.is_connected = False
                self.offset_writes = []
                self.amplitude_writes = []
                self.enabled_writes = []
                self.frequency_writes = []
                self.output_writes = []
                self.shape_writes = []

            def connect(self, settings):
                self.is_connected = True
                self.settings = settings
                return snapshot

            def disconnect(self):
                self.is_connected = False

            def set_sc_offset(self, value):
                self.offset_writes.append(value)
                snapshot.sc_offset = value
                return snapshot

            def set_sc_amplitude(self, value):
                self.amplitude_writes.append(value)
                snapshot.sc_amplitude = value
                return snapshot

            def set_sc_enabled(self, value):
                self.enabled_writes.append(bool(value))
                snapshot.sc_enabled = bool(value)
                return snapshot

            def set_sc_frequency(self, value):
                self.frequency_writes.append(float(value))
                snapshot.sc_frequency = float(value)
                return snapshot

            def set_sc_output_channel(self, value):
                self.output_writes.append(int(value))
                snapshot.sc_output_channel = int(value)
                return snapshot

            def set_sc_signal_type(self, value):
                self.shape_writes.append(int(value))
                snapshot.sc_signal_type = int(value)
                return snapshot

            def read_snapshot(self, _request):
                return snapshot

            @staticmethod
            def format_error(exc):
                return str(exc)

        service = FakeService()
        session = DlcScanSession(service, owns_service=True)
        updates = QSignalSpy(session.snapshot_changed)
        session.connect_device(ConnectionSettings("network", "192.168.10.2"))
        self.assertTrue(updates.wait(2000))
        self.assertTrue(session.is_connected)
        self.assertEqual(service.settings.mode, "network")
        session.set_scan_offset(2.5)
        self.assertTrue(updates.wait(2000))
        session.set_scan_amplitude(0.25)
        self.assertTrue(updates.wait(2000))
        session.set_scan_enabled(False)
        self.assertTrue(updates.wait(2000))
        session.set_scan_frequency(0.5)
        self.assertTrue(updates.wait(2000))
        session.set_scan_output_channel(51)
        self.assertTrue(updates.wait(2000))
        session.set_scan_signal_type(1)
        self.assertTrue(updates.wait(2000))
        self.assertEqual(service.offset_writes, [2.5])
        self.assertEqual(service.amplitude_writes, [0.25])
        self.assertEqual(service.enabled_writes, [False])
        self.assertEqual(service.frequency_writes, [0.5])
        self.assertEqual(service.output_writes, [51])
        self.assertEqual(service.shape_writes, [1])
        session.shutdown()

    def test_scan_control_popup_uses_shared_session_and_adc_style(self):
        snapshot = SimpleNamespace(
            sc_enabled=True, sc_offset=0.2, sc_amplitude=1.5,
            sc_frequency=1.0, sc_output_channel=50,
            sc_signal_type=0, sc_unit="V",
        )

        class FakeService:
            is_connected = True
            shape_writes = []

            @staticmethod
            def format_error(exc):
                return str(exc)

            @staticmethod
            def read_snapshot(_request):
                return snapshot

            @staticmethod
            def set_sc_offset(value):
                snapshot.sc_offset = float(value)
                return snapshot

            @classmethod
            def set_sc_signal_type(cls, value):
                cls.shape_writes.append(int(value))
                snapshot.sc_signal_type = int(value)
                return snapshot

            @staticmethod
            def disconnect():
                return None

        session = DlcScanSession(FakeService(), owns_service=True)
        session.poll_timer.stop()
        popup = DlcScanControlWindow(session, self.settings)
        popup._render_snapshot(snapshot)
        self.assertTrue(session.pool.waitForDone(2000))
        self.app.processEvents()
        self.assertIn("background: #f3f6fa", popup.styleSheet())
        self.assertEqual(popup.amplitude.suffix(), " V pp")
        self.assertEqual(popup.offset.suffix(), " V")
        self.assertEqual(popup.frequency.value(), 1.0)
        self.assertTrue(popup.enable_button.isChecked())
        self.assertEqual(popup.shape.currentData(), 1)
        self.assertFalse(popup.shape.isEnabled())
        self.assertEqual(FakeService.shape_writes, [1])
        popup.set_scan_edit_locked(True)
        self.assertFalse(popup.offset.isEnabled())
        popup.set_scan_edit_locked(False)
        self.assertTrue(popup.offset.isEnabled())
        popup.close()
        session.shutdown()

    def test_scan_frequency_coarse_down_step_never_collapses_to_zero(self):
        spin = PositiveFrequencySpinBox()
        spin.setRange(0.001, 1_000_000.0)
        spin.setSingleStep(1.0)
        spin.setValue(0.5)
        spin.stepBy(-1)
        self.assertEqual(spin.value(), 0.5)
        spin.stepBy(1)
        self.assertEqual(spin.value(), 1.5)
        QApplication.processEvents()
        spin.deleteLater()
        QApplication.processEvents()

    def test_constant_adc_code_gets_visible_vertical_padding(self):
        minimum = np.full(32, 221, dtype=np.int16)
        maximum = minimum.copy()
        valid = np.ones(32, dtype=bool)
        low, high = EnvelopePlot._display_bounds(minimum, maximum, valid)
        self.assertEqual((low, high), (205.0, 237.0))

    def test_auto_range_uses_true_extrema_and_preserves_single_spike(self):
        signal = np.linspace(-0.0002, 0.0002, 1000)
        signal[-1] = 5.0
        valid = np.ones(signal.size, dtype=bool)
        low, high = EnvelopePlot._display_bounds(
            signal,
            signal,
            valid,
            minimum_half_span=16.0 * 5.0 / 32768.0,
        )
        self.assertLessEqual(low, -0.0002)
        self.assertGreaterEqual(high, 5.0)

    def test_auto_range_matches_reference_formula_and_y_multiplier(self):
        minimum = np.array([0.0, 10.0])
        maximum = np.array([90.0, 100.0])
        valid = np.ones(2, dtype=bool)
        low, high = EnvelopePlot._display_bounds(
            minimum, maximum, valid, minimum_half_span=16.0,
            vertical_scale=2.0,
        )
        self.assertAlmostEqual(low, -60.0)
        self.assertAlmostEqual(high, 160.0)

    def test_auto_range_expands_immediately_and_contracts_smoothly(self):
        plot = EnvelopePlot("#22d3ee")
        self.assertEqual(
            plot._stabilize_auto_bounds((-10.0, 10.0), now=0.0),
            (-10.0, 10.0),
        )
        self.assertEqual(
            plot._stabilize_auto_bounds((-20.0, 20.0), now=0.1),
            (-20.0, 20.0),
        )
        contracted = plot._stabilize_auto_bounds((-5.0, 5.0), now=0.2)
        self.assertLess(contracted[0], -5.0)
        self.assertGreater(contracted[1], 5.0)
        plot.close()

    def test_scope_axes_use_voltage_and_time_divisions(self):
        scope = ScopeWindow("A", "#22d3ee")
        scope.timebase.setCurrentIndex(scope.timebase.findData(200e-3))
        scope._apply_display()
        self.assertEqual(scope.plot.axis_unit, "V")
        self.assertAlmostEqual(scope.plot.seconds_per_div, 200e-3)
        self.assertEqual(EnvelopePlot._time_axis_scale(200e-3), (1e3, "ms"))
        self.assertGreater(scope.plot._plot_rect().left(), 0)
        self.assertLess(scope.plot._plot_rect().bottom(), scope.plot.height())
        scope.close()

    def test_default_channel_mapping_corrects_physical_edges(self):
        self.assertEqual(ad9269_config_channel_swap(False), CONFIG_CHANNEL_SWAP)
        self.assertEqual(ad9269_config_channel_swap(True), 0)

    def test_acquisition_start_handshake_runs_in_worker(self):
        class FakeControl:
            adc_model = 0

            def __init__(self):
                self.calls = []

            def request(self, command, **kwargs):
                self.calls.append((command, kwargs))
                if command == Command.STATUS:
                    return SimpleNamespace(daq_state=3, stream_id=11)
                return SimpleNamespace()

        control = FakeControl()
        worker = AcquisitionStarter(
            control, sample_rate_hz=20_000_000, flags=7,
            jumbo_enabled=True, previous_stream=10,
        )
        succeeded = QSignalSpy(worker.succeeded)
        failed = QSignalSpy(worker.failed)
        worker.start()
        self.assertTrue(worker.wait(2_000))
        self.app.processEvents()
        self.assertEqual(succeeded.count(), 1)
        self.assertEqual(failed.count(), 0)
        self.assertEqual(control.adc_model, 1)
        self.assertEqual(
            [command for command, _kwargs in control.calls],
            [Command.STOP, Command.CONFIG, Command.START, Command.STATUS],
        )
        self.assertTrue(control.calls[1][1]["jumbo_enable"])

    def test_ten_msps_starts_with_jumbo_frames_unchecked(self):
        self.settings.setValue("main/rate", 10_000_000)
        self.settings.setValue("main/jumbo", True)
        with mock.patch(
            "daq_pc.unified_daq_gui.windows_jumbo_status",
            side_effect=AssertionError("must not probe jumbo mode while opening"),
        ):
            window = MainWindow(preset_model=1, settings=self.settings)
        self.assertFalse(window.jumbo.isChecked())
        self.assertIsNone(self.settings.value("main/jumbo"))
        window.close()

    def test_selecting_twenty_msps_enables_jumbo_frames(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        window.jumbo.setChecked(False)
        window.rate.setCurrentIndex(window.rate.findData(20_000_000))
        self.assertTrue(window.jumbo.isChecked())
        window.close()

    def test_startup_ignores_saved_twenty_msps_and_disables_jumbo(self):
        self.settings.setValue("main/rate", 20_000_000)
        self.settings.setValue("main/jumbo", True)
        with mock.patch(
            "daq_pc.unified_daq_gui.windows_jumbo_status",
            side_effect=AssertionError("must not probe jumbo mode while opening"),
        ):
            window = MainWindow(preset_model=1, settings=self.settings)
        self.assertEqual(window.rate.currentData(), 10_000_000)
        self.assertFalse(window.jumbo.isChecked())
        self.assertIsNone(self.settings.value("main/rate"))
        self.assertIsNone(self.settings.value("main/jumbo"))
        window.close()

    def test_scope_controls_are_lightweight_and_model_aware(self):
        scope = ScopeWindow("A", "#22d3ee")
        self.assertEqual(scope.refresh_fps, 30)
        self.assertEqual(
            [scope.fps.itemData(index) for index in range(scope.fps.count())],
            [10, 20, 30],
        )
        self.assertEqual(scope.required_samples(5_000_000), 2_500)
        self.assertEqual(scope.units.currentData(), "module")
        self.assertFalse(scope.smoothing.isChecked())
        self.assertFalse(scope.plot.smoothing)
        scope.configure_model(1)
        self.assertEqual(scope.units.currentData(), "module")
        self.assertEqual(scope.y_range.currentData(), "auto")
        self.assertGreaterEqual(scope.y_range.findData(5.0), 0)
        self.assertGreaterEqual(scope.y_range.findData(0.0001), 0)
        self.assertEqual(scope.control_labels["range"].text(), "电压范围")
        one_volt = scope.y_range.findData(1.0)
        scope.y_range.setCurrentIndex(one_volt)
        self.assertEqual(scope.plot.fixed_bounds, (-1.0, 1.0))
        scope.vertical_scale.setValue(2.0)
        self.assertEqual(scope.plot.fixed_bounds, (-2.0, 2.0))
        self.assertGreaterEqual(scope.timebase.findData(10.0), 0)
        self.assertEqual(scope.vertical_scale.minimum(), 0.001)
        self.assertEqual(scope.vertical_scale.maximum(), 8.0)
        scope.units.setCurrentIndex(scope.units.findData("raw"))
        self.assertGreater(scope.y_range.count(), 2)
        scope.fps.setCurrentIndex(scope.fps.findData(10))
        scope.scroll_speed.setCurrentIndex(scope.scroll_speed.findData(4))
        self.assertEqual((scope.refresh_fps, scope.scroll_divisor), (10, 4))
        scope.trigger_mode.setCurrentIndex(
            scope.trigger_mode.findData("rising")
        )
        scope.trigger_level.setValue(1.0)
        self.assertEqual(scope.trigger_config[0], 0)
        self.assertTrue(scope.trigger_config[2])
        scope.smoothing.setChecked(False)
        self.assertFalse(scope.plot.smoothing)
        scope.close()

    def test_all_plot_modes_batch_render_with_invalid_gaps(self):
        plot = EnvelopePlot("#22d3ee")
        plot.resize(900, 340)
        values = np.linspace(-20.0, 20.0, 900, dtype=np.float32)
        valid = np.ones(900, dtype=bool)
        valid[210:218] = False
        valid[640:644] = False
        plot.set_envelope(values, values, valid)
        for mode in ("trace", "points", "envelope"):
            plot.set_plot_mode(mode)
            image = plot.grab()
            self.assertFalse(image.isNull())
            self.assertEqual(plot.plot_mode, mode)
        plot.close()

    def test_channels_are_independent_top_level_scope_windows(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        self.assertIsNone(window.scope_a.parentWidget())
        self.assertIsNone(window.scope_b.parentWidget())
        self.assertTrue(window.scope_a.isWindow())
        self.assertTrue(window.scope_b.isWindow())
        window.show_scope_a()
        self.app.processEvents()
        self.assertTrue(window.scope_a.isVisible())
        self.assertFalse(window.scope_b.isVisible())
        window.show_scope_b()
        self.app.processEvents()
        self.assertTrue(window.scope_a.isVisible())
        self.assertTrue(window.scope_b.isVisible())
        window.close()

    def test_adc_windows_keep_light_theme_inside_dark_host_application(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        dlc_dialog = DlcProSettingsDialog(
            window.dlc_session, self.settings, window
        )
        recording_dialog = RecordingOptionsDialog(
            RecordingOptionsDialog.WAVEFORM_ONLY,
            "recording summary",
            False,
            window,
        )
        self.assertIn("background: #f3f6fa", window.styleSheet())
        self.assertIn("QCheckBox", window.styleSheet())
        self.assertIn("background: #f3f6fa", dlc_dialog.styleSheet())
        self.assertEqual(dlc_dialog.styleSheet(), recording_dialog.styleSheet())
        recording_dialog.close()
        dlc_dialog.close()
        window.close()

    def test_dlc_dialog_steps_only_selected_scan_value(self):
        snapshot = SimpleNamespace(
            sc_enabled=True,
            sc_offset=2.0,
            sc_amplitude=0.5,
            sc_frequency=0.5,
            sc_output_channel=50,
            sc_signal_type=0,
            sc_unit="V",
        )

        class FakeService:
            def __init__(self):
                self.is_connected = True
                self.offset_writes = []
                self.amplitude_writes = []

            @staticmethod
            def list_serial_ports():
                return []

            @staticmethod
            def format_error(exc):
                return str(exc)

            def read_snapshot(self, _request):
                return snapshot

            def set_sc_offset(self, value):
                self.offset_writes.append(value)
                snapshot.sc_offset = value
                return snapshot

            def set_sc_amplitude(self, value):
                self.amplitude_writes.append(value)
                snapshot.sc_amplitude = value
                return snapshot

            def disconnect(self):
                self.is_connected = False

        service = FakeService()
        session = DlcScanSession(service, owns_service=True)
        session.poll_timer.stop()
        dialog = DlcProSettingsDialog(session, self.settings)
        dialog._render_snapshot(snapshot)
        self.assertTrue(dialog.amplitude_target.isChecked())
        self.assertEqual(dialog.amplitude.suffix(), " V pp")
        self.assertEqual(dialog.offset.suffix(), " V")

        dialog.offset_target.click()
        step_button = next(
            button for button in dialog.precision_buttons
            if abs(button._precision_step - 0.001) < 1e-12
        )
        step_button.click()
        self.assertTrue(dialog.offset_target.isChecked())
        self.assertAlmostEqual(dialog.offset.singleStep(), 0.001)

        updates = QSignalSpy(session.write_snapshot_changed)
        dialog.offset.stepBy(1)
        # Finish this session's private worker first, then dispatch its queued
        # Qt signal. This avoids racing an instantaneous fake service against
        # QSignalSpy.wait().
        self.assertTrue(session.pool.waitForDone(2000))
        self.app.processEvents()
        self.assertGreater(updates.count(), 0)
        self.assertEqual(service.amplitude_writes, [])
        self.assertEqual(service.offset_writes, [2.001])
        dialog.close()
        session.shutdown()

    def test_fast_timebase_supports_five_mhz_view(self):
        scope = ScopeWindow("A", "#22d3ee")
        scope.timebase.setCurrentIndex(scope.timebase.findData(0.1e-6))
        self.assertEqual(scope.required_samples(20_000_000), 20)
        scope.close()

    def test_tool_window_buttons_use_shared_foreground_helper(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        with mock.patch(
            "daq_pc.unified_daq_gui.show_window_front"
        ) as foreground:
            window.auto_lock_button.click()
            foreground.assert_called_with(window.auto_lock_workspace)
            self.assertIs(window.auto_lock_workspace, window.peak_lock_window)
            foreground.reset_mock()
            window.scan_control_button.click()
            foreground.assert_called_with(window.scan_control_window)
            foreground.reset_mock()
            window.scope_a_button.click()
            foreground.assert_called_with(window.scope_a)
            foreground.reset_mock()
            window.scope_b_button.click()
            foreground.assert_called_with(window.scope_b)
        window.close()

    def test_auto_lock_and_scopes_remain_independent_windows(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        auxiliary_windows = (
            window.auto_lock_workspace,
            window.scan_control_window,
        )

        for auxiliary in auxiliary_windows:
            self.assertIsNone(auxiliary.parentWidget())
            self.assertTrue(auxiliary.isWindow())
            self.assertEqual(auxiliary.windowType(), Qt.Window)
        self.assertIsNone(window.scope_a.parentWidget())
        self.assertIsNone(window.scope_b.parentWidget())
        self.assertIs(window.auto_lock_workspace, window.peak_lock_window)
        self.assertTrue(window.peak_lock_window.isWindow())

        window.show()
        window.show_scope_a()
        window.show_peak_lock()
        window.scan_control_window.show()
        self.app.processEvents()
        self.assertTrue(window.scope_a.isVisible())
        self.assertIsNone(window.scope_a.parentWidget())
        self.assertIsNone(window.peak_lock_window.parentWidget())
        window.peak_lock_window.show_scope_a_button.click()
        self.app.processEvents()
        self.assertTrue(window.scope_a.isVisible())
        self.assertGreaterEqual(
            window.scope_a.geometry().left(),
            window.peak_lock_window.geometry().right(),
        )
        window.showMinimized()
        self.app.processEvents()
        for auxiliary in auxiliary_windows:
            self.assertFalse(auxiliary.windowState() & Qt.WindowMinimized)

        window.close()

    def test_auto_lock_scope_buttons_tile_without_embedding(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        window.show_peak_lock()
        window.peak_lock_window.show_scope_b_button.click()
        self.app.processEvents()
        self.assertTrue(window.scope_b.isVisible())
        self.assertIsNone(window.scope_b.parentWidget())
        self.assertTrue(window.scope_b.isWindow())
        self.assertGreaterEqual(
            window.scope_b.geometry().left(),
            window.peak_lock_window.geometry().right(),
        )
        window.peak_lock_window.close()
        self.assertTrue(window.scope_b.isVisible())
        window.close()

    def test_auto_lock_scan_button_opens_shared_scan_window(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        with mock.patch(
            "daq_pc.unified_daq_gui.show_window_front"
        ) as foreground:
            window.peak_lock_window.scan_control_button.click()
        foreground.assert_called_once_with(window.scan_control_window)
        window.close()

    def test_all_21_parameters_have_toggle_and_window_remains_freely_resizable(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        panel = window.peak_lock_window
        self.assertFalse(panel.algorithm_settings_panel.isHidden())
        self.assertFalse(panel.algorithm_settings_button.isHidden())
        self.assertTrue(panel.algorithm_settings_button.isChecked())
        self.assertEqual(panel.algorithm_settings_button.text(), "隐藏算法参数")
        self.assertGreater(panel.maximumWidth(), 760)
        self.assertTrue(panel.algorithm_settings_panel.isAncestorOf(
            panel.save_button
        ))
        self.assertEqual(len(panel.parameter_info_buttons), 21)
        headings = {item.text() for item in panel.findChildren(QLabel)}
        self.assertTrue({"峰识别参数", "宽扫参数", "最终锁定参数"}.issubset(headings))
        self.assertEqual(
            panel.main_scroll.horizontalScrollBarPolicy(),
            Qt.ScrollBarAsNeeded,
        )
        self.assertEqual(panel.channel.itemText(0), "通道 A")
        self.assertEqual(panel.channel.itemText(1), "通道 B")
        panel.algorithm_settings_button.click()
        self.assertTrue(panel.algorithm_settings_panel.isHidden())
        self.assertEqual(panel.algorithm_settings_button.text(), "显示算法参数")
        panel.algorithm_settings_button.click()
        self.assertFalse(panel.algorithm_settings_panel.isHidden())
        window.close()

    def test_peak_lock_qsettings_migrates_old_values_without_overwriting_1hz_7pct(self):
        self.settings.setValue("peak_lock/search_frequency_hz", 1.0)
        self.settings.setValue("peak_lock/final_tolerance", 7.0)
        self.settings.setValue("peak_lock/direction_probe_step", 0.06)
        self.settings.setValue("peak_lock/min_offset_step", 0.002)
        window = MainWindow(preset_model=1, settings=self.settings)
        panel = window.peak_lock_window
        self.assertAlmostEqual(panel.search_frequency.value(), 1.0)
        self.assertAlmostEqual(panel.balance_tolerance.value(), 7.0)
        self.assertAlmostEqual(panel.offset_step.value(), 0.06)
        self.assertAlmostEqual(panel.min_offset_step.value(), 0.002)
        panel._save_ui_settings()
        self.assertAlmostEqual(float(self.settings.value("peak_lock/wide_probe_step")), 0.06)
        self.assertAlmostEqual(float(self.settings.value("peak_lock/final_fine_step")), 0.002)
        self.assertAlmostEqual(float(self.settings.value("peak_lock/final_balance_tolerance")), 7.0)
        window.close()

    def test_fpga_bit_selection_is_remembered_and_programming_is_background(self):
        bitstream = Path(self.tempdir.name) / "candidate.bit"
        bitstream.write_bytes(b"test-bitstream")
        window = MainWindow(preset_model=1, settings=self.settings)
        with mock.patch.object(
            QFileDialog, "getOpenFileName",
            return_value=(str(bitstream), "Xilinx Bitstream (*.bit)"),
        ):
            window.fpga_select_button.click()
        self.assertEqual(window.fpga_bit_path, bitstream.resolve())
        self.assertEqual(
            Path(str(self.settings.value("fpga/bit_path"))),
            bitstream.resolve(),
        )
        self.assertTrue(window.fpga_program_button.isEnabled())

        with (
            mock.patch(
                "daq_pc.unified_daq_gui.find_vivado_batch",
                return_value=Path("C:/Xilinx/Vivado/bin/vivado.bat"),
            ),
            mock.patch(
                "daq_pc.unified_daq_gui.FpgaProgrammer",
                FakeFpgaProgrammer,
            ),
            mock.patch.object(QMessageBox, "information") as information,
        ):
            window.fpga_program_button.click()
        self.assertEqual(window.fpga_progress.value(), 100)
        self.assertIn("下载完成", window.fpga_progress.format())
        information.assert_called_once()
        window.close()

        restored = MainWindow(preset_model=1, settings=self.settings)
        self.assertEqual(restored.fpga_bit_path, bitstream.resolve())
        self.assertIn("candidate.bit", restored.fpga_path_label.text())
        restored.close()

    def test_peak_lock_parameters_are_manual_only_and_explicitly_saved(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        panel = window.peak_lock_window
        self.assertAlmostEqual(panel.final_max_offset_deviation.value(), 0.09)
        cases = (
            (panel.min_prominence, "120", 120.0),
            (panel.noise_sigma, "7.5", 7.5),
            (panel.dominance, "5.50", 5.5),
            (panel.period_tolerance, "12.0", 12.0),
            (panel.narrow_main_height_ratio, "6.0", 6.0),
            (panel.invalid_retry_windows, "4", 4),
            (panel.offset_step, "0.050000", 0.05),
            (panel.search_frequency, "10.00", 10.0),
            (panel.initial_search_amplitude, "2.500000", 2.5),
            (panel.initial_offset_search_step, "1.000000", 1.0),
            (panel.min_offset_step, "0.001000", 0.001),
            (panel.target_amplitude, "0.200000", 0.2),
            (panel.final_coarse_step, "0.010000", 0.01),
            (panel.final_max_offset_deviation, "0.090000", 0.09),
            (panel.search_tolerance, "8.0", 8.0),
            (panel.model_corrections, "2", 2),
            (panel.search_windows, "2", 2),
            (panel.balance_tolerance, "5.0", 5.0),
            (panel.final_windows, "3", 3),
        )
        panel.show()
        self.app.processEvents()
        for spinbox, entered, expected in cases:
            self.assertEqual(
                spinbox.buttonSymbols(), QAbstractSpinBox.NoButtons
            )
            before = spinbox.value()
            spinbox.stepUp()
            self.assertAlmostEqual(spinbox.value(), before)
            spinbox.setFocus()
            QTest.keyClick(spinbox, Qt.Key_Up)
            self.assertAlmostEqual(spinbox.value(), before)
            editor = spinbox.lineEdit()
            editor.setFocus()
            editor.selectAll()
            QTest.keyClicks(editor, entered)
            QTest.keyClick(editor, Qt.Key_Return)
            self.assertAlmostEqual(spinbox.value(), expected)

        # Clicking in a numeric editor must place a normal caret instead of
        # forcing the complete value to remain selected.
        editor = panel.final_coarse_step.lineEdit()
        editor.setFocus()
        editor.selectAll()
        QTest.mouseClick(editor, Qt.LeftButton, pos=editor.rect().center())
        self.app.processEvents()
        self.assertEqual(editor.selectedText(), "")

        with mock.patch.object(QMessageBox, "information") as information:
            panel.save_button.click()
        information.assert_called_once()
        self.assertAlmostEqual(
            float(self.settings.value("peak_lock/final_max_offset_deviation")),
            0.09,
        )
        self.assertFalse(self.settings.contains("peak_lock/prediction_gain"))

        self.assertEqual(len(panel.parameter_info_buttons), 21)
        with mock.patch.object(ParameterHelpDialog, "exec") as show_help:
            panel.parameter_info_buttons["最终最大Offset偏移"].click()
        show_help.assert_called_once()
        help_dialog = panel.findChild(ParameterHelpDialog)
        self.assertIsNotNone(help_dialog)
        self.assertLessEqual(help_dialog.width(), 500)
        self.assertTrue(help_dialog.description_label.wordWrap())
        message = help_dialog.description_label.text()
        self.assertIn("0.09 V", message)

        configurable = (
            panel.channel, panel.polarity, panel.min_prominence,
            panel.noise_sigma, panel.dominance,
            panel.period_tolerance, panel.narrow_main_height_ratio,
            panel.invalid_retry_windows,
            panel.offset_step, panel.search_frequency,
            panel.initial_search_amplitude,
            panel.initial_offset_search_step,
            panel.target_amplitude, panel.final_coarse_step,
            panel.min_offset_step, panel.final_max_offset_deviation,
            panel.search_tolerance, panel.model_corrections,
            panel.search_windows, panel.balance_tolerance,
            panel.final_windows,
        )
        panel._running_changed(True)
        self.assertTrue(all(not widget.isEnabled() for widget in configurable))
        self.assertTrue(all(
            not edit.isEnabled() for edit in panel.strategy_edits.values()
        ))
        self.assertFalse(panel.save_button.isEnabled())
        self.assertTrue(all(
            button.isEnabled()
            for button in panel.parameter_info_buttons.values()
        ))
        panel._running_changed(False)
        self.assertTrue(all(widget.isEnabled() for widget in configurable))
        self.assertTrue(all(
            edit.isEnabled() for edit in panel.strategy_edits.values()
        ))
        self.assertTrue(panel.save_button.isEnabled())
        window.close()

    def test_peak_lock_advice_card_opens_copyable_history(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        panel = window.peak_lock_window
        observation = SimpleNamespace(
            measured_period=1.0, prominence=5200.0,
            second_prominence=500.0, dominance_ratio=10.4, snr=80.0,
            delta_t1=0.49, delta_t2=0.51, balance_error=0.02,
        )
        panel._render_status({
            "observation": observation,
            "state": "observe",
            "message": "00模有效",
            "offset": 0.2,
            "start_offset": 0.0,
            "amplitude": 1.0,
            "last_good_amplitude": 1.0,
            "start_amplitude": 4.0,
            "scan_frequency": 1.0,
            "offset_step": 0.01,
            "step_profile": "中调（Amplitude≤1 Vpp）",
            "manual_advice": "请把 Scan Offset 从 0.200000 调到 0.210000。",
        })
        self.assertGreaterEqual(panel.manual_advice_label.minimumHeight(), 70)
        self.assertIn("0.210000", panel.manual_advice_label.text())
        panel.manual_advice_label.clicked.emit()
        self.app.processEvents()
        self.assertTrue(panel.advice_dialog.isVisible())
        self.assertIn("0.210000", panel.advice_dialog.current.toPlainText())
        self.assertIn("0.210000", panel.advice_dialog.history.toPlainText())
        panel.advice_dialog.close()
        window.close()

    def test_peak_lock_two_level_summary_follows_editable_parameters(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        panel = window.peak_lock_window
        top_editor = panel.target_amplitude.lineEdit()
        top_editor.setFocus()
        top_editor.selectAll()
        QTest.keyClicks(top_editor, "0.190000")
        QTest.keyClick(top_editor, Qt.Key_Return)
        panel.min_offset_step.setValue(0.001)
        panel.final_coarse_step.setValue(0.01)
        panel.final_max_offset_deviation.setValue(0.09)
        self.assertEqual(panel.strategy_labels[(2, 1)].text(), "0.190 Vpp")
        self.assertIn("定向0.010 V", panel.strategy_labels[(2, 3)].text())
        self.assertIn("边界±0.090 V", panel.strategy_labels[(2, 3)].text())
        self.assertAlmostEqual(panel.current_settings().final_amplitude, 0.19)
        window.close()

    def test_scope_vertical_ranges_are_independent_but_timebase_is_linked(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        window.scope_a.y_range.setCurrentIndex(
            window.scope_a.y_range.findData(0.02)
        )
        window.scope_b.y_range.setCurrentIndex(
            window.scope_b.y_range.findData(0.005)
        )
        self.assertEqual(window.scope_a.y_range.currentData(), 0.02)
        self.assertEqual(window.scope_b.y_range.currentData(), 0.005)

        window.scope_a.units.setCurrentIndex(
            window.scope_a.units.findData("raw")
        )
        self.assertEqual(window.scope_a.units.currentData(), "raw")
        self.assertEqual(window.scope_b.units.currentData(), "module")
        self.assertEqual(window.scope_b.y_range.currentData(), 0.005)

        window.scope_a.display_mode.setCurrentIndex(
            window.scope_a.display_mode.findData("envelope")
        )
        window.scope_b.display_mode.setCurrentIndex(
            window.scope_b.display_mode.findData("points")
        )
        self.assertEqual(window.scope_a.plot.plot_mode, "envelope")
        self.assertEqual(window.scope_b.plot.plot_mode, "points")
        self.assertFalse(window.scope_a.smoothing.isEnabled())
        self.assertFalse(window.scope_b.smoothing.isEnabled())

        window.scope_a.timebase.setCurrentIndex(
            window.scope_a.timebase.findData(20e-3)
        )
        self.assertEqual(window.scope_b.timebase.currentData(), 20e-3)
        window.close()

    def test_one_second_per_div_uses_long_history_cache(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        window.show_scope_a()
        self.app.processEvents()
        window.scope_a.timebase.setCurrentIndex(
            window.scope_a.timebase.findData(1.0)
        )
        self.assertEqual(
            window.scope_a.required_samples(20_000_000), 200_000_000
        )
        payload = np.column_stack((
            np.arange(100, dtype=np.int16),
            -np.arange(100, dtype=np.int16),
        )).astype("<i2").tobytes()
        window.ring.append_packet(0, 1, 20_000_000, payload)
        with (
            mock.patch.object(
                window.ring, "history_envelope",
                return_value=(
                    np.array([0]), np.array([1]),
                    np.array([-1]), np.array([0]),
                    np.array([True]),
                ),
            ) as history,
            mock.patch.object(window.ring, "envelope") as raw,
        ):
            window.refresh_plots()
        history.assert_called_once()
        raw.assert_not_called()
        window.close()

    def test_hdf5_destination_is_selected_before_recording_starts(self):
        snapshot = SimpleNamespace(
            sc_enabled=False, sc_offset=0.1, sc_amplitude=0.2,
            sc_frequency=5.0, sc_output_channel=50, sc_signal_type=0,
            sc_unit="V",
        )
        window = MainWindow(
            preset_model=1,
            settings=self.settings,
            snapshot_provider=lambda: snapshot,
        )
        destination = os.path.join(self.tempdir.name, "capture.h5")
        with (
            mock.patch.object(
                RecordingOptionsDialog, "get_mode",
                return_value=RecordingOptionsDialog.WAVEFORM_ONLY,
            ),
            mock.patch.object(
                QFileDialog, "getSaveFileName",
                return_value=(destination, "HDF5实验数据 (*.h5)")
            ) as save_dialog,
        ):
            window.toggle_recording()
            self.assertIsNotNone(window.recorder)
            self.assertEqual(window.record_temp_path, Path(destination))
            save_dialog.assert_called_once()
            payload = np.array([[1, 3], [2, 4]], dtype="<i2").tobytes()
            window.recorder.append_packet(1.5, SimpleNamespace(
                sample_pair_count=2,
                channel_mask=3,
                payload=payload,
                stream_id=7,
                sample_rate_hz=20_000_000,
                first_sample_pair=0,
            ))
            window.toggle_recording()
        self.assertTrue(os.path.exists(destination))
        self.assertIsNone(window.record_temp_path)
        window.close()

    def test_record_rate_options_exclude_unsafe_full_rate_hdf5(self):
        window = MainWindow(settings=self.settings)
        rates = {
            int(window.record_rate.itemData(index))
            for index in range(window.record_rate.count())
        }
        self.assertEqual(rates, {1_000_000, 100_000, 10_000, 1_000})
        self.assertEqual(window.record_rate.currentData(), 100_000)
        window.close()

    def test_20_msps_recording_requires_jumbo_before_path_selection(self):
        window = MainWindow(settings=self.settings)
        window.rate.setCurrentIndex(window.rate.findData(20_000_000))
        window.jumbo.setChecked(False)
        with (
            mock.patch.object(
                RecordingOptionsDialog, "get_mode",
                return_value=RecordingOptionsDialog.WAVEFORM_ONLY,
            ),
            mock.patch.object(QMessageBox, "critical") as warning,
            mock.patch.object(QFileDialog, "getSaveFileName") as save_dialog,
        ):
            window.toggle_recording()
        self.assertIsNone(window.recorder)
        warning.assert_called_once()
        save_dialog.assert_not_called()
        window.close()

    def test_recording_cancel_does_not_create_a_recorder(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        with (
            mock.patch.object(
                RecordingOptionsDialog, "get_mode",
                return_value=RecordingOptionsDialog.WAVEFORM_ONLY,
            ),
            mock.patch.object(
                QFileDialog, "getSaveFileName", return_value=("", "")
            ),
        ):
            window.toggle_recording()
        self.assertIsNone(window.recorder)
        self.assertIsNone(window.record_temp_path)
        self.assertFalse(window.record_button.isChecked())
        window.close()

    def test_combined_recording_requires_a_live_dlcpro_snapshot(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        with (
            mock.patch.object(
                RecordingOptionsDialog, "get_mode",
                return_value=RecordingOptionsDialog.WITH_DLCPRO,
            ),
            mock.patch.object(QMessageBox, "warning") as warning,
            mock.patch.object(window, "show_dlc_settings") as show_settings,
            mock.patch.object(QFileDialog, "getSaveFileName") as save_dialog,
        ):
            window.toggle_recording()
        self.assertIsNone(window.recorder)
        warning.assert_called_once()
        show_settings.assert_called_once()
        save_dialog.assert_not_called()
        window.close()

    def test_combined_recording_writes_dlcpro_timeline(self):
        snapshot = SimpleNamespace(
            sc_enabled=True, sc_offset=2.0, sc_amplitude=0.75,
            sc_frequency=20.0, sc_output_channel=50, sc_signal_type=1,
            sc_unit="V",
        )
        service = SimpleNamespace(
            is_connected=True,
            list_serial_ports=lambda: [],
        )
        window = MainWindow(
            preset_model=1,
            settings=self.settings,
            snapshot_provider=lambda: snapshot,
            dlc_service=service,
        )
        destination = os.path.join(self.tempdir.name, "combined.h5")
        with (
            mock.patch.object(
                RecordingOptionsDialog, "get_mode",
                return_value=RecordingOptionsDialog.WITH_DLCPRO,
            ),
            mock.patch.object(
                QFileDialog, "getSaveFileName",
                return_value=(destination, "HDF5实验数据 (*.h5)"),
            ),
        ):
            window.toggle_recording()
            packet = SimpleNamespace(
                sample_pair_count=4,
                channel_mask=3,
                payload=np.array(
                    [[1, 2], [3, 4], [5, 6], [7, 8]], dtype="<i2"
                ).tobytes(),
                stream_id=2,
                sample_rate_hz=5_000_000,
                first_sample_pair=100,
            )
            window.recorder.append_packet(1.0, packet)
            window.toggle_recording()
        with h5py.File(destination, "r") as handle:
            self.assertEqual(
                handle.attrs["recording_mode"], "waveform_with_dlcpro"
            )
            self.assertEqual(handle["dlcpro/scan_offset"][0], 2.0)
            self.assertEqual(handle["dlcpro/scan_amplitude"][0], 0.75)
        window.close()

    def test_recording_blocks_a_target_without_safe_free_space(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        destination = os.path.join(self.tempdir.name, "too_small.h5")
        with (
            mock.patch.object(
                RecordingOptionsDialog, "get_mode",
                return_value=RecordingOptionsDialog.WAVEFORM_ONLY,
            ),
            mock.patch.object(
                QFileDialog, "getSaveFileName",
                return_value=(destination, "HDF5实验数据 (*.h5)")
            ),
            mock.patch(
                "daq_pc.unified_daq_gui.shutil.disk_usage",
                return_value=SimpleNamespace(
                    total=12 * 1024 ** 3,
                    used=3 * 1024 ** 3,
                    free=9 * 1024 ** 3,
                ),
            ),
            mock.patch.object(QMessageBox, "critical") as critical,
        ):
            window.toggle_recording()
        self.assertIsNone(window.recorder)
        self.assertFalse(window.record_button.isChecked())
        critical.assert_called_once()
        window.close()

    def test_triggered_envelope_aligns_both_channels(self):
        ring = DualSampleRingBuffer(capacity=4096)
        a = np.tile(np.array([-20, -10, 10, 20], np.int16), 300)
        b = -a
        payload = np.column_stack((a, b)).astype("<i2").tobytes()
        ring.append_packet(0, 1, 5_000_000, payload)
        result = ring.triggered_envelope(
            400, 200, channel=0, level=0, rising=True
        )
        self.assertIsNotNone(result)
        self.assertTrue(result[-1])

    def test_scope_and_main_settings_persist(self):
        window = MainWindow(preset_model=1, settings=self.settings)
        window.rate.setCurrentIndex(window.rate.findData(20_000_000))
        window.scope_a.timebase.setCurrentIndex(
            window.scope_a.timebase.findData(200e-6)
        )
        window.scope_a.trigger_mode.setCurrentIndex(
            window.scope_a.trigger_mode.findData("falling")
        )
        window.scope_a.smoothing.setChecked(False)
        window._save_settings()
        window.close()
        restored = MainWindow(settings=self.settings)
        self.assertEqual(restored.model.currentData(), 1)
        self.assertEqual(restored.rate.currentData(), 10_000_000)
        self.assertFalse(restored.jumbo.isChecked())
        self.assertEqual(restored.scope_a.timebase.currentData(), 200e-6)
        self.assertEqual(restored.scope_a.trigger_mode.currentData(), "falling")
        self.assertFalse(restored.scope_a.smoothing.isChecked())
        restored.close()


if __name__ == "__main__":
    unittest.main()
