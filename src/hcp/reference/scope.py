from __future__ import annotations

import fnmatch

from hcp.scope import Capability, ScopeEnforcer


class TableScopeEnforcer(ScopeEnforcer):
    """In-memory least-privilege scope: deny by default, allow only granted patterns."""

    def __init__(self) -> None:
        self._granted: set[Capability] = set()

    def grant(self, capability: Capability) -> None:
        self._granted.add(capability)

    def check(self, capability: Capability) -> bool:
        return any(
            granted.kind == capability.kind
            and fnmatch.fnmatch(capability.pattern, granted.pattern)
            for granted in self._granted
        )

    def active_scope(self) -> frozenset[Capability]:
        return frozenset(self._granted)
