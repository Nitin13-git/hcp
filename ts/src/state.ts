/**
 * Durable, out-of-context state for a harness session.
 *
 * Whatever this is backed by is the source of truth. Nothing here may
 * rely on the model's conversation history to recover state — a fresh
 * session with no memory of prior turns must be able to call `read` and
 * get the same answer a continuing session would.
 *
 * Field names are snake_case to match the Python reference SDK's JSON
 * wire format exactly (`key`, `value`, `by`, `at`) — a deliberate choice
 * so a state file written by one language's reference implementation is
 * byte-identical in shape to one written by the other, which is the
 * precondition for cross-language interop (see HCP's Open Problems: #4).
 */
export interface StateRecord {
  key: string;
  value: unknown;
  by: string;
  at: string; // ISO 8601 timestamp
}

export interface StateStore {
  read(key: string): StateRecord | null;
  write(key: string, value: unknown, by: string): StateRecord;
  history(key: string): StateRecord[];
  /**
   * Snapshot current state under `label`; return a checkpoint id.
   *
   * Calling this twice with the same label must not error and must not
   * duplicate the checkpoint — the second call returns the existing id.
   */
  checkpoint(label: string): string;
}
