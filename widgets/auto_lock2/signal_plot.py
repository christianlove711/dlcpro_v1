from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from controllers.auto_lock2_acquisition import AcquisitionFrame


class AutoLock2SignalPlot(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(280)
        self._frame: AcquisitionFrame | None = None
        self._message = ""
        self._peak_fraction: float | None = None
        self._zero_fraction: float | None = None
        self._labels = {
            "transmission": "Transmission",
            "error": "Error",
            "empty": "No signal frame yet.",
            "peak": "Peak",
            "zero": "Error zero",
        }
        self._plot_rect = QRectF()

    def set_labels(self, labels: dict[str, str]) -> None:
        self._labels.update(labels)
        self.update()

    def set_frame(
        self,
        frame: AcquisitionFrame | None,
        message: str = "",
        peak_fraction: float | None = None,
        zero_fraction: float | None = None,
    ) -> None:
        self._frame = frame
        self._message = message
        self._peak_fraction = peak_fraction
        self._zero_fraction = zero_fraction
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#343434"))
        self._plot_rect = QRectF(62.0, 24.0, max(160.0, self.width() - 92.0), max(160.0, self.height() - 72.0))
        painter.setPen(QPen(QColor("#5f5f5f"), 1.0))
        painter.drawRect(self._plot_rect)
        self._draw_grid(painter)

        if self._frame is None or len(self._frame.time) < 2:
            self._draw_center_message(painter, self._message or self._labels["empty"])
            return

        x_values = self._normalized_x(self._frame.time)
        y1 = self._normalize(self._frame.transmission, top=0.10, bottom=0.48)
        y2 = self._normalize(self._frame.error, top=0.55, bottom=0.92)
        self._draw_trace(painter, x_values, y1, QColor("#e36f6f"), 1.8)
        self._draw_trace(painter, x_values, y2, QColor("#6aa8ff"), 1.5)
        self._draw_center_line(painter)
        self._draw_markers(painter)
        self._draw_legend(painter)
        self._draw_footer(painter)

    def _normalized_x(self, values: Sequence[float]) -> tuple[float, ...]:
        first = values[0]
        last = values[-1]
        width = last - first
        if abs(width) < 1e-15:
            return tuple(index / max(1, len(values) - 1) for index in range(len(values)))
        return tuple((value - first) / width for value in values)

    def _normalize(self, values: Sequence[float], top: float, bottom: float) -> tuple[float, ...]:
        if not values:
            return ()
        lo = min(values)
        hi = max(values)
        span = hi - lo
        if abs(span) < 1e-15:
            mid = (top + bottom) / 2.0
            return tuple(mid for _ in values)
        return tuple(bottom - ((value - lo) / span) * (bottom - top) for value in values)

    def _map(self, x_fraction: float, y_fraction: float) -> tuple[float, float]:
        rect = self._plot_rect
        return rect.left() + x_fraction * rect.width(), rect.top() + y_fraction * rect.height()

    def _draw_trace(
        self,
        painter: QPainter,
        x_values: Sequence[float],
        y_values: Sequence[float],
        color: QColor,
        width: float,
    ) -> None:
        limit = min(len(x_values), len(y_values))
        if limit < 2:
            return
        path = QPainterPath()
        x0, y0 = self._map(x_values[0], y_values[0])
        path.moveTo(x0, y0)
        for index in range(1, limit):
            x, y = self._map(x_values[index], y_values[index])
            path.lineTo(x, y)
        painter.setPen(QPen(color, width))
        painter.drawPath(path)

    def _draw_grid(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#4a4a4a"), 1.0, Qt.DashLine))
        rect = self._plot_rect
        for index in range(1, 4):
            x = rect.left() + rect.width() * index / 4.0
            y = rect.top() + rect.height() * index / 4.0
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

    def _draw_center_line(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#d0d0d0"), 1.0, Qt.DotLine))
        x = self._plot_rect.left() + self._plot_rect.width() * 0.5
        painter.drawLine(QPointF(x, self._plot_rect.top()), QPointF(x, self._plot_rect.bottom()))

    def _draw_markers(self, painter: QPainter) -> None:
        if self._peak_fraction is not None:
            self._draw_vertical_marker(painter, self._peak_fraction, QColor("#ffb14d"), self._labels["peak"])
        if self._zero_fraction is not None:
            self._draw_vertical_marker(painter, self._zero_fraction, QColor("#76d48c"), self._labels["zero"])

    def _draw_vertical_marker(self, painter: QPainter, fraction: float, color: QColor, label: str) -> None:
        fraction = max(0.0, min(1.0, fraction))
        rect = self._plot_rect
        x = rect.left() + fraction * rect.width()
        painter.setPen(QPen(color, 1.4, Qt.DashLine))
        painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
        painter.setPen(color)
        painter.drawText(QRectF(x + 4.0, rect.top() + 4.0, 120.0, 18.0), Qt.AlignLeft | Qt.AlignVCenter, label)

    def _draw_legend(self, painter: QPainter) -> None:
        x = self._plot_rect.left() + 10.0
        y = self._plot_rect.top() + 10.0
        for color, label in (
            (QColor("#e36f6f"), self._labels["transmission"]),
            (QColor("#6aa8ff"), self._labels["error"]),
        ):
            painter.setPen(QPen(color, 2.0))
            painter.drawLine(QPointF(x, y + 7.0), QPointF(x + 18.0, y + 7.0))
            painter.setPen(QColor("#f0f0f0"))
            painter.drawText(QRectF(x + 24.0, y - 1.0, 180.0, 18.0), Qt.AlignLeft | Qt.AlignVCenter, label)
            y += 20.0

    def _draw_footer(self, painter: QPainter) -> None:
        if self._frame is None:
            return
        duration = self._frame.time[-1] - self._frame.time[0] if len(self._frame.time) > 1 else 0.0
        text = f"{len(self._frame.time)} samples, {duration:.3f} s, {self._frame.sample_rate:.1f} Sa/s"
        if self._message:
            text = f"{text}  |  {self._message}"
        painter.setPen(QColor("#d0d0d0"))
        painter.drawText(
            QRectF(self._plot_rect.left(), self._plot_rect.bottom() + 10.0, self._plot_rect.width(), 22.0),
            Qt.AlignCenter | Qt.AlignVCenter,
            text,
        )

    def _draw_center_message(self, painter: QPainter, text: str) -> None:
        painter.setPen(QColor("#d0d0d0"))
        painter.drawText(self._plot_rect, Qt.AlignCenter | Qt.TextWordWrap, text)
