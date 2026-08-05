from __future__ import annotations

import threading
import time

from device_task_coordinator import DeviceTaskCoordinator


def _drain(coordinator: DeviceTaskCoordinator, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while coordinator.has_work and time.monotonic() < deadline:
        coordinator.poll_completed()
        time.sleep(0.005)
    assert not coordinator.has_work


def test_user_tasks_run_fifo() -> None:
    coordinator = DeviceTaskCoordinator(thread_name_prefix="test-fifo")
    executed: list[int] = []
    completed: list[int] = []
    try:
        for value in (1, 2, 3):
            coordinator.submit(
                lambda value=value: executed.append(value) or value,
                lambda ok, result, kind: completed.append(int(result)),
            )
        _drain(coordinator)
        assert executed == [1, 2, 3]
        assert completed == [1, 2, 3]
    finally:
        coordinator.shutdown()


def test_poll_is_coalesced_and_pending_write_keeps_latest_value() -> None:
    coordinator = DeviceTaskCoordinator(thread_name_prefix="test-coalesce")
    release = threading.Event()
    executed: list[str] = []
    try:
        assert coordinator.submit(lambda: release.wait(1), lambda *_: None, kind="poll")
        assert not coordinator.submit(lambda: None, lambda *_: None, kind="poll")

        assert coordinator.submit(
            lambda: executed.append("old"),
            lambda *_: None,
            coalesce_key="current_set",
        )
        assert coordinator.submit(
            lambda: executed.append("latest"),
            lambda *_: None,
            coalesce_key="current_set",
        )
        release.set()
        _drain(coordinator)
        assert executed == ["latest"]
    finally:
        coordinator.shutdown()


def test_disconnect_stops_polling_and_clears_pending() -> None:
    coordinator = DeviceTaskCoordinator(thread_name_prefix="test-disconnect")
    release = threading.Event()
    try:
        coordinator.submit(lambda: release.wait(1), lambda *_: None)
        coordinator.submit(lambda: None, lambda *_: None)
        coordinator.stop_polling_and_clear()
        assert not coordinator.submit(lambda: None, lambda *_: None, kind="poll")
        release.set()
        _drain(coordinator)
        coordinator.resume_polling()
        assert coordinator.submit(lambda: None, lambda *_: None, kind="poll")
        _drain(coordinator)
    finally:
        coordinator.shutdown()
