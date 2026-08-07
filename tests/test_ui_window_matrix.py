from __future__ import annotations

from itertools import combinations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDialogButtonBox

import ui_scaling
from app import MainWindow, create_safety_notice
from ui_text import TEXT


def _assert_no_overlap(widgets) -> None:
    visible = [widget for widget in widgets if widget.isVisible()]
    for left, right in combinations(visible, 2):
        assert not left.geometry().intersects(right.geometry()), (left.objectName(), right.objectName())


def test_all_windows_reflow_across_scale_language_and_resolution(qapp, tmp_path, monkeypatch) -> None:
    settings = QSettings(str(tmp_path / "ui-matrix.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(ui_scaling, "QSettings", lambda *args, **kwargs: settings)
    window = MainWindow()
    assert len(window.nav_buttons) == 3
    assert not hasattr(window, "overview_button")
    assert not hasattr(window, "scan_lock_button")
    assert not hasattr(window, "auto_lock_button")
    assert window.parameter_group.maximumHeight() == 170
    assert window.network_info.minimumHeight() == 105
    assert window.serial_ports_info.minimumHeight() == 105
    assert "max-width: 360px" not in qapp.styleSheet()
    safety_notice = create_safety_notice(window)
    safety_label = safety_notice.findChild(type(window.hero_title), "qt_msgbox_label")
    assert safety_label is not None
    assert safety_label.wordWrap()
    assert safety_label.maximumWidth() == 520
    assert safety_label.text() == TEXT[window.language]["safety_text"]
    auxiliary = (
        window.laser_window,
        window.falc_window,
        window.scan_lock_window,
        window.auto_lock_window,
        window.auto_lock_window.config_window,
        window.auto_lock_window.waveform_window,
        window.auto_lock_window.log_window,
    )
    try:
        window.show()
        for item in auxiliary:
            item.show()
        qapp.processEvents()

        for width, height in ((1366, 768), (1920, 1080), (2560, 1440)):
            for scale in (None, 0.8, 1.0, 1.2, 1.4):
                window.scale_manager.set_scale(scale)
                for language in ("zh", "en"):
                    window.language = language
                    window._apply_texts()
                    window.resize(width - 64, height - 64)
                    for item in auxiliary:
                        item.resize(min(1180, width - 64), min(900, height - 64))
                    qapp.processEvents()

                    _assert_no_overlap(window.nav_buttons)
                    _assert_no_overlap(
                        (
                            window.auto_lock_window.algorithm_button,
                            window.auto_lock_window.falc_button,
                            window.auto_lock_window.waveform_button,
                            window.auto_lock_window.log_button,
                        )
                    )
                    assert window.auto_lock_window.acq_status_value.text() == TEXT[language]["auto_lock_disconnected"]
                    assert window.auto_lock_window.confidence_value.text() == TEXT[language]["auto_lock_waiting_frame"]
                    assert (
                        window.auto_lock_window.config_window.dialog_buttons.button(QDialogButtonBox.Ok).text()
                        == TEXT[language]["dialog_ok"]
                    )
                    assert window.centralWidget() is not None
                    assert all(
                        (item.centralWidget() is not None if hasattr(item, "centralWidget") else item.layout() is not None)
                        for item in auxiliary
                    )
    finally:
        for item in auxiliary:
            item.hide()
        window.hide()
        window.task_coordinator.shutdown()


def test_adc_entry_opens_acquisition_without_scope(qapp, tmp_path, monkeypatch) -> None:
    settings = QSettings(str(tmp_path / "adc-entry.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(ui_scaling, "QSettings", lambda *args, **kwargs: settings)
    window = MainWindow()
    try:
        window._open_daq_window()
        qapp.processEvents()
        assert window.daq_window is not None
        assert window.daq_window.isVisible()
        assert not window.daq_window.auto_lock_workspace.isVisible()
        assert not window.daq_window.scope_window.isVisible()
    finally:
        if window.daq_window is not None:
            window.daq_window.close()
        window.hide()
        window.task_coordinator.shutdown()
