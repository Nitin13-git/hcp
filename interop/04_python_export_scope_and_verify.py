"""Step 4 of the interop proof: Python grants a scope and runs real
verifications, then exports both to the shared state file as plain data.

This is a different kind of interop than steps 1-3: Scope and Verifier
don't have their own persistence (a Scope's grants live in memory; a
Verifier's result is a one-off report), so there's nothing to "resume."
What's being proven here is narrower and more concrete: that the *wire
format* HCP's own JSON-serializable types produce in one language decodes
correctly, with the right types and the right meaning, in the other.
"""

from __future__ import annotations

import sys
from dataclasses import asdict

from hcp.reference import JsonFileStateStore, SubprocessVerifier, TableScopeEnforcer
from hcp.scope import Capability, CapabilityKind


def main() -> None:
    state_path = sys.argv[1]
    state = JsonFileStateStore(state_path)

    # --- Scope: grant two capabilities, export the granted list. ---
    scope = TableScopeEnforcer()
    scope.grant(Capability(kind=CapabilityKind.PATH, pattern="/workspace/*"))
    scope.grant(Capability(kind=CapabilityKind.COMMAND, pattern="pytest"))

    exported = [{"kind": c.kind.value, "pattern": c.pattern} for c in scope.active_scope()]
    state.write("scope:shared", exported, by="python-session")

    # --- Verifier: run two real checks, export both reports. ---
    verifier = SubprocessVerifier()
    pass_report = verifier.run("true")
    fail_report = verifier.run("false")
    state.write("verify:pass_report", asdict(pass_report), by="python-session")
    state.write("verify:fail_report", asdict(fail_report), by="python-session")

    print(f"python exported scope ({len(exported)} capabilities) and 2 verification reports")


if __name__ == "__main__":
    main()
