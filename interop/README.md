# Cross-language interop proof

HCP's [root README](../README.md) flagged this as the real open question:
"no test yet proves a session can actually hand off between the Python and
TS implementations through a shared `StateStore`." This is that test.

## What it proves

1. **Python** starts a session (`FileLifecycle.init`), writes a finding,
   checkpoints.
2. **Node.js**, in a *separate process*, resumes the *same* session using
   only the session id and the shared `state.json` file — no out-of-band
   knowledge of the task string. It reads Python's finding (proving the
   JSON shape is actually readable cross-language, not just
   superficially similar), writes its own finding, and checkpoints again.
3. **Python** resumes a second time, verifies both findings are present,
   verifies the full status history reflects both languages' activity, and
   tears the session down.

If any step can't read what the other language wrote, or `resume()` can't
reconstruct the handle from state alone, the script fails loudly — this
isn't a demo that only shows the happy path by construction.

## Run it

```bash
./run_interop.sh
```

Requires `hcp` installed (`pip install -e ..`) and Node 18+. The script
builds the TypeScript SDK itself.

## What running it for real surfaced

Both checkpoint calls return the *same* checkpoint id
(`session:<id>-0`), even though they happen in different languages at
different times. That's because `checkpoint()` is idempotent per label
(by spec — calling it twice with the same label must return the existing
id), and both `FileLifecycle` implementations checkpoint under the same
label (`session:<id>`) for the whole life of a session. The status
history still shows two distinct checkpoint *events* happened (one
Python, one Node) — so "did a checkpoint happen, and when" is visible —
but the current reference implementations don't distinguish *which*
snapshot each one corresponds to beyond that. Not a bug against the spec
as written; a real limitation worth knowing if you build on this.

## What this does and doesn't prove

It proves the `StateStore` wire format and the `resume()` reconstruction
path work identically across both reference implementations, for the
state and lifecycle subsystems specifically. It does not prove interop for
`ScopeEnforcer` or `Verifier` — those aren't exercised here, because
nothing about scope or verification needs to cross the language boundary
in this scenario. A fuller proof would also hand off an active `Scope`
grant and show both languages enforce it identically; that's a reasonable
next extension, not yet built.
