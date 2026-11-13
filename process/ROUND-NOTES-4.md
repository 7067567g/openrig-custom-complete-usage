# Round notes 4 — fixes after independent QA

- Workflow instance: `01M7AZ6KH7K6T6929M8M8T55NP` (step `s4_fix`, builder)
- Date: 2026-11-14
- Input: `process/QA-REPORT.md`, verdict **NEED_MAIN**, four bounded content fixes
- Scope: only the four section-5 items; no private source workspace, no push

## 0. Summary

All four QA-listed defects are fixed. The payload is still fully reconciled
(56 files, 0 size mismatches); the byte total moved from 610,399 to **610,763**
because two registry files grew. The four public gates still pass, links are
still 0 broken, and the thinking-rounds table now renders all 15 rows.

A fifth, adjacent inconsistency was corrected inside the same README edit:
`process/README.md` still said project names were removed, while `PROVENANCE.md`
(round 2) now says codenames are retained. The README sanitization boundary now
matches the provenance map. This is a wording consistency fix, not a new
redaction.

## 1. Before / after

| # | QA item | Before | After |
|---|---|---|---|
| 1 | Broken table | `registries/thinking-rounds.md` had a blank line between `THINK-13` and `THINK-14`; only 13 of 15 rows rendered as a table | Blank line removed; 15 contiguous rows; the `THINK-14/15` note moved below the table |
| 2 | 13-vs-15 drift | `standalone-rounds.md` said `staffIndexed 13`; `thinking-rounds.md` said 15; no explanation | Both files now carry a `口径` note: standalone is the earlier `v1.0.9` snapshot (13); thinking is the later index (15, includes `SOLO-09/10` meta rounds) |
| 3 | Reading order | `process/README.md` listed 10 steps and omitted `reports/`; no unresolved-path note | 11 steps, including `reports/`; new paragraph says internal `docs/...`/`reports/...`/`tools/...` paths are intentionally unresolved and `fileCount` covers payload only |
| 4 | Unshipped companions | No disclosure that `tools/*.mjs` and templates/ledgers are absent | Same paragraph names `tools/*.mjs` and the round/evaluation templates as not shipped |

Exact files changed:

- `process/registries/thinking-rounds.md` — 4,606 -> 4,784 bytes
- `process/registries/standalone-rounds.md` — 13,517 -> 13,703 bytes
- `process/README.md` — top-level document, not in the payload inventory
- `process/INVENTORY.json` — two entry sizes + total 610,399 -> 610,763
- `process/PROVENANCE.md` — the same two rows updated

No other payload file changed. `process/ROUND-NOTES-1.md` and
`process/ROUND-NOTES-2.md` remain as point-in-time records.

## 2. Post-fix verification

Inventory reconciliation:

```text
missing []
size_mismatches []
declared 610763, sum_listed 610763, actual_payload 610763
```

Table check:

```text
THINK rows: 15
```

Gates, run after all edits:

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

Additional checks:

- Relative links across `process/**/*.md`: 0 broken.
- JSON/YAML parse: all files parse.
- Residual patterns: no absolute home paths, email addresses, IPv4 literals,
  token shapes, private-key material, binaries, or the previously removed
  device/host literal.
- `reports/openrig_smoke.json` was already restored to HEAD in round 2 and is
  still clean.

## 3. Recorded, not changed

These are QA section-6 items and remain true; each is now either disclosed or
acceptable as sampling:

- Case-study pair asymmetry: fast-response has a final report but no acceptance
  record.
- Redaction observability: QA's independent marker count differs from round 2's
  "12 files" because the two passes used different definitions of a redaction
  marker. The safety verdict does not depend on the exact count; the limitation
  remains recorded.
- Per-file traceability: the inventory still records category/source kind, not
  source path or commit.
- Trace sampling: `traces/` covers only fast-response rounds 3/4; README already
  calls them examples.
- Uncommitted state: `process/` is untracked; commit/push is the Lead's step.

## 4. Boundary compliance

- Only `process/` was modified.
- The private source workspace was not read or modified during this step.
- No commit, tag, or push was made.
- Fixes were limited to the four QA items plus the README/provenance wording
  alignment described in section 0.

## 5. Handoff

Ready for `s5_final_qa`: re-run the gates, confirm the four fixes, and update
`process/QA-REPORT.md` with the final verdict.
