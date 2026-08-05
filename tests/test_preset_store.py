from __future__ import annotations

import json

from preset_store import AUTO_LOCK_PRESET_FILENAME, LEGACY_AUTO_LOCK_PRESET_FILENAMES, PresetStore


def test_legacy_preset_migrates_once_and_saves_atomically(tmp_path) -> None:
    config_dir = tmp_path / "config"
    bundled_dir = tmp_path / "bundle"
    bundled_dir.mkdir()
    legacy = bundled_dir / LEGACY_AUTO_LOCK_PRESET_FILENAMES[0]
    legacy.write_text(json.dumps({"legacy": {"strategy": "hybrid"}}), encoding="utf-8")

    store = PresetStore(
        AUTO_LOCK_PRESET_FILENAME,
        legacy_filenames=LEGACY_AUTO_LOCK_PRESET_FILENAMES,
        config_dir=config_dir,
        bundled_dir=bundled_dir,
    )
    assert store.load()["legacy"]["strategy"] == "hybrid"
    assert store.user_path.exists()

    store.save({"saved": {"strategy": "error_primary"}})
    assert store.load() == {"saved": {"strategy": "error_primary"}}
    assert not store.user_path.with_suffix(".json.tmp").exists()
