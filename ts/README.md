# HCP — TypeScript reference SDK

The same Harness Context Protocol as the [Python SDK](../README.md), ported
to TypeScript: four interfaces (state, verification, scope, lifecycle), a
minimal reference implementation of each, and a conformance validator.

## A deliberate design choice: snake_case fields

`StateRecord`, `VerificationReport`, and `SessionHandle` use snake_case
field names (`duration_s`, `session_id`) instead of idiomatic TypeScript
camelCase. That's not an oversight — it's so a state file written by the
Python reference's `JsonFileStateStore` and one written by this package's
`JsonFileStateStore` are byte-identical in shape. Cross-language interop
(can a Python-driven session hand off to a TypeScript-driven one through
the same `StateStore`?) is listed as an open problem in the project this
protocol is used by; keeping the wire format identical from day one is the
precondition for ever answering it, even though it isn't proven yet.

## A real difference from the Python SDK: how conformance is checked

The Python `validate()` checks `isinstance(obj, SomeABC)` — nominal typing,
enforced by Python's ABC machinery. TypeScript interfaces are structural
and erased at runtime, so there's no equivalent `instanceof` check.
`validate()` here does the TypeScript-native equivalent: it checks that
each required method exists and is a function (duck typing). Both
validators answer "does this object fulfill the contract," but by
genuinely different mechanisms — documented here rather than presented as
if the two SDKs work identically under the hood.

## Two reference verifiers

`SubprocessVerifier` runs a local command and checks its exit status — good
for "does the test suite pass." `HttpVerifier` hits a live endpoint and
checks its status code and (optionally) response body — good for "did the
patched service actually stop leaking data." `HttpVerifier.run` returns a
`Promise<VerificationReport>`, since HTTP requests are inherently async in
Node; `Verifier.run`'s return type is `VerificationReport |
Promise<VerificationReport>` to accommodate that without changing
`SubprocessVerifier` or any existing sync call site at all.

## Quickstart

```bash
npm install hcp-protocol
```

```typescript
import {
  JsonFileStateStore,
  SubprocessVerifier,
  TableScopeEnforcer,
  FileLifecycle,
} from "hcp-protocol/reference";
import { validate } from "hcp-protocol";

const state = new JsonFileStateStore("state.json");
const harness = {
  state,
  verification: new SubprocessVerifier(),
  scope: new TableScopeEnforcer(),
  lifecycle: new FileLifecycle(state),
};

const report = validate(harness);
console.assert(report.conformant);
```

## Development setup

```bash
npm install
npm test
```

## Status

v0.1, same as the Python SDK — interfaces are the contract, reference
implementations are intentionally minimal and meant to be replaced.
[`interop/`](https://github.com/Nitin13-git/hcp/tree/main/interop) now
proves cross-language interop for all four interfaces against the Python
SDK — a real session hand-off (state + lifecycle), plus a Scope grant and
Verifier reports that round-trip and get independently re-evaluated by
this package, not just echoed back.

## License

MIT
