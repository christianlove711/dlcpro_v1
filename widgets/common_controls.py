from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QStyle,
    QStyleOptionSpinBox,
    QWidget,
)


class SafeComboBox(QComboBox):
    """Block mouse-wheel selection changes to avoid accidental device writes."""

    def wheelEvent(self, event) -> None:  # noqa: N802
        event.ignore()


class SafeDoubleSpinBox(QDoubleSpinBox):
    """Block mouse-wheel value changes; edits must come from arrows or typing."""

    stepApplied = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._button_only_mode = False
        self._step_feedback_direction = 0

    def wheelEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def stepBy(self, steps: int) -> None:  # noqa: N802
        previous = self.value()
        super().stepBy(steps)
        if self.value() != previous:
            self._mark_pending_device_value()
            self._flash_step_feedback(1 if steps > 0 else -1)
            self._clear_editor_selection()
            self.stepApplied.emit()

    def connect_live_apply(self, slot) -> None:
        def wrapped_slot() -> None:
            self._mark_pending_device_value()
            slot()

        self.editingFinished.connect(wrapped_slot)
        self.stepApplied.connect(wrapped_slot)

    def set_button_only_mode(self, enabled: bool = True) -> None:
        self._button_only_mode = enabled
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setReadOnly(enabled)
        if enabled:
            self._clear_editor_selection()

    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        if self._button_only_mode:
            self._clear_editor_selection()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if self._button_only_mode and event.key() not in {
            Qt.Key_Up,
            Qt.Key_Down,
            Qt.Key_PageUp,
            Qt.Key_PageDown,
            Qt.Key_Tab,
            Qt.Key_Backtab,
            Qt.Key_Left,
            Qt.Key_Right,
            Qt.Key_Home,
            Qt.Key_End,
            Qt.Key_Return,
            Qt.Key_Enter,
            Qt.Key_Escape,
        }:
            event.ignore()
            self._clear_editor_selection()
            return
        super().keyPressEvent(event)

    def _clear_editor_selection(self) -> None:
        line_edit = self.lineEdit()
        if line_edit is not None:
            QTimer.singleShot(0, line_edit.deselect)

    def _mark_pending_device_value(self) -> None:
        self.setProperty("deviceWritePending", True)
        self.setProperty("pendingDeviceValue", float(self.value()))

    def _flash_step_feedback(self, direction: int) -> None:
        self._step_feedback_direction = direction
        self.update()
        QTimer.singleShot(80, self._clear_step_feedback)

    def _clear_step_feedback(self) -> None:
        self._step_feedback_direction = 0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._step_feedback_direction == 0:
            return
        option = QStyleOptionSpinBox()
        self.initStyleOption(option)
        button = (
            QStyle.SubControl.SC_SpinBoxUp
            if self._step_feedback_direction > 0
            else QStyle.SubControl.SC_SpinBoxDown
        )
        rect = self.style().subControlRect(QStyle.ComplexControl.CC_SpinBox, option, button, self)
        if rect.isEmpty():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(rect.adjusted(1, 1, -1, -1), QColor(32, 32, 32, 90))

    def sync_from_device(self, value: float) -> None:
        pending = self.property("deviceWritePending")
        pending_value = self.property("pendingDeviceValue")
        if pending and pending_value is not None and abs(float(pending_value) - value) < 1e-9:
            self.setProperty("deviceWritePending", False)
            self.setProperty("pendingDeviceValue", None)
        if self.hasFocus():
            return
        if pending:
            return
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)


class SafeSpinBox(QSpinBox):
    """Block mouse-wheel value changes; edits must come from arrows or typing."""

    stepApplied = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._button_only_mode = False
        self._step_feedback_direction = 0

    def wheelEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def stepBy(self, steps: int) -> None:  # noqa: N802
        previous = self.value()
        super().stepBy(steps)
        if self.value() != previous:
            self._mark_pending_device_value()
            self._flash_step_feedback(1 if steps > 0 else -1)
            self._clear_editor_selection()
            self.stepApplied.emit()

    def connect_live_apply(self, slot) -> None:
        def wrapped_slot() -> None:
            self._mark_pending_device_value()
            slot()

        self.editingFinished.connect(wrapped_slot)
        self.stepApplied.connect(wrapped_slot)

    def set_button_only_mode(self, enabled: bool = True) -> None:
        self._button_only_mode = enabled
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setReadOnly(enabled)
        if enabled:
            self._clear_editor_selection()

    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        if self._button_only_mode:
            self._clear_editor_selection()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if self._button_only_mode and event.key() not in {
            Qt.Key_Up,
            Qt.Key_Down,
            Qt.Key_PageUp,
            Qt.Key_PageDown,
            Qt.Key_Tab,
            Qt.Key_Backtab,
            Qt.Key_Left,
            Qt.Key_Right,
            Qt.Key_Home,
            Qt.Key_End,
            Qt.Key_Return,
            Qt.Key_Enter,
            Qt.Key_Escape,
        }:
            event.ignore()
            self._clear_editor_selection()
            return
        super().keyPressEvent(event)

    def _clear_editor_selection(self) -> None:
        line_edit = self.lineEdit()
        if line_edit is not None:
            QTimer.singleShot(0, line_edit.deselect)

    def _mark_pending_device_value(self) -> None:
        self.setProperty("deviceWritePending", True)
        self.setProperty("pendingDeviceValue", int(self.value()))

    def _flash_step_feedback(self, direction: int) -> None:
        self._step_feedback_direction = direction
        self.update()
        QTimer.singleShot(80, self._clear_step_feedback)

    def _clear_step_feedback(self) -> None:
        self._step_feedback_direction = 0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._step_feedback_direction == 0:
            return
        option = QStyleOptionSpinBox()
        self.initStyleOption(option)
        button = (
            QStyle.SubControl.SC_SpinBoxUp
            if self._step_feedback_direction > 0
            else QStyle.SubControl.SC_SpinBoxDown
        )
        rect = self.style().subControlRect(QStyle.ComplexControl.CC_SpinBox, option, button, self)
        if rect.isEmpty():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(rect.adjusted(1, 1, -1, -1), QColor(32, 32, 32, 90))

    def sync_from_device(self, value: int) -> None:
        pending = self.property("deviceWritePending")
        pending_value = self.property("pendingDeviceValue")
        if pending and pending_value is not None and int(pending_value) == int(value):
            self.setProperty("deviceWritePending", False)
            self.setProperty("pendingDeviceValue", None)
        if self.hasFocus():
            return
        if pending:
            return
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)


class PrecisionButtonRow(QWidget):
    def __init__(
        self,
        options: Sequence[tuple[str, float]],
        setter: Callable[[float], None],
        parent: QWidget | None = None,
        max_columns: int | None = None,
    ) -> None:
        super().__init__(parent)
        if max_columns and max_columns > 0:
            layout = QGridLayout(self)
        else:
            layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.buttons: list[QPushButton] = []
        for index, (text_key, step) in enumerate(options):
            button = QPushButton(self)
            button.setObjectName("PrecisionButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, s=step: setter(s))
            button._text_key = text_key
            button._precision_step = step
            self.buttons.append(button)
            if max_columns and max_columns > 0:
                row, column = divmod(index, max_columns)
                layout.addWidget(button, row, column)
            else:
                layout.addWidget(button)
        if max_columns and max_columns > 0:
            for column in range(max_columns):
                layout.setColumnStretch(column, 1)
        else:
            layout.addStretch(1)


class StepTargetSpinBoxRow(QWidget):
    def __init__(
        self,
        module: str,
        spinbox: QDoubleSpinBox,
        on_select: Callable[[str, QDoubleSpinBox], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(spinbox, 1)

        self.target_button = QPushButton(self)
        self.target_button.setObjectName("StepTargetButton")
        self.target_button.setCheckable(True)
        self.target_button.clicked.connect(lambda checked=False, m=module, s=spinbox: on_select(m, s))
        self.target_button._precision_module = module
        self.target_button._precision_target = spinbox
        layout.addWidget(self.target_button, 0)


def create_toggle_button(slot, parent: QWidget | None = None) -> QPushButton:
    button = QPushButton(parent)
    button.setCheckable(True)
    button.setMinimumWidth(124)
    button.clicked.connect(slot)
    return button
