"""PL-UDP protocol used by the unified Zynq DAQ image.

The public names in this module deliberately retain the v2 GUI API so the
existing AD9269 viewer remains usable while its wire protocol is PLDQ v1.
All multi-byte words on the wire are big endian; AD9269 payload samples are
little endian pairs (A_L, A_H, B_L, B_H).
"""
from __future__ import annotations

import enum
import struct
from dataclasses import dataclass

PROTOCOL_VERSION = 1
CONTROL_PORT = 5000
DATA_PORT = 5001
CONTROL_MAGIC = 0x504C4451  # PLDQ
DATA_MAGIC = 0x44415144     # DAQD
STATUS_MAGIC = 0x44415153   # DAQS
REQUEST_STRUCT = struct.Struct("!IIIII")
DATA_HEADER_STRUCT = struct.Struct("!10I")
STATUS_STRUCT = struct.Struct("!14I")
STATUS_EXTENSION_STRUCT = struct.Struct("!6I")
DATA_FORMAT_DUAL_S16 = 0x03100204


class Command(enum.IntEnum):
    DISCOVER = 1
    GET_INFO = 2
    CONFIG = 3
    START = 4
    STOP = 5
    STATUS = 6


class Status(enum.IntEnum):
    OK = 0
    BAD_MESSAGE = 1
    BAD_CONFIG = 2
    BUSY = 3
    HW_ERROR = 4


class PlCommand(enum.IntEnum):
    DISCOVER = 1
    GET_STATUS = 2
    SELECT_ADC = 3
    CONFIG_RATE = 4
    ACQ_START = 5
    ACQ_STOP = 6
    MONITOR_START = 7
    MONITOR_STOP = 8
    SET_ADC_TEST = 9
    CLEAR_STATS = 10


FLAG_RUNNING = 1 << 0
FLAG_FIFO_FULL = 1 << 1
FLAG_FIFO_OVERFLOW = 1 << 2
FLAG_DMA_ERROR = 1 << 3
FLAG_LINK_UP = 1 << 4
FLAG_TRIGGER_SEEN = 1 << 5
FLAG_OTR_A = 1 << 6
FLAG_OTR_B = 1 << 7
FLAG_DCO_ALIVE = 1 << 8
FLAG_SPI_ERROR = 1 << 9

CONFIG_TRIGGER_B = 1 << 0
CONFIG_CHANNEL_SWAP = 1 << 1
CONFIG_TEST_SHIFT = 4
CONFIG_TEST_MASK = 7 << CONFIG_TEST_SHIFT
CHANNEL_A = 1 << 0
CHANNEL_B = 1 << 1

# The final PL-UDP monitor is AD9269-only.  40/80 MSPS remain available to
# Linux through the independent Scope/Event DMA paths, never as continuous
# Ethernet modes.
RATE_TO_SELECTOR = {
    5_000_000: 1,
    10_000_000: 2,
    20_000_000: 3,
}
SELECTOR_TO_RATE = {selector: rate for rate, selector in RATE_TO_SELECTOR.items()}


@dataclass(frozen=True)
class ControlResponse:
    command: int
    request_id: int
    status: int
    sample_rate_hz: int
    block_bytes: int
    ring_blocks: int
    stream_id: int
    flags: int
    fifo_level: int
    fifo_overflow: int
    dma_errors: int
    blocks_completed: int
    blocks_dropped: int
    sample_pair_count: int
    preview_stride: int
    data_format: int
    otr_a_count: int
    otr_b_count: int
    dco_frequency_hz: int
    daq_state: int
    last_error: int
    adc_model: int
    jumbo_enabled: bool
    monitor_enabled: bool
    event_count: int
    dropped_event_count: int
    suppressed_event_count: int
    event_path_enabled: bool
    peak_interval_q16: int


@dataclass(frozen=True)
class DataPacket:
    flags: int
    stream_id: int
    block_sequence: int
    packet_index: int
    packet_count: int
    sample_rate_hz: int
    sample_stride: int
    channel_mask: int
    first_sample_pair: int
    sample_pair_count: int
    payload: memoryview


@dataclass(frozen=True)
class ContinuityUpdate:
    network_packets_lost: int = 0
    pl_samples_lost: int = 0
    reordered_or_duplicate: bool = False


class DaqdContinuityTracker:
    """Track network sequence gaps separately from PL sample-index gaps.

    ``pl_samples_lost`` is authoritative for the missing sample timeline.
    Network packet loss is retained as a transport diagnostic and is never
    added to the sample-index loss, avoiding double counting when both jump.
    """

    def __init__(self) -> None:
        self.expected_sequence: int | None = None
        self.expected_first_sample: int | None = None
        self.network_packets_lost = 0
        self.pl_samples_lost = 0
        self.index_gap_events = 0
        self.last_gap_expected: int | None = None
        self.last_gap_actual: int | None = None

    def reset(self) -> None:
        self.expected_sequence = None
        self.expected_first_sample = None
        self.network_packets_lost = 0
        self.pl_samples_lost = 0
        self.index_gap_events = 0
        self.last_gap_expected = None
        self.last_gap_actual = None

    def observe(self, packet: DataPacket) -> ContinuityUpdate:
        sequence = int(packet.block_sequence) & 0xFFFFFFFF
        first = int(packet.first_sample_pair)
        count = int(packet.sample_pair_count)
        network_gap = 0
        sample_gap = 0
        reordered = False

        if self.expected_sequence is not None:
            delta = (sequence - self.expected_sequence) & 0xFFFFFFFF
            if 0 < delta < 0x80000000:
                network_gap = delta
            elif delta >= 0x80000000:
                # A late/duplicate UDP datagram must not create a false sample
                # gap or move either expected position backwards.
                return ContinuityUpdate(reordered_or_duplicate=True)

        if self.expected_first_sample is not None:
            if first > self.expected_first_sample:
                sample_gap = first - self.expected_first_sample
                self.pl_samples_lost += sample_gap
                self.index_gap_events += 1
                self.last_gap_expected = self.expected_first_sample
                self.last_gap_actual = first
            elif first < self.expected_first_sample:
                return ContinuityUpdate(reordered_or_duplicate=True)

        self.network_packets_lost += network_gap
        self.expected_sequence = (sequence + 1) & 0xFFFFFFFF
        self.expected_first_sample = first + count

        return ContinuityUpdate(
            network_packets_lost=network_gap,
            pl_samples_lost=sample_gap,
            reordered_or_duplicate=reordered,
        )


def pack_pldq(command: PlCommand, transaction_id: int, arg0: int = 0, arg1: int = 0) -> bytes:
    return REQUEST_STRUCT.pack(
        CONTROL_MAGIC,
        ((PROTOCOL_VERSION & 0xFF) << 24) | ((int(command) & 0xFF) << 16),
        transaction_id & 0xFFFFFFFF,
        arg0 & 0xFFFFFFFF,
        arg1 & 0xFFFFFFFF,
    )


def parse_status_packet(data: bytes) -> ControlResponse:
    if len(data) < STATUS_STRUCT.size:
        raise ValueError("short PL status packet")
    values = STATUS_STRUCT.unpack_from(data)
    if values[0] != STATUS_MAGIC:
        raise ValueError("not a DAQS packet")
    version = values[1] >> 24
    if version != PROTOCOL_VERSION:
        raise ValueError(f"unsupported DAQS version {version}")
    state = (values[1] >> 17) & 0x7
    model = (values[1] >> 16) & 0x1
    error = values[1] & 0xFF
    options = values[11]
    extension = (0, 0, 0, 0, 0, 0)
    if len(data) >= STATUS_STRUCT.size + STATUS_EXTENSION_STRUCT.size:
        extension = STATUS_EXTENSION_STRUCT.unpack_from(data, STATUS_STRUCT.size)
    flags = FLAG_LINK_UP
    if state == 3:
        flags |= FLAG_RUNNING
    if values[6]:
        flags |= FLAG_FIFO_OVERFLOW
    if values[4]:
        flags |= FLAG_DCO_ALIVE
    if error:
        flags |= FLAG_DMA_ERROR
    return ControlResponse(
        command=int(Command.STATUS), request_id=values[13], status=0,
        sample_rate_hz=values[3], block_bytes=8_320, ring_blocks=0,
        stream_id=values[2], flags=flags, fifo_level=values[5] & 0x7FFF,
        fifo_overflow=values[6], dma_errors=0, blocks_completed=values[8],
        blocks_dropped=values[7], sample_pair_count=0, preview_stride=1,
        data_format=DATA_FORMAT_DUAL_S16 if model else 0x01080101,
        dco_frequency_hz=values[4],
        daq_state=state, last_error=error, adc_model=model,
        jumbo_enabled=bool(options & 0x4), monitor_enabled=bool(options & 0x2),
        event_count=values[9], dropped_event_count=values[10],
        suppressed_event_count=extension[4],
        event_path_enabled=bool(extension[5] & 0x1),
        otr_a_count=extension[0], otr_b_count=extension[1],
        peak_interval_q16=(extension[3] << 32) | extension[2],
    )


def parse_data_packet(data: bytes) -> DataPacket:
    if len(data) < DATA_HEADER_STRUCT.size:
        raise ValueError("short PL data packet")
    words = DATA_HEADER_STRUCT.unpack_from(data)
    if words[0] != DATA_MAGIC:
        raise ValueError("not a DAQD packet")
    version = words[1] >> 24
    if version != PROTOCOL_VERSION:
        raise ValueError(f"unsupported DAQD version {version}")
    model = (words[1] >> 16) & 0xFF
    channels = (words[1] >> 8) & 0xFF
    header_bytes = words[9] >> 16
    payload_bytes = words[9] & 0xFFFF
    if header_bytes != DATA_HEADER_STRUCT.size or len(data) != header_bytes + payload_bytes:
        raise ValueError("truncated or oversized DAQD payload")
    if model == 2:
        if channels != 2 or payload_bytes % 4:
            raise ValueError("invalid AD9269 DAQD payload")
        pairs = payload_bytes // 4
        channel_mask = CHANNEL_A | CHANNEL_B
    elif model == 1:
        if channels != 1:
            raise ValueError("invalid AD9280 DAQD payload")
        pairs = payload_bytes
        channel_mask = CHANNEL_A
    else:
        raise ValueError("unknown DAQD ADC model")
    return DataPacket(
        flags=words[8], stream_id=words[2], block_sequence=words[3],
        packet_index=0, packet_count=1, sample_rate_hz=words[4],
        sample_stride=1, channel_mask=channel_mask,
        first_sample_pair=(words[5] << 32) | words[6],
        sample_pair_count=pairs, payload=memoryview(data)[header_bytes:],
    )


def pack_control_request(*args, **kwargs):
    """Removed v3 wire encoder; callers must use ``ControlClient.request``."""
    raise RuntimeError("PLDQ v1 is command-oriented; use ControlClient.request")


def parse_control_response(data: bytes) -> ControlResponse:
    return parse_status_packet(data)
