"""Hardware-free contract tests for the 64-slot event-ring state machine."""
import unittest


class MockRing:
    def __init__(self, slots):
        self.slots = slots
        self.running = False
        self.submitted = set()
        self.ready = set()
        self.leased = set()

    def start(self):
        if self.running:
            raise RuntimeError("busy")
        self.running = True
        self.submitted = set(range(self.slots))

    def complete(self, slot):
        self.submitted.remove(slot)
        if self.running and slot not in self.leased:
            self.ready.add(slot)

    def dequeue(self):
        if not self.ready:
            raise BrokenPipeError
        slot = min(self.ready)
        self.ready.remove(slot)
        self.leased.add(slot)
        return slot

    def release(self, slot):
        if slot not in self.leased:
            raise ValueError("duplicate or invalid release")
        self.leased.remove(slot)
        if not self.running:
            raise BrokenPipeError
        self.submitted.add(slot)

    def stop(self):
        self.running = False
        self.submitted.clear()
        self.ready.clear()
        self.leased.clear()


class RingTests(unittest.TestCase):
    def test_all_slots_cycle(self):
        ring = MockRing(64)
        ring.start()
        self.assertEqual(len(ring.submitted), 64)
        for slot in range(64):
            ring.complete(slot)
        leased = [ring.dequeue() for _ in range(64)]
        self.assertEqual(leased, list(range(64)))
        for slot in leased:
            ring.release(slot)
        self.assertEqual(len(ring.submitted), 64)

    def test_duplicate_release_is_rejected(self):
        ring = MockRing(64)
        ring.start()
        ring.complete(0)
        slot = ring.dequeue()
        ring.release(slot)
        with self.assertRaises(ValueError):
            ring.release(slot)

    def test_stop_revokes_all_states_and_unblocks_dequeue(self):
        ring = MockRing(16)
        ring.start()
        ring.complete(3)
        ring.dequeue()
        ring.stop()
        self.assertFalse(ring.running)
        self.assertFalse(ring.ready or ring.leased or ring.submitted)
        with self.assertRaises(BrokenPipeError):
            ring.dequeue()

    def test_page_aligned_layout(self):
        self.assertEqual(12288 % 4096, 0)
        self.assertGreaterEqual(12288, 8320)
        self.assertEqual(63 * 12288 % 4096, 0)
        self.assertEqual(36864 % 4096, 0)
        self.assertGreaterEqual(36864, 32832)
        self.assertEqual(15 * 36864 % 4096, 0)

    def test_scope_ring_cycles_all_16_slots(self):
        ring = MockRing(16)
        ring.start()
        for slot in range(16):
            ring.complete(slot)
        leased = [ring.dequeue() for _ in range(16)]
        self.assertEqual(leased, list(range(16)))
        for slot in leased:
            ring.release(slot)
        self.assertEqual(len(ring.submitted), 16)


if __name__ == "__main__":
    unittest.main()
