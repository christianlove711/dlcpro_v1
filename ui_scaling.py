from __future__ import annotations

import re
from collections.abc import Iterable

from PySide6.QtCore import QMargins, QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget


SCALE_OPTIONS: tuple[tuple[str, float | None], ...] = (
    ("auto", None),
    ("50%", 0.50),
    ("60%", 0.60),
    ("75%", 0.75),
    ("90%", 0.90),
    ("100%", 1.00),
    ("110%", 1.10),
    ("125%", 1.25),
    ("150%", 1.50),
)


_PX_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)px")


def screen_fit_scale(reference_size: QSize | None = None) -> float:
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return 1.0
    available = screen.availableGeometry().size()
    reference = reference_size or QSize(1120, 900)
    width_scale = available.width() / max(reference.width(), 1)
    height_scale = available.height() / max(reference.height(), 1)
    return max(0.50, min(1.25, min(width_scale, height_scale, 1.0)))


def scaled_size(width: int, height: int, scale: float) -> QSize:
    return QSize(max(1, round(width * scale)), max(1, round(height * scale)))


def fit_size_to_screen(size: QSize, margin: int = 48) -> QSize:
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return size
    available = screen.availableGeometry()
    return QSize(
        min(size.width(), max(320, available.width() - margin)),
        min(size.height(), max(240, available.height() - margin)),
    )


def fit_window_to_screen(window: QWidget, margin: int = 48) -> None:
    screen = window.screen() or QGuiApplication.primaryScreen()
    if screen is None:
        return
    available = screen.availableGeometry()
    geometry = window.frameGeometry()
    if geometry.width() > available.width() - margin or geometry.height() > available.height() - margin:
        window.resize(
            min(geometry.width(), max(320, available.width() - margin)),
            min(geometry.height(), max(240, available.height() - margin)),
        )
        geometry = window.frameGeometry()
    geometry.moveCenter(available.center())
    if geometry.left() < available.left():
        geometry.moveLeft(available.left())
    if geometry.top() < available.top():
        geometry.moveTop(available.top())
    if geometry.right() > available.right():
        geometry.moveRight(available.right())
    if geometry.bottom() > available.bottom():
        geometry.moveBottom(available.bottom())
    window.move(geometry.topLeft())


def scale_stylesheet(stylesheet: str, scale: float) -> str:
    def replace(match: re.Match[str]) -> str:
        value = float(match.group("value"))
        scaled = max(1, round(value * scale))
        return f"{scaled}px"

    return _PX_PATTERN.sub(replace, stylesheet)


def apply_font_scale(app: QApplication, scale: float) -> None:
    font = app.font()
    base_size = app.property("basePointSize")
    if base_size is None:
        base_size = font.pointSizeF()
        if base_size <= 0:
            base_size = 9.0
        app.setProperty("basePointSize", base_size)
    font.setPointSizeF(max(7.0, float(base_size) * scale))
    app.setFont(font)


def _scaled_margins(margins: QMargins, scale: float) -> QMargins:
    return QMargins(
        round(margins.left() * scale),
        round(margins.top() * scale),
        round(margins.right() * scale),
        round(margins.bottom() * scale),
    )


def scale_widget_metrics(root: QWidget, scale: float) -> None:
    for widget in (root, *root.findChildren(QWidget)):
        layout = widget.layout()
        if layout is not None:
            base_margins = layout.property("baseContentsMargins")
            if base_margins is None:
                base_margins = layout.contentsMargins()
                layout.setProperty("baseContentsMargins", base_margins)
            layout.setContentsMargins(_scaled_margins(base_margins, scale))

            base_spacing = layout.property("baseSpacing")
            if base_spacing is None:
                base_spacing = layout.spacing()
                layout.setProperty("baseSpacing", base_spacing)
            if int(base_spacing) >= 0:
                layout.setSpacing(max(0, round(int(base_spacing) * scale)))

        minimum = widget.minimumSize()
        maximum = widget.maximumSize()
        if minimum == maximum and maximum.width() < 16_000_000 and maximum.height() < 16_000_000:
            base_fixed_size = widget.property("baseFixedSize")
            if base_fixed_size is None:
                base_fixed_size = QSize(minimum.width(), minimum.height())
                widget.setProperty("baseFixedSize", base_fixed_size)
            widget.setFixedSize(scaled_size(base_fixed_size.width(), base_fixed_size.height(), scale))


class UiScaleManager:
    def __init__(self, app: QApplication, base_stylesheet: str, scale: float | None = None) -> None:
        self.app = app
        self.base_stylesheet = base_stylesheet
        self._manual_scale = scale
        self.windows: list[tuple[QMainWindow, QSize]] = []

    @property
    def scale(self) -> float:
        return self._manual_scale if self._manual_scale is not None else screen_fit_scale()

    def set_scale(self, scale: float | None) -> None:
        self._manual_scale = scale
        self.apply()

    def register_window(self, window: QMainWindow, width: int, height: int) -> None:
        size = QSize(width, height)
        self.windows.append((window, size))
        self._resize_window(window, size)

    def register_windows(self, windows: Iterable[tuple[QMainWindow, int, int]]) -> None:
        for window, width, height in windows:
            self.register_window(window, width, height)

    def apply(self) -> None:
        scale = self.scale
        apply_font_scale(self.app, scale)
        self.app.setStyleSheet(scale_stylesheet(self.base_stylesheet, scale))
        for window, base_size in self.windows:
            self._resize_window(window, base_size)

    def _resize_window(self, window: QMainWindow, base_size: QSize) -> None:
        scale_widget_metrics(window, self.scale)
        window.resize(fit_size_to_screen(scaled_size(base_size.width(), base_size.height(), self.scale)))
        fit_window_to_screen(window)
