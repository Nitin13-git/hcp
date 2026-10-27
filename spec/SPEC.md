# HCP — Harness Context Protocol (v0.1 draft)

## Why

MCP standardized how an agent talks to a *tool*. It said nothing about how an
agent's surrounding harness — the thing that holds state across turns,
decides what the agent is allowed to touch, checks whether the agent's work
is actually correct, and manages the session's start/checkpoint/end — should
behave. Every agent framework reinvents that layer from scratch, and no two
are compatible.

HCP standardizes the harness layer itself. A runtime that "speaks HCP"
exposes four interfaces. Anything that implements them — a CLI tool, an
orchestrator, a CI pipeline — can plug into any HCP-compliant agent runtime,
and vice versa.

## The four interfaces

### 1. State (`hcp.state.StateStore`)

Persists session state outside the model's context window: receipts of
completed work, progress against a task list, and a replayable history of
what happened. The repository (or equivalent durable store) is the source of
truth, not the conversation.

Required methods: `read(key) -> StateRecord | None`, `write(key, value,
*, by) -> StateRecord`, `history(key) -> list[StateRecord]`,
`checkpoint(label) -> str` (returns a checkpoint id).

### 2. Verification (`hcp.verification.Verifier`)

Reports pass/fail/evidence back to whatever is driving the session. A
verifier never trusts the agent's own claim that something works; it runs an
independent check and returns structured evidence.

Required methods: `run(target) -> VerificationReport`. `VerificationReport`
carries `passed: bool`, `evidence: str`, and `duration_s: float` — enough for
a caller to decide whether to trust the result without re-deriving it.

### 3. Scope (`hcp.scope.ScopeEnforcer`)

Declares and enforces the least-privilege capability set for a session:
which paths, commands, and network destinations are reachable. A scope is
computed per-task, not granted globally.

Required methods: `grant(capability) -> None`, `check(capability) -> bool`,
`active_scope() -> frozenset[Capability]`.

### 4. Lifecycle (`hcp.lifecycle.SessionLifecycle`)

Standard init/checkpoint/teardown hooks so sessions compose: a session
started by one tool can be checkpointed and resumed by another, as long as
both speak HCP.

Required methods: `init(task) -> SessionHandle`, `checkpoint(handle) ->
str`, `teardown(handle, *, reason) -> None`.

## Conformance

A harness implementation is HCP-conformant if it implements all four
interfaces and passes `hcp.validator.validate(harness)`, which checks method
presence, return-type shape, and the behavioral invariants described above
(e.g. `checkpoint` must be idempotent-safe to call twice with the same
label).

This is a v0.1 draft: the reference implementation in `hcp/reference/` is
intentionally minimal (local filesystem state, subprocess-based
verification, an in-memory scope table) so the interfaces stay the
contract, not the implementation.
