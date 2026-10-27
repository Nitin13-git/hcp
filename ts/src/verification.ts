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
  run(target: string): VerificationReport;
}
