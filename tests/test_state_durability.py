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


def test_saved_state_file_respects_umask(tmp_path: Path) -> None:
    old = os.umask(0o022)
    try:
        path = tmp_path / "state.json"
        JsonFileStateStore(path).write("k", 1, by="test")
        assert (path.stat().st_mode & 0o777) == 0o644
    finally:
        os.umask(old)


def test_save_retries_transient_permission_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    store = JsonFileStateStore(path)
    real_replace = os.replace
    failures = {"left": 2}

    def flaky(src: str, dst: str) -> None:
        if failures["left"] > 0:
            failures["left"] -= 1
            raise PermissionError("file held open by a reader")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky)
    store.write("k", 1, by="test")
    assert failures["left"] == 0
    assert json.loads(path.read_text())["records"][0]["key"] == "k"
