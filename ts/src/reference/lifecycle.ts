import { randomUUID } from "node:crypto";
import type { StateStore } from "../state.js";
import type { SessionHandle, SessionLifecycle } from "../lifecycle.js";

/**
 * SessionLifecycle backed by a StateStore for checkpointing.
 *
 * `init` and `teardown` just record events into the store under the
 * session id, so any other HCP-speaking tool reading the same store can
 * see whether a session is live, checkpointed, or torn down.
 */
export class FileLifecycle implements SessionLifecycle {
  constructor(private readonly state: StateStore) {}

  init(task: string): SessionHandle {
    const handle: SessionHandle = { session_id: randomUUID(), task };
    this.state.write(`session:${handle.session_id}:status`, "init", "hcp.lifecycle");
    this.state.write(`session:${handle.session_id}:task`, task, "hcp.lifecycle");
    return handle;
  }

  checkpoint(handle: SessionHandle): string {
    const checkpointId = this.state.checkpoint(`session:${handle.session_id}`);
    this.state.write(
      `session:${handle.session_id}:status`,
      `checkpoint:${checkpointId}`,
      "hcp.lifecycle",
    );
    return checkpointId;
  }

  teardown(handle: SessionHandle, reason: string): void {
    this.state.write(
      `session:${handle.session_id}:status`,
      `teardown:${reason}`,
      "hcp.lifecycle",
    );
  }
}

/**
 * Reconstruct a SessionHandle for a session started elsewhere.
 *
 * Works across processes, and across language implementations, as long
 * as both read the same StateStore — the handle's `task` is read back
 * from the record `init` wrote, not passed in out-of-band.
 */
export function resume(state: StateStore, sessionId: string): SessionHandle {
  const record = state.read(`session:${sessionId}:task`);
  if (record === null) {
    throw new Error(`no session found with id ${sessionId}`);
  }
  return { session_id: sessionId, task: record.value as string };
}
