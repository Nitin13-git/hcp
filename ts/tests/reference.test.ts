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
  resume,
} from "../src/reference/index.js";

function tmpStatePath(): string {
  const dir = mkdtempSync(join(tmpdir(), "hcp-test-"));
  return join(dir, "state.json");
}

test("state store roundtrip", () => {
  const store = new JsonFileStateStore(tmpStatePath());
  store.write("progress", { done: 1 }, "test");
  store.write("progress", { done: 2 }, "test");

  const latest = store.read("progress");
  assert.ok(latest !== null);
  assert.deepEqual(latest!.value, { done: 2 });
  assert.equal(store.history("progress").length, 2);
});

test("checkpoint is idempotent", () => {
  const store = new JsonFileStateStore(tmpStatePath());
  const first = store.checkpoint("phase-1");
  const second = store.checkpoint("phase-1");
  assert.equal(first, second);
});

test("scope denies by default", () => {
  const scope = new TableScopeEnforcer();
  assert.equal(scope.check({ kind: "path", pattern: "/etc/passwd" }), false);
});

test("scope allows granted pattern", () => {
  const scope = new TableScopeEnforcer();
  scope.grant({ kind: "path", pattern: "/repo/*" });
  assert.equal(scope.check({ kind: "path", pattern: "/repo/src/main.ts" }), true);
  assert.equal(scope.check({ kind: "path", pattern: "/etc/passwd" }), false);
});

test("verifier reports pass and fail", () => {
  const verifier = new SubprocessVerifier();
  const ok = verifier.run("true");
  const bad = verifier.run("false");
  assert.equal(ok.passed, true);
  assert.equal(bad.passed, false);
});

test("lifecycle records status transitions", () => {
  const store = new JsonFileStateStore(tmpStatePath());
  const lifecycle = new FileLifecycle(store);

  const handle = lifecycle.init("demo task");
  lifecycle.checkpoint(handle);
  lifecycle.teardown(handle, "done");

  const history = store.history(`session:${handle.session_id}:status`);
  assert.equal(history[0].value, "init");
  assert.equal(history[history.length - 1].value, "teardown:done");
});

test("resume reconstructs handle from state alone", () => {
  const store = new JsonFileStateStore(tmpStatePath());
  const lifecycle = new FileLifecycle(store);
  const original = lifecycle.init("investigate the login endpoint");

  const resumed = resume(store, original.session_id);

  assert.equal(resumed.session_id, original.session_id);
  assert.equal(resumed.task, original.task);
  assert.equal(resumed.task, "investigate the login endpoint");
});

test("resume throws for unknown session", () => {
  const store = new JsonFileStateStore(tmpStatePath());
  assert.throws(() => resume(store, "does-not-exist"));
});
