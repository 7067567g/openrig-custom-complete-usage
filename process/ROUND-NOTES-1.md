# Round notes 1 — inventory coverage and gaps

- Workflow instance: `01M7AZ6KH7K6T6929M8M8T55NP` (step `s1_inventory`, builder)
- Date: 2026-11-14
- Scope: read-only review of `process/` in this public repo; only this note was written
- Out of scope: source edits, commits, pushes, and any change to the private source workspace

## 0. Summary

The archive is readable and largely coherent. All **56** payload files named in
`INVENTORY.json` and `PROVENANCE.md` are present, their sizes agree except one
1-byte difference, all JSON and YAML files parse, and no relative Markdown link
in `process/` is broken. The four public gates pass, and `BENCHMARK-STATUS.md`
states **NOT RUN** with a matching disclosure in the root READMEs and
`VALIDATION*`.

The material blockers for publication QA are not missing bytes; they are claim
accuracy and traceability:

1. `PROVENANCE.md` says project names, host names, device IDs, and user
   identifiers were replaced with generic placeholders, but internal codenames
   and rig targets remain throughout the archive.
2. `reports/openrig-local-share-report.md` contains a literal device/host-model
   string inside its own sanitization grep pattern (masked in this note), which
   directly conflicts with its own "host name: 0" row.
3. The inventory/provenance map covers only 56 copied payload files; the 7
   top-level narrative/control files (README, STORY, DECISIONS, PITFALLS,
   BENCHMARK-STATUS, PROVENANCE, INVENTORY) are outside the map, so `fileCount:
   56` is not the file count of `process/` (63 before this note, 64 with it).
4. The archive is a snapshot with many unresolved companion references: a raw
   scan found 99 of 109 distinct repo-relative path references that do not exist
   in this repository (some are illustrative command examples, many are evidence
   and ledger paths).
5. Two published registries disagree on how many SOLO rounds are indexed, and
   one Markdown table is broken by a blank line.

None of these is a benchmark claim. No performance or cost claim was found in
`process/`.

## 1. What was published

`process/` contained 63 files and 636,989 bytes before this note was added. Of
those, 56 files / 610,419 bytes are the copied payload listed in
`INVENTORY.json`; the remaining 7 files / 26,569 bytes are the top-level reading
and control documents. With this note, `process/` is 64 files; the note itself is
not part of the inventory reviewed below. The figures below describe the archive
as reviewed, not the post-note directory.

| Layer | Files | Bytes | Notes |
|---|---:|---:|---|
| `governance/` | 9 | 97,989 | 8 protocols + 1 proposal |
| `registries/` | 9 | 90,139 | human + machine registries and evaluations |
| `rounds/` | 27 | 180,744 | briefs, workflow specs, reports, stamps |
| `traces/` | 4 | 11,585 | fast-response round 3/4 trace + run log |
| `case-studies/` | 3 | 107,677 | g3d final/acceptance, fast-response final |
| `reports/` | 4 | 122,286 | share report, upstream eval, two analyses |
| Top-level docs | 7 | 26,569 | reading path, story, decisions, pitfalls, benchmark status, provenance, inventory |
| **Total** | **63** | **636,989** | |

Source kinds in the inventory: `bridge-repo` 26, `discussion-archive` 26,
`workspace-root` 4. Redaction flags: 36 `yes`, 20 `no`.

Narrative coverage is good: `STORY.md` explains the evolution, `DECISIONS.md`
records eight decisions with rationale, and `PITFALLS.md` gives ten concrete
symptom/fix pairs. `README.md` supplies a ten-step reading order.

## 2. Category coverage

`INVENTORY.json` uses 16 categories:

| Category | Files | Bytes |
|---|---:|---:|
| round-report | 8 | 138,904 |
| case-study | 3 | 107,677 |
| governance-protocol | 8 | 85,878 |
| analysis-report | 2 | 71,286 |
| registry-machine | 2 | 47,455 |
| evaluation-report | 1 | 30,533 |
| registry | 3 | 22,358 |
| share-report | 1 | 20,466 |
| workflow-spec | 7 | 20,216 |
| round-brief | 8 | 18,145 |
| evaluation | 3 | 16,336 |
| governance-proposal | 1 | 12,111 |
| workflow-trace | 2 | 9,580 |
| evaluation-machine | 1 | 3,990 |
| stamp | 4 | 3,479 |
| run-log | 2 | 2,005 |

This covers the four governance dimensions named in `STORY.md` (Command Center,
General Staff, SOLO, Medical Center), plus round execution, traces, case studies,
and analyses. The archive is strongest on governance prose and round reports;
it is thinnest on executable/reproducible artifacts (see gaps G4 and G5).

## 3. Round coverage matrix

Twelve round directories are present. Coverage is asymmetric:

| Round directory | Brief | Workflow | Report | Stamp |
|---|:---:|:---:|:---:|:---:|
| `command-center-20261114` | yes | yes | — | 2 |
| `general-staff-20261114` | yes | yes | — | 2 |
| `solo-stamp-20261114` | yes | yes | — | — |
| `thinking-dimensions-20261114` | yes | yes | — | — |
| `stop-sweep-20261114` | yes | yes | yes | — |
| `insert-guard-20261114` | yes | yes | yes | — |
| `sync-guard-20261114` | yes | yes | yes | — |
| `quiet-200-20261114` | yes | — | `followup.md` | — |
| `issue-intake-20261113` | — | — | yes | — |
| `monitor-console-20261113` | — | — | yes | — |
| `repo-audit-20261114` | — | — | yes | — |
| `solo-management-20261114` | — | — | yes | — |

Totals: 8 briefs, 7 workflow specs, 8 reports (counting the quiet-200 follow-up),
4 stamp files.

## 4. Obvious gaps

**G1. Stamps are under-represented.** `registries/standalone-rounds.md` records
14 confirmed + 1 candidate SOLO rounds and a stamp summary of `OK 13 / MIRROR 2`;
`registries/thinking-rounds.md` records 15 indexed rounds with in-place staff
stamps. But `process/` contains only 4 stamp files for 2 rounds (command-center
and general-staff). A reader cannot verify the stamp protocol against the
registry from this archive alone.

**G2. Two registries disagree on index size.** `registries/standalone-rounds.md:26`
says `staffIndexed | 13（SOLO-09/10 meta 未入 13 条索引）`, while
`registries/thinking-rounds.md:16` says `入索引 | 15` and the same file lists
15 entries. Both are published as current. This is either a snapshot-time skew
or a genuine drift; it needs one authoritative version or an explicit note.

**G3. A broken Markdown table.** `registries/thinking-rounds.md` has a blank
line between the `THINK-13` row (line 39) and the `THINK-14`/`THINK-15` rows
(lines 41–42). The last two rows fall outside the table when rendered. The doc
consistency gate does not detect this.

**G4. Executable companion artifacts are absent.** The protocols reference
`tools/round-command-center.mjs` (29 mentions) and `tools/solo-round-stamp.mjs`
(17 mentions), but no `tools/` tree is shipped. A public reader gets the rules
but cannot run them. If the tools are intentionally private, the protocol should
say so.

**G5. Templates and machine ledgers are absent.** Registries reference
`STANDALONE-ROUND-TEMPLATE.md/.json`, `ROUND-EVALUATION-TEMPLATE.json`,
`CLOSEOUT-LEDGER-TEMPLATE.json`, and `INSERTION-LEDGER-TEMPLATE.json`; none are
in the archive. The machine-readable registries that are shipped (`round-registry.json`,
`standalone-rounds.json`, `talent-ledger.json`) are therefore not a complete
machine layer.

**G6. Traces cover one workflow only.** All four trace/run-log files belong to
fast-response rounds 3 and 4. No trace exists for the governance rounds, the
SOLO rounds, or the earlier fast-response rounds. This is a sampling choice, but
`README.md` should say the traces are examples, not a complete execution record.

**G7. Case-study pairs are incomplete.** g3d has final + acceptance; fast-response
has final but no acceptance. Either add the acceptance record or note that it was
not part of the sanitized set.

**G8. Discoverability of `reports/` and `traces/`.** `README.md:14-23` gives a
reading order that stops at case studies and provenance; `reports/` (four files,
122 KB, including the share and upstream reports) and the trace-as-example
caveat are not in it. `process/README.md` also does not state that many internal
paths are intentionally unresolved.

**G9. Publication state is uncommitted.** `process/` is untracked, and the root
README/INDEX/VALIDATION edits are unstaged (`git status`). Nothing has been
committed or pushed. This is expected for this step, but the archive should not
be called "published" until the Lead commits it.

## 5. Provenance mismatches

**P1. Payload size drift (minor).** `INVENTORY.json` and `PROVENANCE.md` list
`reports/workflow-review.md` as 15,594 bytes; the file is 15,595 bytes. Every
other listed size matches exactly. Likely a trailing-newline difference during
copy; regenerate the inventory or restore the byte count.

**P2. Inventory scope is ambiguous.** `INVENTORY.json` says `fileCount: 56` and
`bytes: 610419`, which matches the 56 copied payload files exactly. It does not
account for the 7 top-level docs, so the numbers do not describe `process/` as a
directory. `PROVENANCE.md` likewise has 56 rows and ends with "Missing sources:
None." Either add an explicit `authored`/`control` section for the 7 files, or
state in both files that the count covers copied sources only.

**P3. The redaction claim is broader than the artifact.** `PROVENANCE.md:67`
says project names, host names, device IDs, and user identifiers were replaced
with generic placeholders. In practice the archive retains:

- rig targets in `rounds/*/workflow.yaml` (`target.rig`, `preferred_targets`),
  e.g. the target rig repeated across 10 files;
- internal round/branch identifiers used as registry IDs and directory names
  throughout `registries/` and `rounds/`;
- product/rig codenames in the two case studies and in `reports/`;
- project labels in `registries/standalone-rounds.md` and its JSON copy.

Whether these names are public-safe is a Lead/QA decision; this pass only
establishes that the blanket "project names -> generic placeholders" statement
is not literally true of the shipped bytes.

**P4. A literal device/host string survives in a sanitization command.**
`reports/openrig-local-share-report.md` lines 191, 283, and 289 embed a literal
device/host-model string inside a `grep -rInE` pattern (masked here as
`<HOST-LITERAL>`; not reproduced in this note). The report's own table at line 96
claims the host name had 0 occurrences before and after. Even if the string is a
machine model rather than the hostname, it is the same identifier class the
provenance map says was genericized. This is the highest-priority item for QA.

**P5. Redaction flags are not observable for 12 files.** Twelve files marked
`redacted: true` contain none of the documented placeholders
(`<WORKSPACE>`, `<BRIDGE_REPO>`, `<OPENRIG_SRC>`, `<REDACTED_TOKEN>`,
`<REDACTED>`). That can be legitimate (redaction by deletion or paraphrase), but
the artifact gives no evidence of what changed. Either add a per-file redaction
note or narrow the meaning of the flag.

**P6. Documented placeholder classes are incomplete.** `PROVENANCE.md:66-69`
lists four redaction classes, three of which name placeholder families, but the
archive also uses `<HOME>`,
`<DSH_HOME>`, `<USER>`, `<HOST>`, `<IP>`, `<ID>`, `<BRANCH>`, `<ISO>`,
`<SCOPE>`, `<CODE>`, `<DEVICE>`, and others. Most are generic documentation
metavariables, but the provenance map should distinguish "sanitization
placeholders" from "protocol metavariables" so a reader does not over-read them.

**P7. Traceability stops at source kind.** `PROVENANCE.md` records category,
source kind, bytes, and redaction, but not the source path or source commit. A
reader cannot trace a public file to a specific private artifact; "traceable
snapshot" currently means "categorized snapshot". If traceability is a
publication promise, add a source-path or commit column (even if access is
private).

## 6. Gate evidence

Run from the public repo root on 2026-11-14:

```text
$ python3 scripts/check_repo.py
{"verdict": "PASS", "errors": []}

$ python3 scripts/check_content.py
{"verdict": "PASS", "pairs": 23, "examples": 11, "errors": []}

$ python3 scripts/check_sanitization.py
{"verdict": "PASS", "errors": []}

$ python3 scripts/doc_consistency.py --check
doc_consistency: 0 error(s), 0 warning(s)
```

Additional read-only checks:

- Inventory reconciliation: 56 listed / 56 actual payload files; 0 missing,
  0 extra, 1 size mismatch (`workflow-review.md`, +1 byte).
- JSON and YAML parse: all files parse.
- Relative Markdown links inside `process/`: 0 broken.
- Absolute home paths, email addresses, IPv4 literals, and phone-number shapes:
  no matches in `process/` (manual scan in addition to the gate).
- Benchmark disclosure: `process/BENCHMARK-STATUS.md` says NOT RUN; no
  performance/cost claim found in `process/`; root `README.md`,
  `README.zh-CN.md`, `VALIDATION.md`, and `VALIDATION.zh-CN.md` all link to it.
- `make test` with the host `python3` fails during collection because `openpyxl`
  is not installed (pre-existing environment issue, unrelated to `process/`).
  With the existing `/tmp/ocu-venv2` interpreter (openpyxl 3.1.5), the full
  suite passes: 154 passed, 1 skipped.
- `python3 scripts/openrig_smoke.py --rounds 3`: 3/3 passed. This command
  rewrites `reports/openrig_smoke.json`; that file was restored with
  `git checkout --` immediately afterwards, so no source file is left modified.

Gate limitation: `check_sanitization.py` matches a fixed pattern list
(home paths, common token shapes, private keys, inline API-key assignments). It
does not detect project codenames, rig names, device model strings, or
placeholder-class drift. A PASS therefore does not clear P3–P6.

## 7. Recommendations for s2_publication_qa

Priority order, without prescribing implementation:

1. Decide P4 first: either remove the literal host/device string from the three
   grep lines or establish that it is safe to publish. Do not copy it into QA
   notes.
2. Decide P3: either genericize the remaining codenames/rig targets, or narrow
   the provenance claim to what is actually true (for example, "personal paths
   and credentials were removed; project codenames are retained for realism").
3. Fix the inventory scope (P2) and the 1-byte drift (P1) in one regeneration.
4. Resolve the 13-vs-15 registry conflict (G2) and the broken table (G3).
5. Add a short "companion artifacts are not shipped" note (G4/G5) and a
   "traces are examples" note (G6) to `process/README.md`.
6. Add `reports/` to the reading order and state that unresolved internal paths
   are intentional (G8).
7. Re-run all gates after edits and record exact outputs; then hand off to the
   QA step.

## 8. Boundaries and limitations

- No source file is left modified; the only addition is this note. The smoke
  command rewrote `reports/openrig_smoke.json`, and that file was restored to
  HEAD with `git checkout --`. `process/` remains untracked; nothing was
  committed or pushed.
- The review is a static inspection. It does not prove that the private sources
  matched these copies at copy time, because the archive has no source-path or
  commit mapping (P7).
- "Obvious gaps" are judged against the archive's own README and the
  publication brief, not against an external completeness standard.
