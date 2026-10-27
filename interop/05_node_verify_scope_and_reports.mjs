// Step 5 of the interop proof: Node reads what Python exported in step 4
// and independently proves it means the same thing here.
//
// For scope: reconstructs a TableScopeEnforcer from Python's exported
// capability list and runs check() calls of its own — including one
// Python never ran, to show this is real independent evaluation against
// the reconstructed scope, not a copy of Python's reported answers.
//
// For verification: reads both VerificationReports and asserts their
// fields decode with the right types and the right meaning — proving the
// snake_case wire format (duration_s, not durationS) isn't just an
// intention, it's what actually round-trips.

import { JsonFileStateStore, TableScopeEnforcer } from "../ts/dist/src/reference/index.js";

const [, , statePath] = process.argv;
if (!statePath) {
  console.error("usage: node 05_node_verify_scope_and_reports.mjs <state-path>");
  process.exit(1);
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${expected}, got ${actual}`);
  }
}

const state = new JsonFileStateStore(statePath);

// --- Scope ---
const scopeRecord = state.read("scope:shared");
if (scopeRecord === null) {
  throw new Error("could not read scope:shared — did step 4 run first?");
}

const scope = TableScopeEnforcer.fromCapabilities(scopeRecord.value);

// Checks Python also implicitly covers (same patterns, same kind).
assertEqual(
  scope.check({ kind: "path", pattern: "/workspace/report.md" }),
  true,
  "granted path pattern should allow a direct child",
);
assertEqual(
  scope.check({ kind: "command", pattern: "pytest" }),
  true,
  "granted command should be allowed",
);
assertEqual(
  scope.check({ kind: "path", pattern: "/etc/passwd" }),
  false,
  "ungranted path should be denied",
);
assertEqual(
  scope.check({ kind: "command", pattern: "rm" }),
  false,
  "ungranted command should be denied",
);

// A check Python's script never ran: a nested path under the glob, which
// exercises fnmatch-style "*" matching across "/" (not pathname-restricted
// globbing) — this has to be independently re-derived from the
// reconstructed scope, not copied from a Python-reported answer.
assertEqual(
  scope.check({ kind: "path", pattern: "/workspace/sub/dir/report.md" }),
  true,
  "granted path pattern should allow a nested descendant (fnmatch '*' crosses '/')",
);

console.log(`node reconstructed scope (${scopeRecord.value.length} capabilities) ` +
  "and independently confirmed 5 check() results, including one Python never ran");

// --- Verification reports ---
const passReport = state.read("verify:pass_report");
const failReport = state.read("verify:fail_report");
if (passReport === null || failReport === null) {
  throw new Error("could not read verify:pass_report / verify:fail_report");
}

for (const [name, report] of [["pass_report", passReport.value], ["fail_report", failReport.value]]) {
  if (typeof report.passed !== "boolean") {
    throw new Error(`${name}.passed should decode as a boolean, got ${typeof report.passed}`);
  }
  if (typeof report.evidence !== "string") {
    throw new Error(`${name}.evidence should decode as a string, got ${typeof report.evidence}`);
  }
  if (typeof report.duration_s !== "number" || report.duration_s < 0) {
    throw new Error(`${name}.duration_s should decode as a non-negative number, got ${report.duration_s}`);
  }
}

assertEqual(passReport.value.passed, true, "pass_report.passed");
assertEqual(failReport.value.passed, false, "fail_report.passed");

console.log("node read back both VerificationReports with correct types and values " +
  "(passed: boolean, evidence: string, duration_s: number) — the snake_case wire format round-trips");
