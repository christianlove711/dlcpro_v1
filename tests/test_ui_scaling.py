from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QWidget

from ui_scaling import SCALE_OPTIONS, UiScaleManager, WindowLayoutManager


def _settings(path) -> QSettings:
    return QSettings(str(path), QSettings.Format.IniFormat)


def test_scale_options_are_the_supported_five_levels() -> None:
    assert SCALE_OPTIONS == (
        ("auto", None),
        ("80%", 0.8),
        ("100%", 1.0),
        ("120%", 1.2),
        ("140%", 1.4),
    )


def test_scale_change_does_not_move_or_resize_window(qapp, tmp_path) -> None:
    window = QWidget()
    window.setGeometry(120, 140, 640, 480)
    manager = UiScaleManager(qapp, "", _settings(tmp_path / "scale.ini"))
    manager.register_window(window)
    before = window.geometry()
    for scale in (0.8, 1.0, 1.2, 1.4, None):
        manager.set_scale(scale)
        assert window.geometry() == before


def test_window_geometry_is_restored(qapp, tmp_path) -> None:
    settings = _settings(tmp_path / "geometry.ini")
    manager = WindowLayoutManager(settings)
    first = QWidget()
    manager.register_window(first, "test", 640, 480)
    manager.prepare_show(first)
    first.setGeometry(80, 90, 520, 410)
    manager.save_window(first)

    second_manager = WindowLayoutManager(settings)
    second = QWidget()
    second_manager.register_window(second, "test", 640, 480)
    second_manager.prepare_show(second)
    assert second.size() == first.size()
