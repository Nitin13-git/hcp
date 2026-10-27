# HCP — Harness Context Protocol

[![PyPI](https://img.shields.io/pypi/v/hcp-protocol?label=PyPI&color=3775A9)](https://pypi.org/project/hcp-protocol/)
[![npm](https://img.shields.io/npm/v/hcp-protocol?label=npm&color=CB3837)](https://www.npmjs.com/package/hcp-protocol)

MCP standardized how an agent talks to a *tool*. HCP standardizes the
*harness* around the agent: state that outlives the context window,
verification that doesn't trust the agent's own report, least-privilege
scope, and a session lifecycle that survives a process restart.

```bash
pip install hcp-protocol && python -m hcp.demo
```

TypeScript SDK: `npm install hcp-protocol` ([docs](https://github.com/Nitin13-git/hcp/tree/main/ts)).

![All four HCP subsystems running for real, in under a second](https://raw.githubusercontent.com/Nitin13-git/hcp/main/assets/demo.gif)

That's real code, not staged output — scope denying by default, a false
claim caught by independent verification next to a real fix that passes,
and a brand-new process recovering a session's task and findings given
nothing but a session id. Source: [`src/hcp/demo.py`](https://github.com/Nitin13-git/hcp/blob/main/src/hcp/demo.py).

Full spec: [`spec/SPEC.md`](https://github.com/Nitin13-git/hcp/blob/main/spec/SPEC.md).
Two reference SDKs: Python (this package) and
[TypeScript](https://github.com/Nitin13-git/hcp/tree/main/ts) — both
implement the same four interfaces against the same JSON wire format, so a
state file is byte-identical in shape regardless of which SDK wrote it, and
[`interop/`](https://github.com/Nitin13-git/hcp/tree/main/interop) proves a
session can actually hand off between them.

## The four interfaces

| Interface | Module | Answers |
|---|---|---|
| State | `hcp.state.StateStore` | Where does session state live outside the model's context? |
| Verification | `hcp.verification.Verifier` | Who checks the agent's work is actually correct? |
| Scope | `hcp.scope.ScopeEnforcer` | What is this session allowed to touch, and who enforces it? |
| Lifecycle | `hcp.lifecycle.SessionLifecycle` | How does a session start, checkpoint, and end? |

Each is an abstract interface with reference implementations under
`hcp.reference` — a local JSON file store, an in-memory scope table, a
lifecycle built on top of the state store, and **two** verifiers:
`SubprocessVerifier` (run a local command, check its exit status — good
for "does the test suite pass") and `HttpVerifier` (hit a live endpoint,
check its status and response body — good for "did the patched service
actually stop leaking data"). Swap any of them out without touching the
others.

## Development setup

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

The [TypeScript SDK](https://github.com/Nitin13-git/hcp/tree/main/ts)
mirrors this one field-for-field on the wire (snake_case `duration_s`,
`session_id`, etc., even though that's not idiomatic TS) but checks
conformance differently: Python's `validate()` does a nominal `isinstance`
check via ABCs; TypeScript's does structural duck-typing, since interfaces
are erased at runtime.

[`interop/`](https://github.com/Nitin13-git/hcp/tree/main/interop) now
proves cross-language interop for **all four**
interfaces, not just two: steps 1-3 hand off a real session between
Python and Node.js through nothing but shared `state.json` (`StateStore`,
`SessionLifecycle`); steps 4-5 have Python grant a `Scope` and run real
`Verifier` checks, then have Node independently reconstruct the scope and
re-evaluate it — including a check Python's script never ran — and assert
both `VerificationReport`s decode with the right types. What's still open:
interop across different agent *runtimes*, not just these two reference
SDKs of the same protocol (see Open Problem #4 in the
[course site](https://nitin13-git.github.io/learn-harness-security/open-problems/)).

## License

MIT
