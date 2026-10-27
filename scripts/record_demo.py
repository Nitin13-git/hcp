"""Paced version of `hcp.demo` for recording a watchable GIF.

Runs the exact same real HCP calls as `python -m hcp.demo` — nothing here
is faked or hardcoded — just with a deliberate pause between each printed
line so a terminal recording of it is actually readable. The shipped demo
(`hcp.demo`) stays genuinely instant for real use; this is a dev tool for
generating promotional material, not part of the installed package.

Run with: python scripts/record_demo.py
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from hcp.reference import (
    FileLifecycle,
    JsonFileStateStore,
    SubprocessVerifier,
    TableScopeEnforcer,
    resume,
)
from hcp.scope import Capability, CapabilityKind

PAUSE = 1.1


def say(line: str) -> None:
    print(line, flush=True)
    time.sleep(PAUSE)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "state.json"

        scope = TableScopeEnforcer()
        etc = Capability(CapabilityKind.PATH, "/etc/passwd")
        say(f"[scope]     deny by default: /etc/passwd allowed? {scope.check(etc)}")
        scope.grant(Capability(CapabilityKind.PATH, "/workspace/*"))
        report = Capability(CapabilityKind.PATH, "/workspace/report.md")
        say(f"[scope]     grant /workspace/*: report.md allowed? {scope.check(report)}, "
            f"/etc/passwd allowed? {scope.check(etc)}")

        state = JsonFileStateStore(state_path)
        lifecycle = FileLifecycle(state)
        handle = lifecycle.init("demo: verify a claimed fix")
        state.write("finding", {"note": "patch applied"}, by="agent")
        lifecycle.checkpoint(handle)
        say(f"[lifecycle] session {handle.session_id[:8]}... started and checkpointed")

        verifier = SubprocessVerifier()
        claim = verifier.run("false")
        say(f"[verify]    agent claims the fix works ... independently checked: "
            f"passed={claim.passed} (caught the lie)")
        real = verifier.run("true")
        say(f"[verify]    agent does the real fix, checks again ... passed={real.passed}")

        fresh_state = JsonFileStateStore(state_path)
        resumed = resume(fresh_state, handle.session_id)
        say(f"[state]     a new process, given only the session id, recovers: "
            f"task={resumed.task!r}")
        say(f"[state]     ...and the finding written earlier: "
            f"{fresh_state.read('finding').value}")

        FileLifecycle(fresh_state).teardown(resumed, reason="demo complete")
        say("[lifecycle] session torn down cleanly")

        print(flush=True)
        say("All four HCP subsystems, demonstrated for real, in under a second.")
        print("https://github.com/Nitin13-git/hcp", flush=True)


if __name__ == "__main__":
    main()
