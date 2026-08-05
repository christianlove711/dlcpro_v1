from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QMessageBox, QWidget

from ui_text import TEXT


class NotificationService:
    def __init__(self, parent: QWidget, language_provider: Callable[[], str]) -> None:
        self.parent = parent
        self.language_provider = language_provider

    @property
    def text(self) -> dict[str, str]:
        return TEXT[self.language_provider()]

    def warning(self, message_key: str, *, title_key: str = "warning_title", **values) -> None:
        QMessageBox.warning(
            self.parent,
            self.text[title_key],
            self.text[message_key].format(**values),
        )

    def confirm_parameter_write(self, label: str, current: str, value: str) -> bool:
        t = self.text
        result = QMessageBox.question(
            self.parent,
            t["confirm_large_change_title"],
            t["confirm_large_change_body"].format(label=label, current=current, value=value),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        return result == QMessageBox.Yes
