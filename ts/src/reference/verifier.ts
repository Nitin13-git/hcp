import { spawnSync } from "node:child_process";
import type { VerificationReport, Verifier } from "../verification.js";

/**
 * Verifies a target by running it as a shell command and checking exit status.
 *
 * `target` is a command string, e.g. "npm test". Evidence is stdout+stderr,
 * truncated, so a caller can see why a check failed without re-running it.
 */
export class SubprocessVerifier implements Verifier {
  constructor(
    private readonly timeoutMs: number = 60_000,
    private readonly evidenceLimit: number = 4000,
  ) {}

  run(target: string): VerificationReport {
    const start = performance.now();
    const [command, ...args] = target.split(" ");
    const result = spawnSync(command, args, {
      encoding: "utf-8",
      timeout: this.timeoutMs,
      shell: false,
    });
    const duration_s = (performance.now() - start) / 1000;

    if (result.error) {
      return {
        passed: false,
        evidence: `failed to run: ${result.error.message}`.slice(0, this.evidenceLimit),
        duration_s,
      };
    }

    const evidence = `${result.stdout ?? ""}${result.stderr ?? ""}`.slice(
      0,
      this.evidenceLimit,
    );
    return { passed: result.status === 0, evidence, duration_s };
  }
}
