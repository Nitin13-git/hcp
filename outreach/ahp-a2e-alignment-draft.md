<!--
DRAFT — NOT SENT.

Neither AHP nor A2E has GitHub Discussions enabled (checked via
`gh api repos/<owner>/<repo> --jq .has_discussions`, both false). Both
have Issues enabled, which is the only available contact path found —
no listed Discord, no named maintainer email, no homepage URL on either
repo. Sending this means manually opening a GitHub Issue on the target
repo with this text. Pick ONE target (A2E's repo is more active; AHP's
has more commits/history) rather than cross-posting the same issue to
both, unless you want to post a tailored version to each.

Full research behind this draft:
/Users/nitin/harness_engineering/learn-harness-security/docs/frontier/ahp-a2e-breakdown.md
-->

## Target

- A2E: https://github.com/a2eprotocol/python-sdk/issues (1 contributor, most recent commit Oct 2026)
- AHP: https://github.com/a3s-lab/agentharnessprotocol/issues (30 commits, most recent push Sept 2026)

## Suggested issue title

"Possible overlap with another harness-protocol effort — worth comparing notes?"

## Draft body

Hi — I maintain [HCP](https://github.com/Nitin13-git/hcp) (Harness
Context Protocol), a small project standardizing four interfaces for AI
agent harnesses: durable state, independent verification, least-privilege
scope, and session lifecycle. I came across your project while trying to
understand what else exists in this space, and wanted to flag the overlap
directly rather than build in parallel without saying anything.

To be upfront about where things stand: HCP is newer and smaller than
yours by every measure I could check (commit history, time since first
commit). I'm not approaching this as equals proposing a merger — more
as one small project checking whether a bigger, earlier one has already
solved problems I'm about to hit, or would find it useful to compare
designs.

The specific thing I'd value your take on: [HCP's verification interface](https://github.com/Nitin13-git/hcp/blob/main/src/hcp/verification.py)
is built around independent evidence (`run(target) -> VerificationReport`
with evidence a caller can audit, not a self-report or a feedback score).
From what I could read in your public docs, your project's evaluation
path [routes through <learn's feedback/self-critique OR the
runtime-contract verification events — edit to match whichever project
you're sending this to] — I may be misreading the design intent, and
would rather ask than assume.

The reason I'm raising this instead of just quietly building a competing
spec: OpenTelemetry didn't win by out-competing OpenTracing and
OpenCensus — it formed in 2019 by merging them, specifically because
users having to guess which one would survive was hurting adoption of
both (https://cncf.io/blog/2019/05/21/a-brief-history-of-opentelemetry-so-far).
I don't know if alignment makes sense here — our designs differ in real
ways (your [event/namespace model] vs. my four fixed interfaces) — but it
seemed worth asking before three small, independent efforts spend another
year solving the same problem three times.

Happy to share more detail on how HCP's reference SDKs work, including a
[cross-language interop proof](https://github.com/Nitin13-git/hcp/tree/main/interop)
between its Python and TypeScript implementations, if that's useful
context. No expectation of a particular outcome here — genuinely just
asking.

<!-- Edit the bracketed section above to name the specific target
(AHP's runtime-contract verification events, or A2E's learn/feedback
self-critique path) before sending. Sending the same generic text to
both without that edit would read as not having actually read either
project's docs. -->
