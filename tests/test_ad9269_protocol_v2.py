from __future__ import annotations

import struct
import unittest

import numpy as np

from daq_pc.daq_protocol_v2 import (
    CONTROL_MAGIC,
    DATA_FORMAT_DUAL_S16,
    DATA_HEADER_STRUCT,
    DATA_MAGIC,
    PROTOCOL_VERSION,
    STATUS_EXTENSION_STRUCT,
    STATUS_MAGIC,
    STATUS_STRUCT,
    Command,
    PlCommand,
    pack_pldq,
    parse_control_response,
    parse_data_packet,
)
from daq_pc.daq_udp_dual import DualSampleRingBuffer


class ProtocolV2Tests(unittest.TestCase):
    def test_pldq_request_is_20_bytes_and_preserves_arguments(self):
        packet = pack_pldq(PlCommand.CONFIG_RATE, 7, 3, 0xA5A5)
        self.assertEqual(len(packet), 20)
        magic, command_word, transaction, arg0, arg1 = struct.unpack(
            "!IIIII", packet
        )
        self.assertEqual(magic, CONTROL_MAGIC)
        self.assertEqual(command_word >> 24, PROTOCOL_VERSION)
        self.assertEqual((command_word >> 16) & 0xFF, PlCommand.CONFIG_RATE)
        self.assertEqual((transaction, arg0, arg1), (7, 3, 0xA5A5))

    def test_daqs_status_and_extension_are_parsed(self):
        version_state_model = (
            (PROTOCOL_VERSION << 24) | (3 << 17) | (1 << 16)
        )
        raw = STATUS_STRUCT.pack(
            STATUS_MAGIC,
            version_state_model,
            9,
            20_000_000,
            20_000_123,
            17,
            0,
            3,
            12,
            8,
            2,
            0x6,
            0,
            123,
        ) + STATUS_EXTENSION_STRUCT.pack(
            4,
            5,
            0x89ABCDEF,
            0x01234567,
            6,
            1,
        )
        self.assertEqual(len(raw), 80)
        response = parse_control_response(raw)
        self.assertEqual(response.command, Command.STATUS)
        self.assertEqual(response.request_id, 123)
        self.assertEqual(response.stream_id, 9)
        self.assertEqual(response.sample_rate_hz, 20_000_000)
        self.assertEqual(response.data_format, DATA_FORMAT_DUAL_S16)
        self.assertEqual(response.dco_frequency_hz, 20_000_123)
        self.assertEqual(response.daq_state, 3)
        self.assertEqual(response.last_error, 0)
        self.assertTrue(response.jumbo_enabled)
        self.assertTrue(response.monitor_enabled)
        self.assertTrue(response.event_path_enabled)
        self.assertEqual((response.otr_a_count, response.otr_b_count), (4, 5))
        self.assertEqual(response.suppressed_event_count, 6)
        self.assertEqual(response.peak_interval_q16, 0x0123456789ABCDEF)

    def test_data_packet_preserves_little_endian_ab_pairs(self):
        pairs = np.array([(1, -2), (32767, -32768)], dtype="<i2")
        payload = pairs.tobytes()
        header = DATA_HEADER_STRUCT.pack(
            DATA_MAGIC,
            (PROTOCOL_VERSION << 24) | (2 << 16) | (2 << 8),
            5,
            8,
            20_000_000,
            0,
            100,
            0,
            0x11,
            (DATA_HEADER_STRUCT.size << 16) | len(payload),
        )
        packet = parse_data_packet(header + payload)
        decoded = np.frombuffer(packet.payload, dtype="<i2").reshape(-1, 2)
        np.testing.assert_array_equal(decoded, pairs)
        self.assertEqual(packet.first_sample_pair, 100)
        self.assertEqual(packet.sample_stride, 1)
        self.assertEqual(packet.sample_pair_count, 2)
        self.assertEqual(packet.flags, 0x11)

    def test_dual_ring_marks_missing_preview_samples_invalid(self):
        ring = DualSampleRingBuffer(capacity=32)
        first = np.array([(10, 20), (11, 21)], dtype="<i2")
        second = np.array([(14, 24)], dtype="<i2")
        ring.append_packet(0, 2, 10_000_000, first.tobytes())
        ring.append_packet(8, 2, 10_000_000, second.tobytes())
        a, b, valid, rate, stride = ring.snapshot(8)
        np.testing.assert_array_equal(a, [10, 11, 0, 0, 0, 0, 14])
        np.testing.assert_array_equal(b, [20, 21, 0, 0, 0, 0, 24])
        np.testing.assert_array_equal(
            valid, [True, True, False, False, False, False, True]
        )
        self.assertEqual(rate, 10_000_000)
        self.assertEqual(stride, 2)


if __name__ == "__main__":
    unittest.main()
