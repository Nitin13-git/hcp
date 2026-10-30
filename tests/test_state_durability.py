import json
import multiprocessing
import os
from pathlib import Path

import pytest

from hcp.reference import JsonFileStateStore


def _write_many(path: str, worker: str, count: int) -> None:
    store = JsonFileStateStore(path)
    for i in range(count):
        store.write(f"{worker}:{i}", i, by=worker)


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


def test_concurrent_writers_do_not_lose_records(tmp_path: Path) -> None:
    path = str(tmp_path / "state.json")
    JsonFileStateStore(path)
    ctx = multiprocessing.get_context("spawn")
    procs = [ctx.Process(target=_write_many, args=(path, name, 50)) for name in ("a", "b")]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=60)
        assert p.exitcode == 0

    data = json.loads(Path(path).read_text())
    assert len(data["records"]) == 100
