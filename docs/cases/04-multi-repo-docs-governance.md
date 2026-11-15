**English** | [简体中文](04-multi-repo-docs-governance.zh-CN.md)

# Case 04 — Documentation governance across three repositories

## Question

When the same product has three documentation surfaces — a control plane, a
source repository, and a sanitized usage repository — how do you stop agents from
reading the wrong one, and how do you keep the map itself from going stale?

## Background

The three surfaces answered different questions but shared vocabulary:

- **control plane** — goals, decisions, acceptance, run evidence;
- **source repository** — code structure, shipped reference docs, release notes;
- **usage repository** — sanitized examples, operational guides, process archive.

Agents kept landing on the wrong surface: a package-level `README` instead of the
project entry, a historical run instead of the current spec, an example repository
instead of source truth.

## Method

Three rounds, each ending in an independent review:

1. **Inventory (read-only).** Snapshot every candidate entry point: path, size,
   hash, git state, and a judgement (`canonical / stale / duplicate /
   wrong-location`). Copy the before-content of every file that may be edited, so
   later diffs can prove "only a pointer line was added".
2. **Build the maps.** One cross-repo map in the control plane, plus one local map
   in each repository. Each map states: which surface answers what, "I want to do
   X → read this", and "correct location vs common wrong entry".
3. **Correct the entries.** Add one minimal pointer line per entry document,
   redirect at least three known wrong entries, and run each repository's native
   doc checks.

Acceptance was mechanical, not narrative:

```text
14/14 entry documents carry both a local-map and a cross-repo pointer
three maps mutually reachable; relative links resolved: 0 broken
pointer/redirect diffs are append-only: 0 deleted lines
repo-native doc checks: same pass/fail set as the pre-recorded baseline
```

## Result

- Three maps, 16 task routes, 10 wrong-location classes.
- 14/14 entries pointing at both their local map and the cross-repo map.
- 3 explicit redirects (package README, historical runs, usage-as-source).
- Link check: every added link resolved; zero broken.

## What went wrong after closing (the useful part)

Two defects were found only after the workflow had been closed and reviewed:

1. **Stale scope in a shipped map.** One row still described an earlier, smaller
   edit scope that had since been superseded. The map is what the next agent
   reads, so a stale row there is worse than a stale line in a report.
2. **A bare number.** A "difference is 3 lines" claim was true when written, then
   became 4 and then 5 as the document gained lines. Nobody could tell when it
   stopped being true.

Both were fixed by small dedicated workflows (see Case 05), not by reopening the
main one.

## Reusable rules

- **Numbers carry their command and their moment.** A figure in prose must sit
  next to the command that reproduces it and the time it was taken; otherwise
  prefer a qualitative statement. A number that cannot change a reader's decision
  should be deleted.
- **Absence claims need negative verification.** "This file does not exist" is
  only proven by a command aimed at *that* object, not at a similar-looking path.
- **Verification must be written after the last product write.** A record written
  before the final edit describes a state that no longer exists.
- **A pointer that needs a disclaimer is not fixed.** Move the content out of the
  fragile container instead of annotating it.
- **Make judgements mechanical.** "No cell has an odd number of backticks" catches
  a table-breaking pipe better than eyeballing rendered output.

## What it proves

Documentation governance is mostly *evidence discipline*: the maps are the easy
part, and the cost lives in proving that each claim is still true at the moment
someone reads it.
