from __future__ import annotations

import struct
import socket
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from daq_pc.daq_protocol_v2 import (
    CONTROL_MAGIC, DATA_MAGIC, STATUS_MAGIC, Command, DaqdContinuityTracker,
    PlCommand, pack_pldq, parse_data_packet, parse_status_packet,
)
from daq_pc.daq_udp_dual import ControlClient, DualSampleRingBuffer
from daq_pc.daq_udp import SampleRingBuffer


class PlProtocolTest(unittest.TestCase):
    @staticmethod
    def _data_packet(sequence: int, first: int, count: int = 2):
        payload = bytes(count * 4)
        header = struct.pack(
            "!10I", DATA_MAGIC, 0x01020202, 7, sequence & 0xFFFFFFFF,
            20_000_000, (first >> 32) & 0xFFFFFFFF, first & 0xFFFFFFFF,
            count, 0, (40 << 16) | len(payload),
        )
        return parse_data_packet(header + payload)

    def test_control_uses_subnet_broadcast_without_arp(self):
        client = ControlClient("192.168.20.2")
        self.assertEqual(client.control_ip, "192.168.20.255")

    def test_control_ignores_non_status_packet_before_matching_daqs(self):
        words = [
            STATUS_MAGIC, 0x01070000, 9, 5_000_000, 5_000_000, 0, 0,
            0, 0, 0, 0, 0, 0x00010000, 1,
        ]
        good_status = struct.pack("!14I", *words)
        fake_socket = MagicMock()
        fake_socket.__enter__.return_value = fake_socket
        fake_socket.recvfrom.side_effect = [
            (b"not-a-status-datagram", ("192.168.20.2", 5000)),
            (good_status, ("192.168.20.2", 5000)),
        ]
        with patch("daq_pc.daq_udp_dual.socket.socket", return_value=fake_socket):
            response = ControlClient("192.168.20.2")._exchange(
                PlCommand.GET_STATUS
            )
        self.assertEqual((response.request_id, response.stream_id), (1, 9))

    def test_control_retries_same_transaction_after_udp_timeout(self):
        words = [
            STATUS_MAGIC, 0x01070000, 12, 5_000_000, 5_000_000, 0, 0,
            0, 0, 0, 0, 0, 0x00010000, 1,
        ]
        good_status = struct.pack("!14I", *words)
        fake_socket = MagicMock()
        fake_socket.__enter__.return_value = fake_socket
        fake_socket.recvfrom.side_effect = [
            socket.timeout(),
            (good_status, ("192.168.20.2", 5000)),
        ]
        with patch("daq_pc.daq_udp_dual.socket.socket", return_value=fake_socket):
            response = ControlClient("192.168.20.2")._exchange(
                PlCommand.SELECT_ADC
            )
        self.assertEqual((response.request_id, response.stream_id), (1, 12))
        self.assertEqual(fake_socket.sendto.call_count, 2)
        first_packet = fake_socket.sendto.call_args_list[0].args[0]
        second_packet = fake_socket.sendto.call_args_list[1].args[0]
        self.assertEqual(first_packet, second_packet)

    def test_mutating_config_is_confirmed_by_final_get_status(self):
        client = ControlClient("192.168.20.2", adc_model=1)
        response = object()
        with (
            patch.object(client, "_send_only") as send_only,
            patch.object(client, "_exchange", return_value=response) as exchange,
            patch("daq_pc.daq_udp_dual.time.sleep"),
        ):
            actual = client.request(
                Command.CONFIG, sample_rate_hz=5_000_000,
                flags=0, jumbo_enable=False,
            )
        self.assertIs(actual, response)
        self.assertEqual(send_only.call_args_list, [
            unittest.mock.call(PlCommand.SELECT_ADC, 1, 0),
            unittest.mock.call(PlCommand.CONFIG_RATE, 1, 0),
            unittest.mock.call(PlCommand.SET_ADC_TEST, 0, 0),
        ])
        exchange.assert_called_once_with(PlCommand.GET_STATUS)

    def test_high_rate_start_can_disable_raw_monitor(self):
        client = ControlClient("192.168.20.2", adc_model=1)
        response = object()
        with patch.object(
            client, "_mutate_then_status", return_value=response
        ) as mutate:
            actual = client.request(Command.START, monitor_enable=False)
        self.assertIs(actual, response)
        mutate.assert_called_once_with((
            (PlCommand.ACQ_START, 0, 0),
            (PlCommand.MONITOR_STOP, 0, 0),
        ))

    def test_ad9269_packet_and_little_endian_samples(self):
        payload = struct.pack("<hhhh", -2, 3, 100, -101)
        header = struct.pack("!10I", DATA_MAGIC, 0x01020202, 7, 8, 20_000_000,
                             0, 11, 2, 0, (40 << 16) | len(payload))
        packet = parse_data_packet(header + payload)
        self.assertEqual((packet.stream_id, packet.first_sample_pair, packet.sample_pair_count), (7, 11, 2))
        ring = DualSampleRingBuffer(8)
        ring.append_packet(packet.first_sample_pair, 1, packet.sample_rate_hz, packet.payload)
        a, b, valid, rate, stride = ring.snapshot(8)
        self.assertEqual(a.tolist(), [-2, 100]); self.assertEqual(b.tolist(), [3, -101])
        self.assertTrue(valid.all()); self.assertEqual((rate, stride), (20_000_000, 1))

    def test_ad9269_jumbo_packet_is_not_truncated(self):
        payload = struct.pack("<4096h", *(
            value for index in range(2048)
            for value in (index & 0x7fff, -(index & 0x7fff))
        ))
        header = struct.pack(
            "!10I", DATA_MAGIC, 0x01020202, 21, 9, 20_000_000,
            0, 1234, 2048, 4, (40 << 16) | 8192,
        )
        packet = parse_data_packet(header + payload)
        self.assertEqual(packet.sample_pair_count, 2048)
        ring = DualSampleRingBuffer(4096)
        ring.append_packet(
            packet.first_sample_pair, 1, packet.sample_rate_hz, packet.payload
        )
        a, b, valid, rate, _ = ring.snapshot(2048)
        self.assertEqual((a[0], b[0], a[-1], b[-1]),
                         (0, 0, 2047, -2047))
        self.assertTrue(valid.all())
        self.assertEqual(rate, 20_000_000)

    def test_continuity_tracker_separates_network_and_pl_gaps(self):
        tracker = DaqdContinuityTracker()
        tracker.observe(self._data_packet(10, 100, 4))
        update = tracker.observe(self._data_packet(12, 110, 4))
        self.assertEqual(update.network_packets_lost, 1)
        self.assertEqual(update.pl_samples_lost, 6)
        self.assertEqual(tracker.network_packets_lost, 1)
        self.assertEqual(tracker.pl_samples_lost, 6)
        self.assertEqual((tracker.last_gap_expected, tracker.last_gap_actual),
                         (104, 110))
        # The authoritative missing-sample total is six, not six plus one
        # packet; transport and PL diagnostics are deliberately separate.

    def test_continuity_tracker_handles_low32_and_sequence_wrap(self):
        tracker = DaqdContinuityTracker()
        tracker.observe(self._data_packet(0xFFFFFFFF, 0xFFFF_FFFE, 2))
        update = tracker.observe(self._data_packet(0, 0x1_0000_0000, 2))
        self.assertEqual(update.network_packets_lost, 0)
        self.assertEqual(update.pl_samples_lost, 0)
        self.assertFalse(update.reordered_or_duplicate)

    def test_continuity_tracker_reports_pl_gap_with_contiguous_packets(self):
        tracker = DaqdContinuityTracker()
        tracker.observe(self._data_packet(20, 1_000, 4))
        update = tracker.observe(self._data_packet(21, 1_009, 4))
        self.assertEqual(update.network_packets_lost, 0)
        self.assertEqual(update.pl_samples_lost, 5)
        self.assertEqual(tracker.index_gap_events, 1)

    def test_continuity_tracker_ignores_late_duplicate_without_false_gap(self):
        tracker = DaqdContinuityTracker()
        tracker.observe(self._data_packet(30, 2_000, 4))
        tracker.observe(self._data_packet(31, 2_004, 4))
        update = tracker.observe(self._data_packet(30, 2_000, 4))
        self.assertTrue(update.reordered_or_duplicate)
        self.assertEqual(tracker.network_packets_lost, 0)
        self.assertEqual(tracker.pl_samples_lost, 0)
        self.assertEqual(tracker.expected_sequence, 32)
        self.assertEqual(tracker.expected_first_sample, 2_008)

    def test_ad9280_packet(self):
        payload = bytes((1, 2, 3, 4))
        header = struct.pack("!10I", DATA_MAGIC, 0x01010101, 2, 3, 5_000_000,
                             0, 99, 4, 0, (40 << 16) | len(payload))
        packet = parse_data_packet(header + payload)
        dual_ring = DualSampleRingBuffer(8)
        dual_ring.append_packet(packet.first_sample_pair, 1, packet.sample_rate_hz,
                                packet.payload, mono_u8=True)
        a, b, valid_dual, _, _ = dual_ring.snapshot(8)
        self.assertEqual(a.tolist(), [1, 2, 3, 4])
        self.assertEqual(b.tolist(), [0, 0, 0, 0])
        self.assertTrue(valid_dual.all())
        ring = SampleRingBuffer(8); ring.append_packet(packet.first_sample_pair, packet.payload)
        values, valid, first = ring.snapshot(8)
        self.assertEqual(values.tolist(), [1, 2, 3, 4]); self.assertTrue(valid.all()); self.assertEqual(first, 99)

    def test_status_packet(self):
        words = [STATUS_MAGIC, 0x01070000, 15, 10_000_000, 9_999_997, 42, 3, 4, 5, 6, 7, 0x7, 0x00010000, 77]
        response = parse_status_packet(struct.pack("!14I", *words))
        self.assertEqual((response.stream_id, response.sample_rate_hz, response.request_id), (15, 10_000_000, 77))
        self.assertTrue(response.jumbo_enabled)

    def test_extended_status_otr_and_peak_interval(self):
        base = [STATUS_MAGIC, 0x01070000, 15, 10_000_000, 9_999_997,
                42, 3, 4, 5, 6, 7, 0x7, 0x00010000, 77]
        extension = [12, 13, 0x89ABCDEF, 0x01234567, 23, 1]
        response = parse_status_packet(struct.pack("!20I", *(base + extension)))
        self.assertEqual((response.otr_a_count, response.otr_b_count), (12, 13))
        self.assertEqual(response.peak_interval_q16, 0x0123456789ABCDEF)
        self.assertEqual(response.suppressed_event_count, 23)
        self.assertTrue(response.event_path_enabled)

    def test_rejects_bad_payload_size(self):
        header = struct.pack("!10I", DATA_MAGIC, 0x01020202, 0, 0, 1, 0, 0, 2, 0, (40 << 16) | 3)
        with self.assertRaises(ValueError):
            parse_data_packet(header + b"123")

    def test_all_control_commands_are_20_byte_pldq(self):
        for command in PlCommand:
            packet = pack_pldq(command, 0x1234, 7, 9)
            self.assertEqual(len(packet), 20)
            magic, version_command, transaction, arg0, arg1 = struct.unpack("!5I", packet)
            self.assertEqual((magic, transaction, arg0, arg1), (CONTROL_MAGIC, 0x1234, 7, 9))
            self.assertEqual(version_command >> 24, 1)
            self.assertEqual((version_command >> 16) & 0xff, command)

    def test_ring_drops_wholly_reordered_payload_and_envelopes(self):
        ring = DualSampleRingBuffer(8)
        ring.append_packet(10, 1, 20_000_000, struct.pack("<hhhh", 10, 20, 11, 21))
        ring.append_packet(8, 1, 20_000_000, struct.pack("<hh", 8, 18))
        a, b, valid, _, _ = ring.snapshot(8)
        self.assertEqual(a.tolist(), [10, 11]); self.assertEqual(b.tolist(), [20, 21]); self.assertTrue(valid.all())
        amin, amax, bmin, bmax, bins_valid = ring.envelope(2, 1)
        self.assertEqual((amin.tolist(), amax.tolist(), bmin.tolist(), bmax.tolist()), ([10], [11], [20], [21]))
        self.assertTrue(bins_valid.all())

    def test_record_cursor_never_replays_samples(self):
        ring = DualSampleRingBuffer(8)
        ring.append_packet(0, 1, 5_000_000,
                           struct.pack("<hhhhhh", 1, 11, 2, 12, 3, 13))
        a, b, valid, _, _, cursor, dropped = ring.read_since(0, 2)
        self.assertEqual((a.tolist(), b.tolist()), ([2, 3], [12, 13]))
        self.assertTrue(valid.all()); self.assertEqual((cursor, dropped), (3, 1))
        a, _, _, _, _, cursor2, dropped2 = ring.read_since(cursor, 2)
        self.assertEqual(a.size, 0); self.assertEqual((cursor2, dropped2), (3, 0))
        ring.append_packet(3, 1, 5_000_000,
                           struct.pack("<hhhh", 4, 14, 5, 15))
        a, b, _, _, _, cursor3, dropped3 = ring.read_since(cursor2, 2)
        self.assertEqual((a.tolist(), b.tolist()), ([4, 5], [14, 15]))
        self.assertEqual((cursor3, dropped3), (5, 0))

    def test_long_history_keeps_ten_seconds_outside_raw_ring(self):
        ring = DualSampleRingBuffer(128)
        values = np.arange(10_000, dtype=np.int16)
        payload = np.column_stack((values, -values)).astype("<i2").tobytes()
        ring.append_packet(0, 1, 1_000, payload)
        result = ring.history_envelope(10.0, 500)
        self.assertIsNotNone(result)
        amin, amax, bmin, bmax, valid = result
        self.assertLessEqual(len(amin), 500)
        self.assertTrue(valid.all())
        self.assertEqual(int(amin[0]), 0)
        self.assertEqual(int(amax[-1]), 9_999)
        self.assertEqual(int(bmin[-1]), -9_999)


if __name__ == "__main__":
    unittest.main()
