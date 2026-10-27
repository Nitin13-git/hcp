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
