from __future__ import annotations

import enum
import struct
from dataclasses import dataclass


PROTOCOL_VERSION = 1
CONTROL_MAGIC = 0x44415143
DATA_MAGIC = 0x44415144
CONTROL_PORT = 5000
DATA_PORT = 5001
BLOCK_BYTES = 262_144
PAYLOAD_BYTES = 1_440

CONTROL_REQUEST = struct.Struct("!IHHIIHHIII")
CONTROL_RESPONSE = struct.Struct("!IHH12IQ")
DATA_HEADER = struct.Struct("!IBBHHHHHIIQ")


class Command(enum.IntEnum):
    DISCOVER = 1
    GET_INFO = 2
    CONFIG = 3
    START = 4
    STOP = 5
    STATUS = 6
    RESPONSE = 0x8000


class Status(enum.IntEnum):
    OK = 0
    BAD_MESSAGE = 1
    BAD_CONFIG = 2
    BUSY = 3
    HW_ERROR = 4


FLAG_RUNNING = 1 << 0
FLAG_FIFO_FULL = 1 << 1
FLAG_FIFO_OVERFLOW = 1 << 2
FLAG_DMA_ERROR = 1 << 3
FLAG_LINK_UP = 1 << 4
FLAG_TRIGGER_SEEN = 1 << 5


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
    sample_count: int


@dataclass(frozen=True)
class DataPacket:
    flags: int
    stream_id: int
    packet_index: int
    packet_count: int
    sample_count: int
    block_sequence: int
    sample_rate_hz: int
    first_sample: int
    payload: memoryview


def pack_control_request(
    command: int,
    request_id: int,
    *,
    sample_rate_hz: int = 0,
    trigger_mode: int = 0,
    threshold: int = 0,
    flags: int = 0,
    value0: int = 0,
    value1: int = 0,
) -> bytes:
    return CONTROL_REQUEST.pack(
        CONTROL_MAGIC,
        PROTOCOL_VERSION,
        int(command),
        request_id,
        sample_rate_hz,
        trigger_mode,
        threshold,
        flags,
        value0,
        value1,
    )


def parse_control_response(data: bytes) -> ControlResponse:
    if len(data) != CONTROL_RESPONSE.size:
        raise ValueError(f"control response is {len(data)} bytes, expected 64")
    values = CONTROL_RESPONSE.unpack(data)
    if values[0] != CONTROL_MAGIC or values[1] != PROTOCOL_VERSION:
        raise ValueError("control response magic/version mismatch")
    return ControlResponse(
        command=values[2],
        request_id=values[3],
        status=values[4],
        sample_rate_hz=values[5],
        block_bytes=values[6],
        ring_blocks=values[7],
        stream_id=values[8],
        flags=values[9],
        fifo_level=values[10],
        fifo_overflow=values[11],
        dma_errors=values[12],
        blocks_completed=values[13],
        blocks_dropped=values[14],
        sample_count=values[15],
    )


def parse_data_packet(datagram: bytes) -> DataPacket:
    if len(datagram) < DATA_HEADER.size:
        raise ValueError("short DAQ data packet")
    values = DATA_HEADER.unpack_from(datagram)
    if values[0] != DATA_MAGIC or values[1] != PROTOCOL_VERSION:
        raise ValueError("data packet magic/version mismatch")
    header_bytes = values[3]
    sample_count = values[7]
    if header_bytes != DATA_HEADER.size:
        raise ValueError(f"unsupported data header size {header_bytes}")
    if len(datagram) != header_bytes + sample_count:
        raise ValueError("data packet sample count does not match payload")
    return DataPacket(
        flags=values[2],
        stream_id=values[4],
        packet_index=values[5],
        packet_count=values[6],
        sample_count=sample_count,
        block_sequence=values[8],
        sample_rate_hz=values[9],
        first_sample=values[10],
        payload=memoryview(datagram)[header_bytes:],
    )
