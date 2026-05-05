from __future__ import annotations

from windows.base_window import PlaceholderWindow


class RelockWindow(PlaceholderWindow):
    def __init__(self) -> None:
        super().__init__("Relock")
