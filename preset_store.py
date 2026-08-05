from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


AUTO_LOCK_PRESET_FILENAME = "auto_lock_algorithm_presets.json"
LEGACY_AUTO_LOCK_PRESET_FILENAMES = ("auto_lock" + "2_algorithm_presets.json",)


class PresetStore:
    def __init__(
        self,
        filename: str,
        *,
        legacy_filenames: tuple[str, ...] = (),
        config_dir: Path | None = None,
        bundled_dir: Path | None = None,
    ) -> None:
        self.filename = filename
        self.legacy_filenames = legacy_filenames
        self.config_dir = config_dir or self._default_config_dir()
        self.bundled_dir = bundled_dir or self._default_bundled_dir()

    @property
    def user_path(self) -> Path:
        return self.config_dir / self.filename

    @property
    def bundled_path(self) -> Path:
        return self.bundled_dir / self.filename

    def load(self) -> dict[str, dict[str, Any]]:
        self._migrate_legacy_once()
        source = self.user_path if self.user_path.exists() else self.bundled_path
        if not source.exists():
            return {}
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return {
            str(name): dict(values)
            for name, values in payload.items()
            if isinstance(name, str) and isinstance(values, dict)
        }

    def save(self, payload: dict[str, dict[str, Any]]) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.user_path.with_suffix(self.user_path.suffix + ".tmp")
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        try:
            temporary.write_text(text, encoding="utf-8", newline="\n")
            os.replace(temporary, self.user_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _migrate_legacy_once(self) -> None:
        if self.user_path.exists():
            return
        candidates = [self.config_dir / name for name in self.legacy_filenames]
        candidates.extend(self.bundled_dir / name for name in self.legacy_filenames)
        for candidate in candidates:
            if not candidate.exists():
                continue
            self.config_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate, self.user_path)
            return

    @staticmethod
    def _default_config_dir() -> Path:
        if sys.platform == "win32":
            root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            return root / "DLCProControl"
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return root / "DLCProControl"

    @staticmethod
    def _default_bundled_dir() -> Path:
        frozen_root = getattr(sys, "_MEIPASS", None)
        if frozen_root:
            return Path(frozen_root)
        return Path(__file__).resolve().parent
