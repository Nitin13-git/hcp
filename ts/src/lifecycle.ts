export interface SessionHandle {
  session_id: string;
  task: string;
}

/**
 * Init/checkpoint/teardown hooks that let sessions compose.
 *
 * A session started by one HCP-speaking tool must be resumable by a
 * different tool that also speaks HCP, as long as both read the same
 * checkpoint id back through a shared StateStore.
 */
export interface SessionLifecycle {
  init(task: string): SessionHandle;
  checkpoint(handle: SessionHandle): string;
  teardown(handle: SessionHandle, reason: string): void;
}
