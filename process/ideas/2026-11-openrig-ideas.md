# OpenRig ideas — 2026-11

> Distilled from recent OpenRig work (documentation governance, rework loops,
> experience synthesis). Each entry states: the idea, where it came from, current
> state, the smallest next action, and the boundary or risk.
>
> States are used strictly: **implemented** / **prototype** / **to verify** /
> **dropped**. Nothing here is a roadmap promise.

## I01 — Absence-claim gate

- **Idea**: every "this file does not exist / is not installed / was not changed"
  claim must be accompanied by a negative command aimed at the same object.
- **Source**: a post-close review where a file was declared missing while only a
  foreign absolute path had been tested.
- **State**: prototype (`check-absence-claims.py`).
- **Next**: add `--self-test` with 2–3 negative cases and wire it into the
  pre-flight checklist of the next run.
- **Risk**: it only judges text shape. It cannot tell whether the command was run,
  nor whether its output supports the sentence.

## I02 — Long-term canonical count

- **Idea**: the canonical run count should be derived, not maintained by hand.
- **Source**: a documentation consistency check that failed because a hand-written
  count drifted every time a run directory was added.
- **State**: to verify.
- **Next**: either have the run-creation script rewrite the count line, or downgrade
  the check to a warning that points at the directory count.
- **Risk**: a derived number can also be wrong if the derivation ignores hidden
  directories; the definition must be written where the number is read.

## I03 — Where micro-workflows end and full workflows begin

- **Idea**: a micro-workflow is justified when the change is one file, one
  assertion, or one command; anything that crosses those boundaries goes back to a
  full workflow.
- **Source**: one single-round patch and one patch that needed a rework.
- **State**: implemented (used twice, once with a failed first review).
- **Next**: write the threshold into the workflow template as a checklist question.
- **Risk**: a hard threshold cuts work into pieces that share one evidence chain.

## I04 — Workflow monitor auto-mount

- **Idea**: starting a run should attach it to the read-only monitor automatically,
  so operators do not have to register runs by hand.
- **Source**: monitor mount confirmation work and its follow-up notes.
- **State**: partially implemented.
- **Next**: turn the mount confirmation into a re-runnable check with an exit code.
- **Risk**: it depends on local paths and a running service; a portable version
  needs a fallback that reports "unknown" instead of failing hard.

## I05 — Experience synthesis pipeline

- **Idea**: a finished practice can be sealed into a small knowledge tree
  (evidence lock → manifest) instead of a long narrative report.
- **Source**: an experience-synthesis round that emitted a sealed tree with a
  digest.
- **State**: implemented once.
- **Next**: extract the template and the minimal checks (manifest matches files,
  digests verify) so the next attempt starts from a skeleton.
- **Risk**: it easily becomes "one more report layer" if the tree is not actually
  read by the next run.

## I06 — Document fact sync and drift gate

- **Idea**: facts quoted in docs should be re-derived by a check, and disagreement
  should fail the check rather than wait for a reader.
- **Source**: a documentation fact-sync round hardened the drift check.
- **State**: implemented in one repository.
- **Next**: fold the drift check into the pre-flight four questions (does this
  number change after the next write? am I testing the subject or its stand-in?).
- **Risk**: the checker itself ages; it needs its own baseline.

## I07 — Directions still worth keeping from the drafts

- **Idea**: a small number of draft directions remain worth pursuing even though
  the broader draft set is frozen.
- **Source**: draft asset index and development status notes (kept private).
- **State**: to verify — each direction needs its own maturity label before being
  quoted publicly.
- **Next**: pick 3–7 directions, label each `concept / prototype / dropped`, and
  keep them clearly separate from the stable kit.
- **Risk**: drafts and the stable kit share vocabulary; publishing draft text
  verbatim makes readers treat proposals as behavior.

## Cross-cutting note

All seven share one failure shape: **they fail silently**. A drifting number, an
unverified absence, a table broken by a pipe, an empty command output — none of
them raise an error. That is why each idea is paired with a mechanical check
rather than a guideline.
