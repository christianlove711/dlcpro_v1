from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QObject

from controllers.laser_controller import LaserController
from controllers.scan_lock_controller import ScanLockController


class _Spin:
    def __init__(self, value: float) -> None:
        self._value = value

    def value(self) -> float:
        return self._value


class _Combo:
    def __init__(self, value: int) -> None:
        self._value = value

    def currentData(self) -> int:  # noqa: N802
        return self._value


class _Service:
    is_connected = True

    def __init__(self) -> None:
        self.writes: list[tuple[str, float | int]] = []

    def set_feedforward_factor(self, value: float) -> object:
        self.writes.append(("feedforward_factor", value))
        return object()

    def set_sc_output_channel(self, value: int) -> object:
        self.writes.append(("sc_output_channel", value))
        return object()


class _Owner(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.service = _Service()
        self.snapshot = SimpleNamespace(feedforward_factor=1.0, sc_output_channel=50)
        self.feedforward_programmatic_update = False
        self.sc_programmatic_update = False
        self.feedforward_factor_spin = _Spin(2.5)
        self.scan_output_combo = _Combo(51)
        self.submissions = 0

    def submit_device_task(self, fn, on_success=None, *, coalesce_key=None) -> bool:
        self.submissions += 1
        fn()
        return True


def test_laser_write_uses_task_entry_and_ignores_programmatic_update(qapp) -> None:
    owner = _Owner()
    controller = LaserController(owner)
    try:
        controller._on_feedforward_factor_finished()
        assert owner.service.writes == [("feedforward_factor", 2.5)]
        assert owner.submissions == 1

        owner.feedforward_programmatic_update = True
        controller._on_feedforward_factor_finished()
        assert owner.submissions == 1
    finally:
        controller.shutdown()


def test_scan_lock_write_uses_task_entry_and_ignores_programmatic_update(qapp) -> None:
    owner = _Owner()
    controller = ScanLockController(owner)

    controller._on_sc_output_changed()
    assert owner.service.writes == [("sc_output_channel", 51)]
    assert owner.submissions == 1

    owner.sc_programmatic_update = True
    controller._on_sc_output_changed()
    assert owner.submissions == 1
