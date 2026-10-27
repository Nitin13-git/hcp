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

## Steps 4-5: Scope and Verifier

Scope and Verifier don't have sessions to "resume" — a `Scope`'s grants
live in memory, and a `Verifier`'s result is a one-off report. So interop
for these means something narrower and more concrete: does the JSON each
language's reference implementation produces decode correctly, with the
right types and the right meaning, in the other language?

4. **Python** grants a `Scope` (a path glob, a command name), exports the
   granted capabilities, and runs `SubprocessVerifier` twice (a passing
   check and a failing one) — writing the scope export and both
   `VerificationReport`s to the shared state file as plain data.
5. **Node** reads the exported scope back and reconstructs a
   `TableScopeEnforcer` from it via `fromCapabilities()`, then runs its
   *own* `check()` calls against it — including one Python's script never
   ran (a nested path under the granted glob), so this is real independent
   re-evaluation, not Node echoing Python's reported answers. It also
   reads both `VerificationReport`s and asserts `passed` decodes as a
   boolean, `evidence` as a string, and `duration_s` as a non-negative
   number — confirming the deliberately snake_case wire format actually
   round-trips, not just that the field names were chosen to match.

Ran clean on the first real attempt — no surprises this time, unlike steps
1-3's checkpoint-idempotency finding. `Capability` and `VerificationReport`
turned out to already be flat, enum-free-on-the-wire records once
serialized (Python's `str, Enum` `CapabilityKind` encodes as a plain JSON
string automatically), so the only code needed was the dict/array ->
object reconstruction step (`from_capability_dicts` / `fromCapabilities`),
not a custom wire format.

## What this does and doesn't prove

All four interfaces now have a cross-language interop test: `StateStore`
and `SessionLifecycle` via steps 1-3 (a real session handoff), `Scope` and
`Verifier` via steps 4-5 (wire-format fidelity plus independent
re-evaluation). What's still *not* proven: interop across different agent
*runtimes* (not just the two reference SDKs of the same protocol), and a
single scenario combining all four subsystems at once rather than testing
state/lifecycle and scope/verifier as two separate passes.
