import type { VerificationReport, Verifier } from "../verification.js";

export interface HttpVerifierOptions {
  expectedStatus?: number;
  bodyContains?: string;
  timeoutMs?: number;
  evidenceLimit?: number;
}

/**
 * Verifies a target by making an HTTP GET request and checking the response.
 *
 * `target` is a URL. A check passes when the response status matches
 * `expectedStatus` and, if `bodyContains` is set, the response body
 * contains that substring too — a status code alone is a weak check on
 * its own (a 200 from the wrong page still "passes"). Evidence is the
 * status plus truncated body, so a caller can see why a check failed
 * without re-running it.
 *
 * Use this for checking a live service's response (did the patched
 * endpoint actually stop leaking data); use `SubprocessVerifier` for
 * running a local test suite or command instead. Unlike
 * `SubprocessVerifier`, `run` here returns a Promise — HTTP requests are
 * inherently async in Node, and `Verifier.run`'s return type was widened
 * to accommodate that.
 */
export class HttpVerifier implements Verifier {
  private readonly expectedStatus: number;
  private readonly bodyContains: string | undefined;
  private readonly timeoutMs: number;
  private readonly evidenceLimit: number;

  constructor(options: HttpVerifierOptions = {}) {
    this.expectedStatus = options.expectedStatus ?? 200;
    this.bodyContains = options.bodyContains;
    this.timeoutMs = options.timeoutMs ?? 10_000;
    this.evidenceLimit = options.evidenceLimit ?? 4000;
  }

  async run(target: string): Promise<VerificationReport> {
    const start = performance.now();
    let status: number;
    let body: string;

    try {
      const response = await fetch(target, {
        method: "GET",
        signal: AbortSignal.timeout(this.timeoutMs),
      });
      status = response.status;
      body = await response.text();
    } catch (error) {
      const duration_s = (performance.now() - start) / 1000;
      const message = error instanceof Error ? error.message : String(error);
      return {
        passed: false,
        evidence: `request failed: ${message}`.slice(0, this.evidenceLimit),
        duration_s,
      };
    }

    let passed = status === this.expectedStatus;
    if (passed && this.bodyContains !== undefined) {
      passed = body.includes(this.bodyContains);
    }

    const duration_s = (performance.now() - start) / 1000;
    return {
      passed,
      evidence: `status=${status}\n${body}`.slice(0, this.evidenceLimit),
      duration_s,
    };
  }
}
