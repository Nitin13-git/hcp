from __future__ import annotations

from hcp.lifecycle import SessionHandle, SessionLifecycle
from hcp.state import StateStore


class FileLifecycle(SessionLifecycle):
    """SessionLifecycle backed by a StateStore for checkpointing.

    `init` and `teardown` just record events into the store under the
    session id, so any other HCP-speaking tool reading the same store can
    see whether a session is live, checkpointed, or torn down.
    """

    def __init__(self, state: StateStore) -> None:
        self._state = state

    def init(self, task: str) -> SessionHandle:
        handle = SessionHandle(task=task)
        self._state.write(f"session:{handle.session_id}:status", "init", by="hcp.lifecycle")
        self._state.write(f"session:{handle.session_id}:task", task, by="hcp.lifecycle")
        return handle

    def checkpoint(self, handle: SessionHandle) -> str:
        checkpoint_id = self._state.checkpoint(f"session:{handle.session_id}")
        self._state.write(
            f"session:{handle.session_id}:status", f"checkpoint:{checkpoint_id}", by="hcp.lifecycle"
        )
        return checkpoint_id

    def teardown(self, handle: SessionHandle, *, reason: str) -> None:
        self._state.write(
            f"session:{handle.session_id}:status", f"teardown:{reason}", by="hcp.lifecycle"
        )


def resume(state: StateStore, session_id: str) -> SessionHandle:
    """Reconstruct a SessionHandle for a session started elsewhere.

    Works across processes, and across language implementations, as long
    as both read the same StateStore — the handle's `task` is read back
    from the record `init` wrote, not passed in out-of-band.
    """
    record = state.read(f"session:{session_id}:task")
    if record is None:
        raise KeyError(f"no session found with id {session_id!r}")
    return SessionHandle(session_id=session_id, task=record.value)
