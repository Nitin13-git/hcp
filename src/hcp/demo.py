"""HCP demo: all four subsystems doing their job, for real, in under a second.

Run with: python -m hcp.demo
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from hcp.reference import (
    FileLifecycle,
    JsonFileStateStore,
    SubprocessVerifier,
    TableScopeEnforcer,
    resume,
)
from hcp.scope import Capability, CapabilityKind


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "state.json"

        # SCOPE — deny by default, grant narrowly.
        scope = TableScopeEnforcer()
        etc = Capability(CapabilityKind.PATH, "/etc/passwd")
        print(f"[scope]     deny by default: /etc/passwd allowed? {scope.check(etc)}")
        scope.grant(Capability(CapabilityKind.PATH, "/workspace/*"))
        report = Capability(CapabilityKind.PATH, "/workspace/report.md")
        print(f"[scope]     grant /workspace/*: report.md allowed? {scope.check(report)}, "
              f"/etc/passwd allowed? {scope.check(etc)}")

        # LIFECYCLE + STATE — a session starts and records a finding.
        state = JsonFileStateStore(state_path)
        lifecycle = FileLifecycle(state)
        handle = lifecycle.init("demo: verify a claimed fix")
        state.write("finding", {"note": "patch applied"}, by="agent")
        lifecycle.checkpoint(handle)
        print(f"[lifecycle] session {handle.session_id[:8]}... started and checkpointed")

        # VERIFICATION — don't trust the claim, check independently.
        verifier = SubprocessVerifier()
        claim = verifier.run("false")  # the agent's first claim doesn't hold up
        print(f"[verify]    agent claims the fix works ... independently checked: "
              f"passed={claim.passed} (caught the lie)")
        real = verifier.run("true")  # the agent does the real work
        print(f"[verify]    agent does the real fix, checks again ... passed={real.passed}")

        # STATE — a BRAND-NEW process, given only the session id, recovers everything.
        fresh_state = JsonFileStateStore(state_path)  # simulates a different process
        resumed = resume(fresh_state, handle.session_id)
        print(f"[state]     a new process, given only the session id, recovers: "
              f"task={resumed.task!r}")
        print(f"[state]     ...and the finding written earlier: "
              f"{fresh_state.read('finding').value}")

        FileLifecycle(fresh_state).teardown(resumed, reason="demo complete")
        print("[lifecycle] session torn down cleanly")

        print("\nAll four HCP subsystems, demonstrated for real, in under a second.")
        print("https://github.com/Nitin13-git/hcp")


if __name__ == "__main__":
    main()
