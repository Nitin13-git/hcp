---
title: I built a protocol, then wrote a test to prove I wasn't lying to myself
published: false
tags: opensource, python, typescript, agents
---

Most things that call themselves "a protocol" are really one implementation
with a spec document bolted on. Nobody's actually checked whether a second,
independent implementation can talk to the first one. I'd done exactly that
with [HCP](https://github.com/Nitin13-git/hcp) — a Python SDK, a TypeScript
SDK I added later to reach a bigger audience, both claiming to speak the
same four-interface protocol for AI agent harnesses (state, verification,
scope, lifecycle) — and had no actual evidence they did.

So I wrote a test that would catch me if I was wrong.

## The test

Three steps, one shared file, two languages:

1. A **Python** process starts a session, writes a finding, checkpoints.
2. A **separate Node.js process** resumes *that exact session* — given
   nothing but the session id — reads what Python wrote, writes its own
   finding, checkpoints again.
3. **Python** resumes a third time, verifies both findings are present,
   checks the full status history, and tears the session down.

If step 2 can't read what step 1 wrote, or can't reconstruct the session
from the shared state file alone, the test fails loudly. There's no path
where this quietly passes without actually proving the thing.

## It immediately found a real bug

Before I could even write step 2, I hit this: a session's `task`
description — "investigate the login endpoint," whatever it is — was only
ever held in memory, in the object returned by `init()`. Nothing wrote it
to the shared state store. Which meant "resume this session from a
different process" was never actually possible — you'd need to already
know the task string from somewhere else, defeating the entire point of
state being durable.

This wasn't a hypothetical gap I found by reading the code carefully. It's
the kind of bug that only surfaces when you try to use your own interface
for real, across a process boundary, instead of just calling methods on an
object you already have a reference to. Fixed it by writing
`session:<id>:task` as its own state record, and added a `resume()`
function to reconstruct a handle from that — now shipped in both SDKs.

## It also surfaced a nuance worth knowing, not a bug

Once the test passed, I noticed both checkpoint calls — the Python one and
the Node one — returned the *same* checkpoint id. Not a bug: `checkpoint()`
is specified to be idempotent per label, and both languages checkpoint
under the same label for a session's whole lifetime. The status history
correctly shows two separate checkpoint *events* happened (you can see
*when* each language checkpointed), but the current reference
implementations don't distinguish *which snapshot* each one corresponds to
beyond that. If you're building on this and need per-checkpoint
granularity, that's worth knowing before you hit it in production instead
of after.

## What this actually proves, and what it doesn't

It proves the `StateStore` and `SessionLifecycle` interfaces compose
across two independently-written implementations in two different
languages — not just two copies of the same code. It does **not** prove
interop for `ScopeEnforcer` or `Verifier` — this scenario didn't need
either to cross the language boundary, so neither was exercised. "Fully
cross-language" isn't proven for all four interfaces, just the two this
specific handoff needed. I'd rather say that plainly than let the headline
imply more than the test actually checked.

## Try it

```bash
pip install "git+https://github.com/Nitin13-git/hcp.git" && python -m hcp.demo
```

That runs all four subsystems for real in under a second. The interop
proof itself is in [`interop/`](https://github.com/Nitin13-git/hcp/tree/main/interop)
— `./run_interop.sh` runs the full three-step handoff and prints the raw
`state.json` at the end so you can see exactly what crossed the language
boundary.

If you're building something in this space, I'd genuinely like to compare
notes — especially if you've hit the same "does my protocol actually
compose, or do I just have two libraries that happen to agree with each
other" question.
