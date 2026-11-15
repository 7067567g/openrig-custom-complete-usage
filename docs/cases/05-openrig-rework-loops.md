**English** | [简体中文](05-openrig-rework-loops.zh-CN.md)

# Case 05 — Rework loops and micro-workflows

## Question

A workflow has been closed and accepted. Then someone finds a defect that lives in
one file and one sentence. Do you reopen the whole workflow, or something smaller?
And what does the rework itself teach about review?

## Background

Two post-close defects on the same map:

- a row that described a superseded edit scope;
- a "difference is N lines" claim that kept drifting as the document grew.

Both were real product defects: the map is what the next agent reads.

## Method

Two dedicated micro-workflows, each with one execution step and one review step:

```text
patch_x09  (edit) → qa_x09  (read-only verify)     → done in one round
patch_x01  (edit) → qa_x01  (read-only verify)     → FAIL → patch_x01 again → PASS
```

Each micro-workflow:

- is authorised to touch **one or two files**, listed by path;
- must not create a new run directory (that would shift the canonical run count
  and invalidate an unrelated check);
- writes a patch record with before/after text, commands, exit codes, and a file
  list;
- ends in an independent read-only review.

## Result

**x09 (one round).** The row was rewritten to the current scope and the wording
changed from an absence claim to an ownership statement. Review passed first try.

**x01 (one fail, one rework).** Numbers were correct, form was not:

```text
first attempt : "R1 measured 3 lines; after the redirect line it is 5"
review verdict: FAIL — bare number, no timestamp, no "command is authoritative"
rework        : X01 becomes attribution only (no number, points at the §7 command)
                each §7 comment becomes two lines:
                  # difference (measured 5 lines at 2026-11-15T12:34:44Z)
                  # this changes with the files; the command output wins
review verdict: PASS
```

## What it proves

- **Micro-workflows fit closing work.** One file, one assertion, one command, one
  reviewer. They keep the evidence chain intact without reopening a closed run.
- **A failed review must return to the same executor.** The rework happened in the
  original step with the original authority; nothing was "fixed by the reviewer".
- **Numbers belong next to commands.** The rework did not change the value; it
  changed where the value is allowed to live.
- **Do not create a run directory for a patch.** A new directory silently changes a
  count that other documents assert.

## Reusable rules

1. One micro-workflow = one bounded change + one independent read-only review.
2. The review list is written as *executable corrections*, not opinions; the
   executor follows it item by item.
3. When a number must appear, it appears as `timestamp + value + "command output
   wins"`; otherwise the document states the relation qualitatively and points at
   the command.
4. Every patch record lists the files it touched **and the files it did not**; the
   "not touched" list must stay true after any later authorisation change.
