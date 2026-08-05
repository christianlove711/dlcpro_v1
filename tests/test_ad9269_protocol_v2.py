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
    RESPONSE_STRUCT,
    Command,
    Status,
    pack_control_request,
    parse_control_response,
    parse_data_packet,
)
from daq_pc.daq_udp_dual import DualSampleRingBuffer


class ProtocolV2Tests(unittest.TestCase):
    def test_control_request_is_32_bytes_and_signed_threshold(self):
        packet = pack_control_request(
            Command.CONFIG,
            7,
            sample_rate_hz=20_000_000,
            threshold=-1234,
        )
        self.assertEqual(len(packet), 32)
        self.assertEqual(struct.unpack_from("!H", packet, 18)[0], (-1234) & 0xFFFF)

    def test_control_response_is_92_bytes(self):
        raw = RESPONSE_STRUCT.pack(
            CONTROL_MAGIC,
            PROTOCOL_VERSION,
            int(Command.STATUS) | int(Command.RESPONSE),
            9,
            int(Status.OK),
            20_000_000,
            262_144,
            8,
            3,
            0x111,
            17,
            0,
            0,
            12,
            1,
            123_456_789,
            4,
            DATA_FORMAT_DUAL_S16,
            2,
            3,
            20_000_123,
            3,
            0,
        )
        self.assertEqual(len(raw), 92)
        response = parse_control_response(raw)
        self.assertEqual(response.preview_stride, 4)
        self.assertEqual(response.sample_pair_count, 123_456_789)
        self.assertEqual(response.data_format, DATA_FORMAT_DUAL_S16)
        self.assertEqual(response.dco_frequency_hz, 20_000_123)
        self.assertEqual(response.daq_state, 3)
        self.assertEqual(response.last_error, 0)

    def test_data_packet_preserves_little_endian_ab_pairs(self):
        pairs = np.array([(1, -2), (32767, -32768)], dtype="<i2")
        payload = pairs.tobytes()
        header = DATA_HEADER_STRUCT.pack(
            DATA_MAGIC,
            PROTOCOL_VERSION,
            0,
            DATA_HEADER_STRUCT.size,
            5,
            8,
            1,
            3,
            20_000_000,
            4,
            3,
            100,
            2,
            len(payload),
        )
        packet = parse_data_packet(header + payload)
        decoded = np.frombuffer(packet.payload, dtype="<i2").reshape(-1, 2)
        np.testing.assert_array_equal(decoded, pairs)
        self.assertEqual(packet.first_sample_pair, 100)
        self.assertEqual(packet.sample_stride, 4)

    def test_dual_ring_marks_missing_preview_samples_invalid(self):
        ring = DualSampleRingBuffer(capacity=32)
        first = np.array([(10, 20), (11, 21)], dtype="<i2")
        second = np.array([(14, 24)], dtype="<i2")
        ring.append_packet(0, 2, 10_000_000, first.tobytes())
        ring.append_packet(8, 2, 10_000_000, second.tobytes())
        a, b, valid, rate, stride = ring.snapshot(8)
        np.testing.assert_array_equal(a, [10, 11, 0, 0, 14])
        np.testing.assert_array_equal(b, [20, 21, 0, 0, 24])
        np.testing.assert_array_equal(valid, [True, True, False, False, True])
        self.assertEqual(rate, 10_000_000)
        self.assertEqual(stride, 2)


if __name__ == "__main__":
    unittest.main()
