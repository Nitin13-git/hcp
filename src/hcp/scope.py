from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class CapabilityKind(str, Enum):
    PATH = "path"
    COMMAND = "command"
    NETWORK = "network"


@dataclass(frozen=True)
class Capability:
    kind: CapabilityKind
    pattern: str
    """A kind-specific pattern: a path glob, a command name, or a host."""


class ScopeEnforcer(ABC):
    """Least-privilege capability scoping for a single session.

    Scope is computed per task, not granted globally — a session should
    only ever hold the capabilities it was explicitly granted for its
    current task, and `check` must deny anything outside that set by
    default.
    """

    @abstractmethod
    def grant(self, capability: Capability) -> None: ...

    @abstractmethod
    def check(self, capability: Capability) -> bool: ...

    @abstractmethod
    def active_scope(self) -> frozenset[Capability]: ...
