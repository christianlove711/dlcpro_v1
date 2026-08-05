from __future__ import annotations

import threading
import time

from daq_pc.daq_udp_dual import DualSampleRingBuffer, UdpReceiverCore


def test_wait_for_stream_rejects_stale_stream_and_accepts_requested_stream():
    core = UdpReceiverCore(DualSampleRingBuffer(capacity=32), port=5001)
    core._stream_id = 10
    core._packets = 8

    assert not core.wait_for_stream(11, timeout=0.01)

    def publish_new_stream():
        time.sleep(0.02)
        core._stream_id = 11
        core._packets += 1
        core._stream_event.set()

    publisher = threading.Thread(target=publish_new_stream)
    publisher.start()
    assert core.wait_for_stream(11, timeout=0.5)
    publisher.join()


def test_wait_for_stream_stops_waiting_when_receiver_stops():
    core = UdpReceiverCore(DualSampleRingBuffer(capacity=32), port=5001)

    def stop_receiver():
        time.sleep(0.02)
        core.stop()
        core._stream_event.set()

    stopper = threading.Thread(target=stop_receiver)
    stopper.start()
    assert not core.wait_for_stream(1, timeout=0.5)
    stopper.join()
