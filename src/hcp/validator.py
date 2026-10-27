from __future__ import annotations

from dataclasses import dataclass

from hcp.lifecycle import SessionLifecycle
from hcp.scope import ScopeEnforcer
from hcp.state import StateStore
from hcp.verification import Verifier

_INTERFACES = {
    "state": StateStore,
    "verification": Verifier,
    "scope": ScopeEnforcer,
    "lifecycle": SessionLifecycle,
}


@dataclass(frozen=True)
class ConformanceReport:
    conformant: bool
    implemented: frozenset[str]
    missing: frozenset[str]
    errors: tuple[str, ...]


def validate(harness: object) -> ConformanceReport:
    """Check whether `harness` implements the four HCP interfaces.

    `harness` may be a single object implementing all four ABCs, or a
    mapping of interface name -> implementing object (the common case,
    since one object rarely owns state, verification, scope, and
    lifecycle all at once).
    """
    errors: list[str] = []
    implemented: set[str] = set()

    candidates = harness if isinstance(harness, dict) else {
        name: harness for name in _INTERFACES
    }

    for name, iface in _INTERFACES.items():
        obj = candidates.get(name)
        if obj is None:
            errors.append(f"{name}: no implementation provided")
            continue
        if not isinstance(obj, iface):
            errors.append(
                f"{name}: {type(obj).__name__} does not subclass "
                f"{iface.__name__}"
            )
            continue
        implemented.add(name)

    missing = frozenset(_INTERFACES) - implemented
    return ConformanceReport(
        conformant=not missing and not errors,
        implemented=frozenset(implemented),
        missing=missing,
        errors=tuple(errors),
    )
