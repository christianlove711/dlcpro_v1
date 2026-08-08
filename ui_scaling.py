from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from PySide6.QtCore import (
    QByteArray, QEvent, QMargins, QObject, QSettings, QSize, QTimer,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QLabel, QWidget


SETTINGS_ORGANIZATION = "DLCProControl"
SETTINGS_APPLICATION = "DLCProControl"

SCALE_OPTIONS: tuple[tuple[str, float | None], ...] = (
    ("auto", None),
    ("80%", 0.80),
    ("100%", 1.00),
    ("120%", 1.20),
    ("140%", 1.40),
)


def _screen_for_window(window: QWidget):
    center = window.frameGeometry().center()
    screen = QGuiApplication.screenAt(center)
    if screen is not None:
        return screen
    parent = window.parentWidget()
    if parent is not None and parent.screen() is not None:
        return parent.screen()
    return window.screen() or QGuiApplication.primaryScreen()


def screen_fit_scale(window: QWidget | None = None) -> float:
    screen = _screen_for_window(window) if window is not None else QGuiApplication.primaryScreen()
    if screen is None:
        return 1.0
    available = screen.availableGeometry().size()
    logical_scale = min(available.width() / 1440.0, available.height() / 900.0)
    return max(0.80, min(1.20, logical_scale))


def fit_size_to_screen(size: QSize, window: QWidget | None = None, margin: int = 32) -> QSize:
    screen = _screen_for_window(window) if window is not None else QGuiApplication.primaryScreen()
    if screen is None:
        return size
    available = screen.availableGeometry()
    return QSize(
        min(size.width(), max(360, available.width() - margin * 2)),
        min(size.height(), max(280, available.height() - margin * 2)),
    )


def fit_window_to_screen(window: QWidget, margin: int = 16, *, center: bool = False) -> None:
    """Keep the complete native frame, especially its title bar, on-screen."""

    screen = _screen_for_window(window)
    if screen is None:
        return
    available = screen.availableGeometry().adjusted(margin, margin, -margin, -margin)
    target = window.frameGeometry()
    frame_extra_width = max(0, target.width() - window.width())
    frame_extra_height = max(0, target.height() - window.height())
    maximum_client_width = max(360, available.width() - frame_extra_width)
    maximum_client_height = max(280, available.height() - frame_extra_height)
    if (window.width() > maximum_client_width or
            window.height() > maximum_client_height):
        window.resize(
            min(window.width(), maximum_client_width),
            min(window.height(), maximum_client_height),
        )
        target = window.frameGeometry()
    if center:
        target.moveCenter(available.center())
    if target.width() <= available.width():
        target.moveLeft(max(
            available.left(),
            min(target.left(), available.right() - target.width() + 1),
        ))
    else:
        target.moveLeft(available.left())
    # Prioritize the title bar over the bottom edge.  Moving an oversized
    # window upward to expose its bottom is what previously hid all native
    # minimize/maximize/close controls above the desktop.
    if target.height() <= available.height():
        target.moveTop(max(
            available.top(),
            min(target.top(), available.bottom() - target.height() + 1),
        ))
    else:
        target.moveTop(available.top())
    window.move(target.topLeft())


def schedule_window_fit(window: QWidget, margin: int = 16,
                        *, center: bool = False) -> None:
    """Fit now and again after Windows has created the decorated native frame."""

    def apply_if_alive() -> None:
        try:
            if bool(window.property("suppressScheduledScreenFit")):
                return
            fit_window_to_screen(window, margin, center=center)
        except RuntimeError:
            return

    apply_if_alive()
    QTimer.singleShot(0, apply_if_alive)
    QTimer.singleShot(120, apply_if_alive)


def apply_font_scale(app: QApplication, scale: float) -> None:
    font = app.font()
    base_size = app.property("basePointSize")
    if base_size is None:
        base_size = font.pointSizeF()
        if base_size <= 0:
            base_size = 9.0
        base_size = max(10.5, base_size)
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


def _scaled_size(size: QSize, scale: float) -> QSize:
    return QSize(max(1, round(size.width() * scale)), max(1, round(size.height() * scale)))


def scale_widget_metrics(root: QWidget, scale: float) -> None:
    for widget in (root, *root.findChildren(QWidget)):
        if isinstance(widget, QLabel) and not widget.property("preserveSingleLine"):
            widget.setWordWrap(True)
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
            widget.setFixedSize(_scaled_size(base_fixed_size, scale))

        icon_getter = getattr(widget, "icon", None)
        icon = icon_getter() if callable(icon_getter) else None
        if hasattr(icon, "isNull") and not icon.isNull():
            base_icon_size = widget.property("baseIconSize")
            if base_icon_size is None:
                base_icon_size = widget.iconSize()
                widget.setProperty("baseIconSize", base_icon_size)
            widget.setIconSize(_scaled_size(base_icon_size, scale))


def _metric_stylesheet(scale: float) -> str:
    control_height = round(28 * scale)
    horizontal_padding = round(8 * scale)
    vertical_padding = round(4 * scale)
    tab_padding_x = round(10 * scale)
    tab_padding_y = round(6 * scale)
    page_title_size = round(19 * scale)
    section_title_size = round(17 * scale)
    return f"""
        QPushButton, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QLabel#StatusBadge {{
            min-height: {control_height}px;
            padding: {vertical_padding}px {horizontal_padding}px;
        }}
        QLabel#StatusBadge {{ max-height: {control_height}px; }}
        QTabBar::tab {{
            padding: {tab_padding_y}px {tab_padding_x}px;
        }}
        QLabel#PageTitle {{ font-size: {page_title_size}px; }}
        QLabel#SectionTitle {{ font-size: {section_title_size}px; }}
    """


class UiScaleManager:
    def __init__(
        self,
        app: QApplication,
        base_stylesheet: str,
        settings: QSettings | None = None,
    ) -> None:
        self.app = app
        self.base_stylesheet = base_stylesheet
        self.settings = settings or QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        self._manual_scale = self._load_scale()
        self.windows: list[QWidget] = []

    @property
    def scale(self) -> float:
        reference = self.windows[0] if self.windows else None
        return self._manual_scale if self._manual_scale is not None else screen_fit_scale(reference)

    @property
    def selected_scale(self) -> float | None:
        return self._manual_scale

    def _load_scale(self) -> float | None:
        value = self.settings.value("ui/scale", "auto")
        if value in (None, "", "auto"):
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed in {0.8, 1.0, 1.2, 1.4} else None

    def set_scale(self, scale: float | None) -> None:
        self._manual_scale = scale
        self.settings.setValue("ui/scale", "auto" if scale is None else scale)
        self.apply()

    def register_window(self, window: QWidget) -> None:
        if window not in self.windows:
            self.windows.append(window)

    def register_windows(self, windows: Iterable[QWidget]) -> None:
        for window in windows:
            self.register_window(window)

    def apply(self) -> None:
        scale = self.scale
        apply_font_scale(self.app, scale)
        self.app.setStyleSheet(self.base_stylesheet + _metric_stylesheet(scale))
        for window in self.windows:
            scale_widget_metrics(window, scale)


@dataclass(frozen=True, slots=True)
class WindowRegistration:
    window_id: str
    default_size: QSize


class WindowLayoutManager(QObject):
    def __init__(self, settings: QSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        self._registrations: dict[QWidget, WindowRegistration] = {}
        self._restored: set[QWidget] = set()

    def register_window(self, window: QWidget, window_id: str, width: int, height: int) -> None:
        self._registrations[window] = WindowRegistration(window_id, QSize(width, height))
        window.installEventFilter(self)
        window._window_layout_manager = self

    def register_windows(self, windows: Iterable[tuple[QWidget, str, int, int]]) -> None:
        for window, window_id, width, height in windows:
            self.register_window(window, window_id, width, height)

    def prepare_show(self, window: QWidget) -> None:
        if window not in self._registrations:
            return
        if window not in self._restored:
            self.restore_window(window)
        else:
            fit_window_to_screen(window)

    def restore_window(self, window: QWidget) -> None:
        registration = self._registrations.get(window)
        if registration is None:
            return
        raw = self.settings.value(f"windows/{registration.window_id}/geometry")
        restored = isinstance(raw, QByteArray) and not raw.isEmpty() and window.restoreGeometry(raw)
        if not restored:
            window.resize(fit_size_to_screen(registration.default_size, window))
            fit_window_to_screen(window, center=True)
        else:
            fit_window_to_screen(window)
        self._restored.add(window)

    def save_window(self, window: QWidget) -> None:
        registration = self._registrations.get(window)
        if registration is None or window not in self._restored:
            return
        self.settings.setValue(f"windows/{registration.window_id}/geometry", window.saveGeometry())

    def save_all(self) -> None:
        for window in self._registrations:
            self.save_window(window)
        self.settings.sync()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        registrations = getattr(self, "_registrations", {})
        if isinstance(watched, QWidget) and watched in registrations:
            if event.type() == QEvent.Type.Show:
                self.prepare_show(watched)
                schedule_window_fit(watched)
            elif event.type() in {QEvent.Type.Hide, QEvent.Type.Close}:
                self.save_window(watched)
        return super().eventFilter(watched, event)
