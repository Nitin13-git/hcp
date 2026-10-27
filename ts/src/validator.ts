/**
 * Checks whether a harness implements the four HCP interfaces.
 *
 * TypeScript interfaces are structural and erased at runtime — there's no
 * `instanceof` check equivalent to the Python SDK's ABC-based
 * `isinstance`. This validator does the TypeScript-native equivalent
 * instead: duck-typing, checking that each required method exists and is
 * a function. That's a real difference from the Python SDK's conformance
 * check (nominal vs. structural), not just a syntax difference — it's
 * documented here rather than glossed over, matching this project's
 * stance on open problems.
 */

const REQUIRED_METHODS: Record<string, string[]> = {
  state: ["read", "write", "history", "checkpoint"],
  verification: ["run"],
  scope: ["grant", "check", "activeScope"],
  lifecycle: ["init", "checkpoint", "teardown"],
};

export interface HarnessCandidates {
  state?: unknown;
  verification?: unknown;
  scope?: unknown;
  lifecycle?: unknown;
}

export interface ConformanceReport {
  conformant: boolean;
  implemented: string[];
  missing: string[];
  errors: string[];
}

export function validate(harness: HarnessCandidates): ConformanceReport {
  const errors: string[] = [];
  const implemented: string[] = [];

  for (const [name, methods] of Object.entries(REQUIRED_METHODS)) {
    const obj = harness[name as keyof HarnessCandidates] as
      | Record<string, unknown>
      | undefined
      | null;

    if (obj === undefined || obj === null) {
      errors.push(`${name}: no implementation provided`);
      continue;
    }

    const missingMethods = methods.filter((m) => typeof obj[m] !== "function");
    if (missingMethods.length > 0) {
      errors.push(`${name}: missing method(s) ${missingMethods.join(", ")}`);
      continue;
    }

    implemented.push(name);
  }

  const missing = Object.keys(REQUIRED_METHODS).filter(
    (name) => !implemented.includes(name),
  );

  return {
    conformant: missing.length === 0 && errors.length === 0,
    implemented,
    missing,
    errors,
  };
}
