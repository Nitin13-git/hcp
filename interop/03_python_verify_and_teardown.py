"""Step 3 of the interop proof: Python resumes the session a second time.

Verifies both its own write and Node's write are readable, verifies the
full checkpoint history reflects both languages' activity, then tears the
session down. If any assertion fails, this exits non-zero — the shell
orchestrator treats that as proof the handoff did NOT actually work.
"""

from __future__ import annotations

import sys

from hcp.reference import FileLifecycle, JsonFileStateStore, resume

TASK = "cross-language interop proof: recon then verify"


def main() -> None:
    state_path = sys.argv[1]
    session_id = sys.argv[2]

    state = JsonFileStateStore(state_path)
    lifecycle = FileLifecycle(state)

    handle = resume(state, session_id)
    assert handle.task == TASK, f"task mismatch: {handle.task!r}"

    python_finding = state.read("finding:1")
    node_finding = state.read("finding:2")
    assert python_finding is not None and python_finding.value["source"] == "python"
    assert node_finding is not None and node_finding.value["source"] == "typescript"

    status_history = [r.value for r in state.history(f"session:{session_id}:status")]
    assert status_history[0] == "init", status_history
    checkpoint_count = sum(1 for s in status_history if s.startswith("checkpoint:"))
    assert checkpoint_count == 2, f"expected 2 checkpoints (one per language), got {checkpoint_count}: {status_history}"

    lifecycle.teardown(handle, reason="interop proof complete")
    final_status = state.history(f"session:{session_id}:status")[-1].value
    assert final_status == "teardown:interop proof complete"

    print("INTEROP PROOF PASSED")
    print(f"  session: {session_id}")
    print(f"  status history: {status_history + [final_status]}")
    print(f"  python wrote:  {python_finding.value}")
    print(f"  node wrote:    {node_finding.value}")


if __name__ == "__main__":
    main()
