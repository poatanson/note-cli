from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def note_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Every test gets its own NOTE_DIR so the real ~/.notes is never touched."""
    folder = tmp_path / "notes"
    monkeypatch.setenv("NOTE_DIR", str(folder))
    return folder
