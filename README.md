# HCP — Harness Context Protocol

MCP standardized how an agent talks to a *tool*. HCP standardizes the
*harness* around the agent: how a session's state outlives the context
window, how work gets independently verified instead of self-reported, how
least-privilege scope is computed and enforced per task, and how a session's
init/checkpoint/teardown lifecycle composes across tools.

Full spec: [`spec/SPEC.md`](spec/SPEC.md).

## The four interfaces

| Interface | Module | Answers |
|---|---|---|
| State | `hcp.state.StateStore` | Where does session state live outside the model's context? |
| Verification | `hcp.verification.Verifier` | Who checks the agent's work is actually correct? |
| Scope | `hcp.scope.ScopeEnforcer` | What is this session allowed to touch, and who enforces it? |
| Lifecycle | `hcp.lifecycle.SessionLifecycle` | How does a session start, checkpoint, and end? |

Each is an abstract interface with one reference implementation under
`hcp.reference` — a local JSON file store, a subprocess-based verifier, an
in-memory scope table, and a lifecycle built on top of the state store.
Swap any of them out without touching the others.

## Quickstart

```bash
pip install -e ".[dev]"
python examples/minimal_harness.py
pytest
```

```python
from hcp.reference import JsonFileStateStore, SubprocessVerifier, TableScopeEnforcer, FileLifecycle
from hcp.validator import validate

state = JsonFileStateStore("state.json")
harness = {
    "state": state,
    "verification": SubprocessVerifier(),
    "scope": TableScopeEnforcer(),
    "lifecycle": FileLifecycle(state),
}

report = validate(harness)
assert report.conformant
```

## Status

v0.1 draft. The interfaces are the contract; the reference implementations
are intentionally minimal and meant to be replaced (a git-backed
`StateStore`, a sandboxed `ScopeEnforcer`, a CI-integrated `Verifier`, etc.)
without breaking anything that depends on the interface alone.

## License

MIT
