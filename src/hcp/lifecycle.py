from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class SessionHandle:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    task: str = ""


class SessionLifecycle(ABC):
    """Init/checkpoint/teardown hooks that let sessions compose.

    A session started by one HCP-speaking tool must be resumable by a
    different tool that also speaks HCP, as long as both read the same
    checkpoint id back through a shared StateStore.
    """

    @abstractmethod
    def init(self, task: str) -> SessionHandle: ...

    @abstractmethod
    def checkpoint(self, handle: SessionHandle) -> str: ...

    @abstractmethod
    def teardown(self, handle: SessionHandle, *, reason: str) -> None: ...
