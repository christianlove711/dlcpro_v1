from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from dlcpro_service import AutoLockScopeSnapshot, LockPointSnapshot


class ScopePlotWidget(QWidget):
    candidateClicked = Signal(float, float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(320)
        self._scope: AutoLockScopeSnapshot | None = None
        self._candidates: tuple[LockPointSnapshot, ...] = ()
        self._selected: LockPointSnapshot | None = None
        self._tracking: LockPointSnapshot | None = None
        self._target: LockPointSnapshot | None = None
        self._empty_text = ""
        self._error_text: str | None = None
        self._text_map: dict[str, str] = {}
        self._candidate_hit_points: list[tuple[LockPointSnapshot, QPointF]] = []
        self._plot_rect = QRectF()

    def set_plot_data(
        self,
        scope: AutoLockScopeSnapshot | None,
        candidates: Sequence[LockPointSnapshot],
        selected: LockPointSnapshot | None,
        tracking: LockPointSnapshot | None,
        target: LockPointSnapshot | None,
        text_map: dict[str, str],
        *,
        empty_text: str,
        error_text: str | None = None,
    ) -> None:
        self._scope = scope
        self._candidates = tuple(candidates)
        self._selected = selected
        self._tracking = tracking
        self._target = target
        self._text_map = text_map
        self._empty_text = empty_text
        self._error_text = error_text
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.fillRect(self.rect(), QColor("#3a3a3a"))
        self._plot_rect = QRectF(62.0, 24.0, max(120.0, self.width() - 86.0), max(120.0, self.height() - 74.0))
        painter.setPen(QPen(QColor("#5a5a5a"), 1.0))
        painter.drawRect(self._plot_rect)

        if self._scope is None or not self._scope.x_values or not (self._scope.y_values or self._scope.y2_values):
            self._candidate_hit_points = []
            self._draw_center_message(painter, self._error_text or self._empty_text)
            return

        bounds = self._data_bounds()
        if bounds is None:
            self._candidate_hit_points = []
            self._draw_center_message(painter, self._error_text or self._empty_text)
            return
        min_x, max_x, min_y, max_y = bounds

        self._draw_grid(painter)
        self._draw_trace(
            painter,
            self._scope.background_x,
            self._scope.background_y,
            QColor("#8b8b8b"),
            1.0,
        )
        self._draw_trace(
            painter,
            self._scope.x_values,
            self._scope.y_values,
            QColor("#e36f6f"),
            1.6,
        )
        self._draw_trace(
            painter,
            self._scope.x_values,
            self._scope.y2_values,
            QColor("#6aa8ff"),
            1.4,
        )
        self._draw_axes_labels(painter, min_x, max_x, min_y, max_y)
        self._draw_legend(painter)
        self._draw_points(painter, min_x, max_x, min_y, max_y)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        click = QPointF(event.position())
        for point, mapped in self._candidate_hit_points:
            if (mapped - click).manhattanLength() <= 12.0:
                self.candidateClicked.emit(point.x, point.y)
                event.accept()
                return
        super().mousePressEvent(event)

    def _data_bounds(self) -> tuple[float, float, float, float] | None:
        if self._scope is None:
            return None
        xs = list(self._scope.x_values) + list(self._scope.background_x)
        ys = list(self._scope.y_values) + list(self._scope.y2_values) + list(self._scope.background_y)
        for point in (*self._candidates, self._selected, self._tracking, self._target):
            if point is None:
                continue
            xs.append(point.x)
            ys.append(point.y)
        if not xs or not ys:
            return None
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)
        if abs(max_x - min_x) < 1e-12:
            min_x -= 1.0
            max_x += 1.0
        if abs(max_y - min_y) < 1e-12:
            padding = 1.0 if abs(max_y) < 1e-12 else abs(max_y) * 0.1
            min_y -= padding
            max_y += padding
        x_pad = (max_x - min_x) * 0.03
        y_pad = (max_y - min_y) * 0.08
        return min_x - x_pad, max_x + x_pad, min_y - y_pad, max_y + y_pad

    def _map_point(self, x: float, y: float, min_x: float, max_x: float, min_y: float, max_y: float) -> QPointF:
        rect = self._plot_rect
        px = rect.left() + ((x - min_x) / (max_x - min_x)) * rect.width()
        py = rect.bottom() - ((y - min_y) / (max_y - min_y)) * rect.height()
        return QPointF(px, py)

    def _draw_trace(
        self,
        painter: QPainter,
        x_values: Sequence[float],
        y_values: Sequence[float],
        color: QColor,
        width: float,
    ) -> None:
        if self._scope is None or not x_values or not y_values:
            return
        bounds = self._data_bounds()
        if bounds is None:
            return
        min_x, max_x, min_y, max_y = bounds
        limit = min(len(x_values), len(y_values))
        if limit < 2:
            return
        path = QPainterPath()
        first = self._map_point(x_values[0], y_values[0], min_x, max_x, min_y, max_y)
        path.moveTo(first)
        for index in range(1, limit):
            mapped = self._map_point(x_values[index], y_values[index], min_x, max_x, min_y, max_y)
            path.lineTo(mapped)
        painter.setPen(QPen(color, width))
        painter.drawPath(path)

    def _draw_points(self, painter: QPainter, min_x: float, max_x: float, min_y: float, max_y: float) -> None:
        self._candidate_hit_points = []
        painter.setBrush(QColor("#b7b7b7"))
        painter.setPen(QPen(QColor("#d0d0d0"), 1.0))
        for point in self._candidates:
            mapped = self._map_point(point.x, point.y, min_x, max_x, min_y, max_y)
            self._candidate_hit_points.append((point, mapped))
            painter.drawEllipse(mapped, 4.5, 4.5)

        self._draw_hollow_marker(painter, self._selected, QColor("#ff6565"), 7.0, min_x, max_x, min_y, max_y)
        self._draw_hollow_marker(painter, self._tracking, QColor("#ffb14d"), 8.5, min_x, max_x, min_y, max_y)
        self._draw_cross_marker(painter, self._target, QColor("#76d48c"), 9.0, min_x, max_x, min_y, max_y)

    def _draw_hollow_marker(
        self,
        painter: QPainter,
        point: LockPointSnapshot | None,
        color: QColor,
        radius: float,
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
    ) -> None:
        if point is None:
            return
        mapped = self._map_point(point.x, point.y, min_x, max_x, min_y, max_y)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(color, 2.0))
        painter.drawEllipse(mapped, radius, radius)

    def _draw_cross_marker(
        self,
        painter: QPainter,
        point: LockPointSnapshot | None,
        color: QColor,
        radius: float,
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
    ) -> None:
        if point is None:
            return
        mapped = self._map_point(point.x, point.y, min_x, max_x, min_y, max_y)
        painter.setPen(QPen(color, 2.0))
        painter.drawLine(mapped.x() - radius, mapped.y(), mapped.x() + radius, mapped.y())
        painter.drawLine(mapped.x(), mapped.y() - radius, mapped.x(), mapped.y() + radius)

    def _draw_axes_labels(
        self,
        painter: QPainter,
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
    ) -> None:
        if self._scope is None:
            return
        painter.setPen(QColor("#dcdcdc"))
        rect = self._plot_rect
        painter.drawText(
            QRectF(rect.left(), rect.bottom() + 8.0, rect.width(), 20.0),
            Qt.AlignCenter,
            f"{self._scope.x_name} [{self._scope.x_unit}]",
        )
        painter.drawText(
            QRectF(6.0, rect.top() - 2.0, rect.left() - 12.0, 18.0),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"{max_y:.4g}",
        )
        painter.drawText(
            QRectF(6.0, rect.bottom() - 16.0, rect.left() - 12.0, 18.0),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"{min_y:.4g}",
        )
        painter.drawText(
            QRectF(rect.left() - 4.0, rect.bottom() + 26.0, 80.0, 18.0),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"{min_x:.4g}",
        )
        painter.drawText(
            QRectF(rect.right() - 78.0, rect.bottom() + 26.0, 80.0, 18.0),
            Qt.AlignRight | Qt.AlignVCenter,
            f"{max_x:.4g}",
        )

    def _draw_grid(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#4a4a4a"), 1.0, Qt.DashLine))
        rect = self._plot_rect
        for index in range(1, 4):
            x = rect.left() + rect.width() * index / 4.0
            y = rect.top() + rect.height() * index / 4.0
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

    def _draw_legend(self, painter: QPainter) -> None:
        if self._scope is None:
            return
        items = [
            (QColor("#e36f6f"), f"{self._scope.y_name} [{self._scope.y_unit}]"),
        ]
        if self._scope.y2_values:
            items.append((QColor("#6aa8ff"), f"{self._scope.y2_name} [{self._scope.y2_unit}]"))
        if self._scope.background_x and self._scope.background_y:
            items.append((QColor("#8b8b8b"), self._text_map["auto_lock_scope_background_marker"]))
        items.extend(
            [
                (QColor("#b7b7b7"), self._text_map["auto_lock_scope_candidates_marker"]),
                (QColor("#ff6565"), self._text_map["auto_lock_scope_selected_marker"]),
                (QColor("#ffb14d"), self._text_map["auto_lock_scope_tracking_marker"]),
                (QColor("#76d48c"), self._text_map["auto_lock_scope_target_marker"]),
            ]
        )
        painter.setPen(QColor("#efefef"))
        x = self._plot_rect.left() + 10.0
        y = self._plot_rect.top() + 10.0
        for color, label in items:
            painter.setPen(QPen(color, 2.0))
            painter.drawLine(QPointF(x, y + 6.0), QPointF(x + 16.0, y + 6.0))
            painter.setPen(QColor("#efefef"))
            painter.drawText(QRectF(x + 22.0, y - 2.0, 280.0, 16.0), Qt.AlignLeft | Qt.AlignVCenter, label)
            y += 18.0

    def _draw_center_message(self, painter: QPainter, text: str) -> None:
        painter.setPen(QColor("#d0d0d0"))
        painter.drawText(self._plot_rect, Qt.AlignCenter | Qt.TextWordWrap, text)
