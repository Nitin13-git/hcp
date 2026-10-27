from __future__ import annotations

import fnmatch

from hcp.scope import Capability, CapabilityKind, ScopeEnforcer


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

    @staticmethod
    def from_capability_dicts(items: list[dict]) -> TableScopeEnforcer:
        """Reconstruct a scope from `[{"kind": ..., "pattern": ...}, ...]`.

        `Capability` is already a flat (kind, pattern) record, so it
        round-trips through a `StateStore` as plain JSON with no custom
        wire format — this just does the dict -> Capability decode step
        (turning the plain string "kind" back into a CapabilityKind), the
        one part that isn't automatic. See `hcp/interop/` for this used to
        reconstruct a scope granted by a different language.
        """
        scope = TableScopeEnforcer()
        for item in items:
            scope.grant(Capability(kind=CapabilityKind(item["kind"]), pattern=item["pattern"]))
        return scope
