/**
 * Independently checks whether a target's claimed state is true.
 *
 * A Verifier never takes the agent's word for it: `run` must perform its
 * own check (running tests, diffing a snapshot, hitting an endpoint) and
 * return evidence a caller can inspect without re-deriving the result.
 */
export interface VerificationReport {
  passed: boolean;
  evidence: string;
  duration_s: number;
}

export interface Verifier {
  /**
   * Returns a VerificationReport, or a Promise of one.
   *
   * Widened from a plain VerificationReport to accommodate verifiers that
   * are inherently async in Node (an HTTP check, for instance) without
   * forcing synchronous ones (SubprocessVerifier) to change at all — a
   * sync return value is already assignable to this union, so existing
   * implementations and their call sites are unaffected.
   */
  run(target: string): VerificationReport | Promise<VerificationReport>;
}
