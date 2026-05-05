from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QPushButton, QWidget


class PrecisionButtonRow(QWidget):
    def __init__(
        self,
        options: Sequence[tuple[str, float]],
        setter: Callable[[float], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.buttons: list[QPushButton] = []
        for text_key, step in options:
            button = QPushButton(self)
            button.setObjectName("PrecisionButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, s=step: setter(s))
            button._text_key = text_key
            button._precision_step = step
            self.buttons.append(button)
            layout.addWidget(button)
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
