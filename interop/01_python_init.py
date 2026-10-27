"""Step 1 of the interop proof: a Python-driven session starts.

Writes one finding and checkpoints, then exits. Prints only the session id
to stdout — the orchestrating shell script passes that to step 2.
"""

from __future__ import annotations

import sys

from hcp.reference import FileLifecycle, JsonFileStateStore

TASK = "cross-language interop proof: recon then verify"


def main() -> None:
    state_path = sys.argv[1]
    state = JsonFileStateStore(state_path)
    lifecycle = FileLifecycle(state)

    handle = lifecycle.init(TASK)
    state.write(
        "finding:1",
        {"source": "python", "detail": "initial recon complete"},
        by="python-session",
    )
    lifecycle.checkpoint(handle)

    print(handle.session_id)


if __name__ == "__main__":
    main()
