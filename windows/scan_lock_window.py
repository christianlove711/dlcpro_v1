from __future__ import annotations

from windows.base_window import PlaceholderWindow


class ScanLockWindow(PlaceholderWindow):
    def __init__(self) -> None:
        super().__init__("Scan&Lock")
