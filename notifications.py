from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QDialog, QStyle, QWidget

from ui_text import TEXT
from widgets.common_controls import CompactMessageDialog


class NotificationService:
    def __init__(self, parent: QWidget, language_provider: Callable[[], str]) -> None:
        self.parent = parent
        self.language_provider = language_provider

    @property
    def text(self) -> dict[str, str]:
        return TEXT[self.language_provider()]

    def warning(self, message_key: str, *, title_key: str = "warning_title", **values) -> None:
        CompactMessageDialog(
            self.parent,
            self.text[title_key],
            self.text[message_key].format(**values),
            accept_text=self.text["dialog_ok"],
            icon=QStyle.SP_MessageBoxWarning,
        ).exec()

    def confirm_parameter_write(self, label: str, current: str, value: str) -> bool:
        t = self.text
        result = CompactMessageDialog(
            self.parent,
            t["confirm_large_change_title"],
            t["confirm_large_change_body"].format(label=label, current=current, value=value),
            accept_text=t["dialog_confirm"],
            reject_text=t["dialog_cancel"],
            icon=QStyle.SP_MessageBoxQuestion,
        ).exec()
        return result == QDialog.Accepted
