from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QStyleOptionSpinBox,
    QVBoxLayout,
    QWidget,
)


class VisibleCheckBox(QCheckBox):
    """Theme-independent checkbox with a high-contrast blue checked state."""

    INDICATOR_SIZE = 18

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        size = self.INDICATOR_SIZE
        x = 1
        y = max(0, (self.height() - size) // 2)
        checked = self.isChecked()
        enabled = self.isEnabled()
        if checked:
            fill = QColor("#286bc1" if enabled else "#94a3b8")
            border = fill
        else:
            fill = QColor("#ffffff" if enabled else "#f0f2f5")
            border = QColor("#8794a8" if enabled else "#c7cfda")
        painter.setPen(QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawRoundedRect(x, y, size, size, 4, 4)
        if checked:
            path = QPainterPath()
            path.moveTo(x + 4.0, y + 9.5)
            path.lineTo(x + 7.5, y + 13.0)
            path.lineTo(x + 14.5, y + 5.5)
            painter.setPen(QPen(
                QColor("#ffffff"), 2.2,
                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin,
            ))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        text_color = self.palette().color(
            self.foregroundRole() if enabled else self.backgroundRole()
        )
        if not enabled:
            text_color = QColor("#8993a4")
        painter.setPen(text_color)
        painter.drawText(
            self.rect().adjusted(size + 9, 0, 0, 0),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.text(),
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
    button.setObjectName("ToggleButton")
    button.setCheckable(True)
    # Toggle controls represent a state, not a full-width action.  A fixed
    # footprint keeps header and QFormLayout variants visually identical.
    button.setFixedSize(104, 36)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    button.clicked.connect(slot)
    return button


class CompactMessageDialog(QDialog):
    """Small, predictable alternative to platform-dependent QMessageBox sizing."""

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        message: str,
        *,
        accept_text: str,
        reject_text: str | None = None,
        icon: QStyle.StandardPixmap = QStyle.SP_MessageBoxInformation,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CompactMessageDialog")
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(16)

        body = QHBoxLayout()
        body.setSpacing(16)
        icon_label = QLabel(self)
        icon_label.setObjectName("CompactMessageIcon")
        icon_label.setPixmap(self.style().standardIcon(icon).pixmap(32, 32))
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        body.addWidget(icon_label, 0, Qt.AlignTop)

        self.message_label = QLabel(message, self)
        # Keep the historical object name so UI diagnostics can locate it.
        self.message_label.setObjectName("qt_msgbox_label")
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.message_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        body.addWidget(self.message_label, 1)
        layout.addLayout(body)

        self.button_box = QDialogButtonBox(self)
        self.accept_button = self.button_box.addButton(
            accept_text, QDialogButtonBox.AcceptRole
        )
        self.accept_button.setObjectName("PrimaryDialogButton")
        self.accept_button.clicked.connect(self.accept)
        self.reject_button: QPushButton | None = None
        if reject_text is not None:
            self.reject_button = self.button_box.addButton(
                reject_text, QDialogButtonBox.RejectRole
            )
            self.reject_button.clicked.connect(self.reject)
        layout.addWidget(self.button_box)

        # Long notices remain readable without ever growing into a screen-wide bar.
        width = 560 if len(message) > 45 else 460
        self.message_label.setMinimumWidth(width - 110)
        self.message_label.setMaximumWidth(width - 110)
        self.setFixedWidth(width)
