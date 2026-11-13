# Decisions and rationale

## D1. Keep OpenRig execution separate from workflow-group control

OpenRig owns rigs, seats, queue packets, workflow instances, and steps.
Workflow-group owns goals, rounds, decisions, and acceptance. Mixing them makes
people say “the workflow finished” when only a step closed.

## D2. Use one bounded workflow before scaling to a team

A single-seat, single-output workflow exposes the real failure modes: no output
file, a closed packet with no evidence, a seat that keeps calling tools without a
stop condition, or a spec that validates but never executes. Scale only after
the small loop is boring.

## D3. Keep three governance dimensions distinct

- Command Center: rounds and conflicts.
- General Staff: thinking quality and reusable dimensions.
- SOLO: one-off governed work.

They are related but not interchangeable. “组织部” is an alias for Command
Center, not a fourth layer. If a name is unfamiliar, match its responsibility or
ask once with concrete options.

## D4. Make the stamp the identity, not the folder name

A round can be moved or archived; its identity should travel with a small stamp
file. The registry references the stamp, and QA verifies both. A folder name is a
human convenience, not a source of truth.

## D5. Propose patches; never auto-apply them

For injured or ambiguous objects, the Medical Center may write a patch proposal,
risk notes, and a rollback plan. Applying it requires a separate repair round,
QA, and MAIN approval. This prevents “cleanup” from becoming an unreviewed
change.

## D6. No automatic SHA scanner or background fixer

Git already provides status, log, reflog, and worktree views. A permanent
scanner adds process, permissions, false positives, and a second source of truth.
The Medical Center is on-demand and scoped to named patients.

## D7. Sanitize before publishing, and keep provenance

Publication is an irreversible boundary. The public archive includes sanitized
process records and a provenance map, but not raw chat, screenshots, tokens,
device identifiers, or personal paths. Redaction is part of the artifact, not a
footnote.

## D8. Do not run benchmark tests without budget

Benchmark tests need paid model calls, time, and a stable environment. If the
budget is not available, the honest output is “not run”, with the reason and the
limits of what was actually verified. Do not turn unit/doc/render checks into a
benchmark claim.
