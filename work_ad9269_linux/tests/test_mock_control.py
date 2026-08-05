"""Host-only dual-DMA register and ordering contract tests."""
from __future__ import annotations

import errno
import pathlib
import unittest

RATES = {5_000_000: 1, 10_000_000: 2, 20_000_000: 3,
         40_000_000: 4, 80_000_000: 5}


class MockDriver:
    def __init__(self):
        self.running = False
        self.trace: list[str] = []

    def set_threshold(self, _threshold: int):
        raise OSError(errno.EOPNOTSUPP, "fixed RTL parameter")

    def start(self, mode: int, rate: int):
        if self.running:
            raise OSError(errno.EBUSY, "running")
        if mode not in (0, 1) or rate not in RATES:
            raise OSError(errno.EINVAL, "config")
        slots = 16 if mode == 0 else 64
        arm = "scope_arm" if mode == 0 else "event_arm"
        self.trace.extend(("pl_stop", f"mode:{mode}",
                           f"rate:{RATES[rate]}"))
        self.trace.extend(f"submit:{mode}:{slot}" for slot in range(slots))
        self.trace.extend((f"issue:{mode}", arm, "config_commit", "pl_start"))
        self.running = True

    def stop(self):
        self.trace.extend(("pl_stop", "event_disarm", "scope_abort",
                           "terminate:event", "terminate:scope",
                           "wake_waiters"))
        self.running = False


class ControlContractTests(unittest.TestCase):
    def test_device_tree_requests_both_s2mm_channels(self):
        dtsi = (pathlib.Path(__file__).parents[1] /
                "zynq-daq-events.dtsi").read_text(encoding="utf-8")
        self.assertIn("dmas = <&axi_dma_0 1>, <&scope_dma_1 1>;", dtsi)

    def test_event_arm_follows_all_64_descriptors(self):
        driver = MockDriver()
        driver.start(1, 80_000_000)
        self.assertEqual(
            driver.trace[3:67],
            [f"submit:1:{slot}" for slot in range(64)],
        )
        self.assertEqual(driver.trace[-4:],
                         ["issue:1", "event_arm", "config_commit", "pl_start"])

    def test_scope_arm_follows_all_16_descriptors(self):
        driver = MockDriver()
        driver.start(0, 80_000_000)
        self.assertEqual(
            driver.trace[3:19],
            [f"submit:0:{slot}" for slot in range(16)],
        )
        self.assertEqual(driver.trace[-4:],
                         ["issue:0", "scope_arm", "config_commit", "pl_start"])

    def test_stop_disarms_both_before_terminating(self):
        driver = MockDriver()
        driver.start(0, 20_000_000)
        driver.stop()
        self.assertEqual(
            driver.trace[-6:],
            ["pl_stop", "event_disarm", "scope_abort",
             "terminate:event", "terminate:scope", "wake_waiters"],
        )

    def test_removed_rates_and_fixed_threshold_are_rejected(self):
        with self.assertRaises(OSError) as caught:
            MockDriver().start(1, 3_000_000)
        self.assertEqual(caught.exception.errno, errno.EINVAL)
        with self.assertRaises(OSError) as caught:
            MockDriver().set_threshold(512)
        self.assertEqual(caught.exception.errno, errno.EOPNOTSUPP)

    def test_c_source_contains_two_independent_channels_and_rings(self):
        source = (pathlib.Path(__file__).parents[1] / "driver" /
                  "zynq_daq_events.c").read_text(encoding="utf-8")
        self.assertIn('"event-rx"', source)
        self.assertIn('"scope-rx"', source)
        self.assertIn("struct daq_ring event;", source)
        self.assertIn("struct daq_ring scope;", source)
        self.assertIn("ZYNQ_DAQ_RING_SLOTS", source)
        self.assertIn("ZYNQ_SCOPE_RING_SLOTS", source)
        self.assertIn("ZYNQ_DAQ_FRAME_BYTES", source)
        self.assertIn("ZYNQ_SCOPE_FRAME_BYTES", source)
        self.assertIn("return -EOPNOTSUPP;", source)
        self.assertIn("vma->vm_pgoff = 0;", source)
        self.assertLess(source.index("dma_async_issue_pending(ring->chan)"),
                        source.index("writel(DAQ_EVENT_ENABLE"))
        self.assertLess(source.index("writel(DAQ_CTL_STOP"),
                        source.index("dmaengine_terminate_sync(d->event.chan)"))


if __name__ == "__main__":
    unittest.main()
