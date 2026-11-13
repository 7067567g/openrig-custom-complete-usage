# How this OpenRig practice evolved

## Starting point: one bounded workflow at a time

The first useful pattern was deliberately small: declare one workflow, give it a
clear objective, let one seat produce one artifact, then inspect the queue,
trace, and output. This kept the failure surface visible. A green
`workflow validate` was treated as a spec check, not as proof that the work ran.

## From one workflow to governed rounds

As work grew beyond a single packet, three governance dimensions appeared:

1. **Round/conflict governance** — what is running, on which branch/worktree, and
   what may collide. This became the Command Center registry.
2. **Thinking/evaluation governance** — which analyses were worth reusing, how
   they scored, and which dimensions were missed. This became the General Staff
   index and consultation gate.
3. **One-off governed work** — tasks that were neither a formal round nor a
   long-running branch. This became the standalone round (SOLO) plus its stamp.

A fourth dimension appeared later: **injured objects**. Corrupt data, orphan
worktrees, half-finished workflows, and wrong conclusions needed triage,
isolation, evidence, a propose-only patch, and root-cause analysis. That became
the Medical Center plan. It was deliberately kept as a plan first; no automatic
scanner, no daemon, and no auto-apply.

## The stable shape

- Long-running work -> Command Center registry.
- One-off governed work -> SOLO round with ID, anchor, branch, rejoin, QA,
  evidence, and closeout.
- Thinking work -> General Staff consultation before analysis.
- Stop/cleanup -> CLOSEOUT manual and STOP-SWEEP.
- Mid-run insertion -> INSERT-GUARD, not a silent scope change.
- Injured object -> Medical Center triage, not a heroic patch.

The important part was not the number of layers. It was keeping each layer's
job narrow and making the handoff between layers explicit.

## What changed in practice

- Questions moved to a single clarification batch before an automated run; after
  that, ambiguity became a written assumption or a blocker.
- Packet closure stopped being treated as acceptance. A closed packet can still
  lack a report, a test, or a QA verdict.
- Evidence moved closer to the claim: commands, hashes, file paths, and
  independent review, not memory or chat summaries.
- Long-running work got a registry entry before it got more work.
- Sanitization became part of publication, not a last-minute grep.
