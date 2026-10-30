import json
import os
from pathlib import Path

import pytest

from hcp.reference import JsonFileStateStore


def test_failed_save_leaves_previous_state_intact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    store = JsonFileStateStore(path)
    store.write("progress", {"done": 1}, by="test")
    before = path.read_text()

    def crash(src: str, dst: str) -> None:
        raise OSError("simulated crash before rename")

    monkeypatch.setattr(os, "replace", crash)
    with pytest.raises(OSError):
        store.write("progress", {"done": 2}, by="test")

    assert path.read_text() == before
    assert json.loads(path.read_text())["records"][0]["value"] == {"done": 1}
    leftovers = [p.name for p in tmp_path.iterdir() if p.name not in {"state.json", "state.json.lock"}]
    assert leftovers == []
