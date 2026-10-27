from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class StateRecord:
    key: str
    value: object
    by: str
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StateStore(ABC):
    """Durable, out-of-context state for a harness session.

    The repository (or whatever this is backed by) is the source of truth.
    Nothing here may rely on the model's conversation history to recover
    state — a fresh session with no memory of prior turns must be able to
    call `read` and get the same answer a continuing session would.
    """

    @abstractmethod
    def read(self, key: str) -> StateRecord | None: ...

    @abstractmethod
    def write(self, key: str, value: object, *, by: str) -> StateRecord: ...

    @abstractmethod
    def history(self, key: str) -> list[StateRecord]: ...

    @abstractmethod
    def checkpoint(self, label: str) -> str:
        """Snapshot current state under `label`; return a checkpoint id.

        Calling this twice with the same label must not error and must not
        duplicate the checkpoint — the second call returns the existing id.
        """
