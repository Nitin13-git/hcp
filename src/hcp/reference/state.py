from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from hcp.state import StateRecord, StateStore


class StateFileError(Exception):
    """The backing state file exists but cannot be parsed."""


class JsonFileStateStore(StateStore):
    """Minimal StateStore backed by a single JSON file.

    Not meant for production use — it exists so the HCP interfaces have a
    working implementation to test against and to copy from. Swap this
    out for a database- or git-backed store without touching callers.
    """

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        if not self._path.exists():
            self._path.write_text(json.dumps({"records": [], "checkpoints": {}}))

    def _load(self) -> dict:
        try:
            return json.loads(self._path.read_text())
        except json.JSONDecodeError as exc:
            raise StateFileError(f"state file {self._path} is not valid JSON: {exc.msg}") from exc

    def _save(self, data: dict) -> None:
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix=f".{self._path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as handle:
                handle.write(json.dumps(data, default=str, indent=2))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, self._path)
        except BaseException:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise

    def read(self, key: str) -> StateRecord | None:
        records = [r for r in self._load()["records"] if r["key"] == key]
        if not records:
            return None
        latest = records[-1]
        return StateRecord(
            key=latest["key"],
            value=latest["value"],
            by=latest["by"],
            at=datetime.fromisoformat(latest["at"]),
        )

    def write(self, key: str, value: object, *, by: str) -> StateRecord:
        record = StateRecord(key=key, value=value, by=by, at=datetime.now(timezone.utc))
        data = self._load()
        data["records"].append(asdict(record))
        self._save(data)
        return record

    def history(self, key: str) -> list[StateRecord]:
        return [
            StateRecord(
                key=r["key"],
                value=r["value"],
                by=r["by"],
                at=datetime.fromisoformat(r["at"]),
            )
            for r in self._load()["records"]
            if r["key"] == key
        ]

    def checkpoint(self, label: str) -> str:
        data = self._load()
        existing = data["checkpoints"].get(label)
        if existing is not None:
            return existing
        checkpoint_id = f"{label}-{len(data['checkpoints'])}"
        data["checkpoints"][label] = checkpoint_id
        self._save(data)
        return checkpoint_id
