import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  JsonFileStateStore,
  SubprocessVerifier,
  TableScopeEnforcer,
  FileLifecycle,
} from "../src/reference/index.js";
import { validate } from "../src/validator.js";

function tmpStatePath(): string {
  const dir = mkdtempSync(join(tmpdir(), "hcp-test-"));
  return join(dir, "state.json");
}

test("full reference harness is conformant", () => {
  const state = new JsonFileStateStore(tmpStatePath());
  const report = validate({
    state,
    verification: new SubprocessVerifier(),
    scope: new TableScopeEnforcer(),
    lifecycle: new FileLifecycle(state),
  });
  assert.equal(report.conformant, true);
  assert.deepEqual(report.missing, []);
});

test("partial harness reports missing interfaces", () => {
  const report = validate({ state: new JsonFileStateStore(tmpStatePath()) });
  assert.equal(report.conformant, false);
  assert.deepEqual(report.missing.sort(), ["lifecycle", "scope", "verification"]);
});

test("object missing required methods is reported as an error", () => {
  const report = validate({
    state: {},
    verification: {},
    scope: {},
    lifecycle: {},
  });
  assert.equal(report.conformant, false);
  assert.equal(report.errors.length, 4);
});
