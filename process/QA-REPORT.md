# QA report — final verdict (`s3_independent_qa` + `s5_final_qa`)

- Workflow instance: `01M7AZ6KH7K6T6929M8M8T55NP`
- Steps: `s3_independent_qa` (initial review, NEED_MAIN) and `s5_final_qa`
  (post-fix re-verification, PASS)
- Date: 2026-11-14
- Reviewer: `work-qa@openrig-publish-20261114`
- Scope: `process/` in the public repo only; no private source workspace was
  read or modified; no commit, tag, or push.

## 0. Final verdict

**PASS — the archive is publication-safe.**

| Area | Result |
|---|---|
| Sanitization (author paths, credentials, private keys) | **PASS** |
| Benchmark note explicit, no result claimed | **PASS** |
| Four required gates (post-fix) | **PASS** |
| Inventory/provenance reconciliation (56-file payload) | **PASS** — 0 mismatches |
| Broken relative links | **PASS** — 0 |
| Content defects from `s3_independent_qa` | **FIXED** — 4/4 verified |
| Publication-safety blockers | **NONE** |

The initial review returned NEED_MAIN with four bounded content items. The
`s4_fix` builder fixed all four (plus one adjacent wording inconsistency). This
report records the post-fix evidence and the final verdict.

## 1. What changed between the two QA passes

`s4_fix` changed five files under `process/`:

- `registries/thinking-rounds.md` — 4,606 → 4,784 bytes (table repair)
- `registries/standalone-rounds.md` — 13,517 → 13,703 bytes (snapshot note)
- `README.md` — reading order, unresolved-path note, payload-scope note,
  sanitization-boundary wording
- `INVENTORY.json` — two entry sizes + total 610,399 → **610,763**
- `PROVENANCE.md` — the same two rows updated

No other payload file changed. `ROUND-NOTES-1.md` and `ROUND-NOTES-2.md` remain
untouched point-in-time records.

## 2. Required gates (re-run after fixes)

From the public repo root:

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

## 3. Independent verification of the four fixes

**F1 — broken table repaired.** `registries/thinking-rounds.md` now has one
contiguous table. Programmatic count between the header and the first blank
line: **15** `THINK-20261114-*` rows (`THINK-01` … `THINK-15`), with the
`THINK-14/15` note moved below the table.

**F2 — registry drift reconciled.** Both registries now cross-reference each
other and label their snapshots:

- `registries/standalone-rounds.md:30` — says it is the earlier `v1.0.9`
  snapshot (`staffIndexed 13`, `SOLO-09/10` meta rounds not yet indexed) and
  points to `thinking-rounds.md` (15).
- `registries/thinking-rounds.md:23` — says it is the later index (15, includes
  `SOLO-09/10` meta rounds) and points back to the `v1.0.9` ledger (13).

The two counts are no longer presented as competing current values.

**F3 — reading order completed.** `process/README.md` now lists 11 steps
including `reports/` (share, upstream-evaluation, and analysis reports), and a
new paragraph states that internal `docs/...`, `reports/...`, and `tools/...`
paths refer to the private source workspace and are intentionally unresolved.

**F4 — unshipped companions disclosed.** The same paragraph names
`tools/*.mjs` and the round/evaluation templates as not shipped, and states
that `INVENTORY.json` counts the copied payload only.

**Adjacent consistency fix (not required, but correct).** `README.md`'s
sanitization boundary now says project/case codenames are retained as
non-personal labels, matching `PROVENANCE.md` instead of claiming all project
names were replaced.

## 4. Inventory and provenance reconciliation

```text
INVENTORY.json: fileCount=56, bytes=610763, missing=[]
listed total 610763 == declared 610763
size mismatches: 0
PROVENANCE rows=56, sum=610763, mismatches 0
```

`process/` now holds **67** files: the 56-file copied payload plus 11 top-level
authored/publication documents (`README.md`, `STORY.md`, `DECISIONS.md`,
`PITFALLS.md`, `BENCHMARK-STATUS.md`, `PROVENANCE.md`, `INVENTORY.json`,
`ROUND-NOTES-1.md`, `ROUND-NOTES-2.md`, `ROUND-NOTES-4.md`, `QA-REPORT.md`).
`README.md` now states that `INVENTORY.json` covers the payload only, so
"56/56 reconciled" is no longer ambiguous.

## 5. Independent residual scan (post-fix)

| Check | Result |
|---|---|
| Author / macOS home paths | 0 files |
| Email addresses | 0 |
| IPv4 literals | 0 |
| Token-shaped strings / key headers | 1 file: `ROUND-NOTES-2.md` — the scan command's own regex text, not a token |
| Private-key material | 0 |
| Binary / screenshot artefacts | 0 |
| Broken relative links | 0 |
| JSON / YAML parse | all parse |

The single token-pattern hit is a false positive: it is the literal regex used
inside `ROUND-NOTES-2.md`'s scan table, not an actual credential. No real
secret, path, or personal identifier was found.

## 6. Benchmark note review (re-confirmed)

`process/BENCHMARK-STATUS.md` remains explicit:

- Status is **NOT RUN**.
- The reason (paid calls, stable environment, time budget unavailable) is stated.
- Token/cost, latency/throughput, and model-quality claims are disclaimed.
- Unit/doc/render/smoke checks are labelled validation evidence, **not** a
  benchmark.
- A revisit condition is defined.

A grep for `benchmark` across `process/` returns only the NOT RUN disclosure,
narrative references, and the decision not to run without budget. No
performance, cost, throughput, "faster than", or model-quality result is
claimed. **PASS.**

## 7. Recorded, accepted without further change

These are acknowledged characteristics of a sampled, sanitized snapshot, not
blockers:

- **Case-study pair asymmetry.** `case-studies/fast-response-final.md` has no
  acceptance record, while `g3d-usage-sim` ships both final and acceptance.
  Acceptable as sampling; readers should not assume every case has a pair.
- **Redaction observability.** `INVENTORY.json` marks 36 files `redacted: true`.
  Of these, 8 contain no upper-case `<PLACEHOLDER>` token and 5 contain no
  redaction marker at all; redaction-by-deletion is plausible but not
  per-file-verifiable. (This also means `ROUND-NOTES-2.md` §5.7's "12 files"
  should be treated as approximate.)
- **Per-file traceability.** The inventory records category and source kind but
  no per-file source path or commit. The archive is categorized, not
  individually traceable — already stated in `ROUND-NOTES-2.md` §7.
- **Trace sampling.** `traces/` covers only fast-response rounds 3 and 4;
  `README.md` calls them examples, which is adequate disclosure.
- **Uncommitted state.** `process/` is untracked; nothing is committed or
  pushed. This is the Lead's publish step and matches the brief's boundary.

## 8. Boundary compliance

- Reviewed `process/` only; did not read or modify the private source workspace.
- QA wrote/updated only `process/QA-REPORT.md`.
- `s4_fix` changed only the five files listed in section 1.
- No commit, tag, or push was made.
- The four gates and the link scan were re-run after this report was written;
  all pass.

## 9. Final verdict

**PASS.** The sanitized process archive is publication-safe: sanitization is
clean, the benchmark note is explicit with no result claimed, the four gates
pass, inventory/provenance reconcile exactly, links are intact, and the four
QA content defects are fixed and independently verified. The accepted items in
section 7 are snapshot characteristics, not blockers.
