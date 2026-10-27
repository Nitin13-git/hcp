<!-- DRAFT — not posted. Review before submitting to news.ycombinator.com. -->

## Title

Show HN: HCP – a protocol for agent harnesses, with a Python/TS interop proof

(Alternative, more concrete: "Show HN: I tested whether my protocol's
Python and TypeScript SDKs actually agree with each other")

## Founder's first comment

Hi HN. I've been building tooling around running AI agents against
security-benchmark tasks, and kept rebuilding the same four things for
every harness: somewhere durable to put state, a way to verify an agent's
claimed result instead of trusting it, a least-privilege scope the agent
can't talk its way around, and init/checkpoint/teardown hooks so a session
survives a restart. HCP is those four as a shared interface, with a Python
and a TypeScript reference SDK.

The thing I actually want feedback on: most things calling themselves "a
protocol" are one implementation with a spec document attached, and nobody
checks whether a second independent implementation actually interoperates.
So I wrote a test for that — a session started by the Python SDK gets
resumed, continued, and verified by the TypeScript SDK, through nothing but
a shared JSON state file, with each step independently checking what the
other language wrote. It's in `interop/` if you want to see exactly what
crosses the language boundary.

Building that test immediately found a real bug (a session's task
description was never persisted, only held in memory — so "resume this
elsewhere" wasn't actually possible until I fixed it), which I think is
more interesting than the test passing.

Honest limitations, stated upfront: this proves interop for two of the
four interfaces (state, lifecycle) — scope and verification interop aren't
tested yet. I'm also aware I'm not the only person trying to standardize
this — there are at least two other efforts in this exact space (AHP,
A2E), and I'd rather compare notes with them than pretend this is
greenfield.

60-second runnable demo (not just a spec to read):

```
pip install "git+https://github.com/Nitin13-git/hcp.git" && python -m hcp.demo
```

Repo: https://github.com/Nitin13-git/hcp

Genuinely interested in pushback, especially from anyone who's hit the
"do my two SDKs actually agree, or do I just have two libraries" problem
themselves.
