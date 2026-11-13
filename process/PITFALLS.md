# Pitfalls and lessons

## P1. “Round” and “step” get mixed up

Symptom: someone says “12 rounds” but means 12 workflow steps, or claims a round
closed because a packet closed.

Fix: name the unit explicitly. Round = workflow-group cycle. Step = OpenRig
workflow packet. Packet closure is not acceptance.

## P2. Validation green is mistaken for end-to-end success

Symptom: `workflow validate` or `rig up --plan` passes, so the work is called
done.

Fix: validation proves the spec; it does not prove a model executed, a file was
written, or a reviewer accepted it.

## P3. A seat closes the packet without writing the report

Symptom: workflow shows completed, but the expected artifact is missing or
empty.

Fix: make the deliverable path explicit in the step objective, check it in QA,
and use closure evidence where available.

## P4. Agent startup mutates the workspace

Symptom: `AGENTS.md` changes, `.agents/` appears, or untracked files show up
after a seat starts.

Fix: restore managed files, remove generated scaffolding, and add it to
`.gitignore` when appropriate. Treat startup side effects as part of the launch
contract.

## P5. Memory estimates based on RSS are wrong

Symptom: the host OOMs while the visible process looks small.

Fix: use cgroup limits and watch page cache. `MemoryHigh`, `MemoryMax`, and
`MemorySwapMax` have different semantics; they are not additive. Avoid broad
filesystem scans from agent seats.

## P6. Work starts on a dirty or ambiguous baseline

Symptom: two workers produce incompatible patches, or the branch point is not
auditable.

Fix: freeze and record the baseline first. Split curated pathspecs; never use a
blind `git add -A` as a baseline strategy.

## P7. Documentation drift grows faster than code drift

Symptom: the branch ledger, branch doc, registry, and actual `HEAD` disagree.

Fix: name one source of truth per field, update all mirrors in the same round,
and run a consistency check before claiming a clean state.

## P8. Sanitization is left until publication

Symptom: a public push contains a home path, a host name, a device ID, or a
project name that should not be there.

Fix: sanitize on a copy, scan the final tree with multiple patterns, and keep a
provenance map. A publish gate should fail closed.

## P9. Too many questions, then none

Symptom: the agent asks one question per turn, or asks nothing and silently
invents scope.

Fix: one consolidated clarification batch before an automated run. After start,
record assumptions and write a blocker for genuinely unauthorized actions.

## P10. Overbuilding the process

Symptom: a small cleanup task grows a daemon, a scanner, and three new
registries.

Fix: start with the smallest mechanism that preserves evidence and review. Add a
layer only when a real repeated failure demands it.
