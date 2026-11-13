# Round notes 2 — sanitization and publication-gate evidence

- Workflow instance: `01M7AZ6KH7K6T6929M8M8T55NP` (step `s2_publication_qa`, builder)
- Date: 2026-11-14
- Scope: gates, residual-pattern scan, and publication-safety fixes under `process/` only
- Input handling: no private source files were read or modified; no commit or push

## 0. Summary

All four public gates pass. The residual scan found **one** literal device/host
identifier left inside a sanitization command in
`reports/openrig-local-share-report.md`; it has been replaced with `<HOST>`.
It also found a 1-byte inventory drift, which is now corrected. The payload is
fully reconciled: **56/56 files, 0 size mismatches, 610,399 bytes**.

After the fixes, the archive contains no absolute home paths, email addresses,
IPv4 literals, token-shaped strings, private-key material, binaries, or the
previously identified device/host literal. Project and case codenames remain;
`PROVENANCE.md` now states that explicitly instead of claiming all project names
were replaced.

Remaining findings are content/render issues, not sanitization failures; they
are listed for `s3_independent_qa` in section 5.

## 1. Gate results

Run from the public repo root:

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

Supplementary: the full test suite passes with the existing `/tmp/ocu-venv2`
interpreter (`openpyxl 3.1.5`): `154 passed, 1 skipped`. With the host
`python3`, collection fails because `openpyxl` is not installed; that is a
pre-existing environment gap unrelated to `process/`.

## 2. Residual-pattern scan

Manual scans in addition to the gate (all from `process/`):

| Check | Command shape | Result |
|---|---|---|
| Absolute home/user paths | `grep -rIlE '/home/<user>/\|/Users/<user>/\|~/.<credential-dir>' .` | 0 files |
| Email addresses | `grep -rIlE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' .` | 0 files |
| IPv4 literals | `grep -rIlE '([0-9]{1,3}\.){3}[0-9]{1,3}' .` | 0 files |
| Token-shaped strings / keys | `grep -rIlE 'sk-[A-Za-z0-9]{20,}\|ghp_[A-Za-z0-9]{20,}\|AKIA[0-9A-Z]{16}\|-----BEGIN' .` | 0 files |
| Device/host literal | `grep -rIl '<HOST-LITERAL>' .` | 1 file before fix, 0 after |
| Private workspace markers | `grep -rIlE '<PRIVATE-WORKSPACE-MARKER>\|<AUTHOR-NAME>' .` | 0 files |
| Binaries/screenshots | file-extension census at scan time | 10 JSON, 47 Markdown, 7 YAML, 0 binaries |
| Broken relative links | link scan over `**/*.md` | 0 broken |
| Benchmark claims | `grep -rIn -i 'benchmark' .` | only the NOT RUN disclosure and narrative references |
| JSON/YAML parse | `json.load` / `yaml.safe_load` over all files | all parse |

The scan does not treat project/case codenames as leaks; see section 3, F2.

## 3. Fixes applied

**F1. Removed the literal device/host string.** In
`reports/openrig-local-share-report.md`, the literal appeared three times inside
`grep -rInE` self-check patterns (lines 191, 283, 289). Replaced each with
`<HOST>` (masked here as well; the literal is deliberately not reproduced in
this note).

- File bytes: 20,466 -> 20,445 (-21)
- `INVENTORY.json`: entry bytes 20466 -> 20445; top-level total 610419 -> 610399
- `PROVENANCE.md`: row bytes 20466 -> 20445

**F2. Narrowed the provenance claim.** `PROVENANCE.md` said "Project names, host
names, device IDs, and user identifiers -> generic placeholders." The archive
retains round IDs, rig targets, and case-study codenames, so that statement was
not literally true. It now reads:

> Personal paths, host names, device identifiers, and account/user identifiers
> -> generic placeholders; project/case codenames are retained as non-personal
> labels.

This is a documentation correction, not a new redaction. If the Lead decides
those codenames are not publishable, they must be genericized in a separate
scoped pass; this note does not claim they were removed.

**F3. Corrected the 1-byte inventory drift.** `reports/workflow-review.md` was
listed as 15,594 bytes but is 15,595 bytes. Updated the entry in
`INVENTORY.json` and `PROVENANCE.md`; top-level total 610398 -> 610399.

No other file was edited. `process/ROUND-NOTES-1.md` was left as the
point-in-time record; this note supersedes its P1 and P4 where they differ.

## 4. Post-fix verification

```text
listed 56, actual payload 56
missing []
size_mismatches []
sum_listed 610399, declared_total 610399, actual_payload_total 610399
json_yaml_parse OK
broken_links 0
absolute_home 0, email 0, ipv4 0, token_shapes 0, private_markers 0, binaries 0
```

Gate re-run after the fixes:

```text
check_repo.py         PASS
check_content.py      PASS (23 pairs, 11 examples)
check_sanitization.py PASS
doc_consistency.py    0 error(s), 0 warning(s)
```

`git status` shows only the expected untracked `process/` and the pre-existing
unstaged root-doc edits; no source file outside `process/` was left modified.
The earlier smoke command rewrote `reports/openrig_smoke.json`; it was restored
to HEAD with `git checkout --`.

One self-check lesson: the first draft of this note repeated two masked literals
(the private-workspace marker and a credential directory path) in its own scan
table. `check_content.py` and `check_sanitization.py` failed on this note, the
literals were replaced with `<PRIVATE-WORKSPACE-MARKER>` and
`~/.<credential-dir>`, and the re-run passes. The gate is working at the note
layer, not only at the payload layer.

## 5. Remaining issues for independent QA

These were found in round 1 and are **not** sanitization failures. They are
recorded here so QA can decide whether to fix, document, or accept them:

1. **Registry drift (G2).** `registries/standalone-rounds.md:26` says 13 indexed;
   `registries/thinking-rounds.md:16` says 15 indexed. One authoritative value or
   an explicit snapshot note is needed.
2. **Broken table (G3).** A blank line in `registries/thinking-rounds.md` between
   the `THINK-13` and `THINK-14` rows drops the last two rows out of the rendered
   table.
3. **Missing companion artifacts (G4/G5).** Protocols reference `tools/*.mjs` and
   several templates/ledgers that are not shipped. A reader gets rules but cannot
   run or fill them.
4. **Trace sampling (G6).** Traces cover only fast-response rounds 3/4; the
   archive should say they are examples, not a complete execution record.
5. **Case-study pair (G7).** fast-response has a final report but no acceptance
   record, unlike g3d.
6. **Reading order (G8).** `README.md` does not list `reports/` and does not state
   that many internal paths are intentionally unresolved.
7. **Redaction observability (P5).** 12 files marked `redacted: true` contain no
   documented placeholder; redaction by deletion is plausible but unverifiable.
8. **Traceability (P7).** No source path or commit is mapped per file; the archive
   is categorized, not individually traceable.
9. **Publication state (G9).** `process/` is untracked; nothing is committed or
   pushed.

## 6. Evidence

- Changed files: `process/reports/openrig-local-share-report.md`,
  `process/INVENTORY.json`, `process/PROVENANCE.md`.
- Added file: `process/ROUND-NOTES-2.md`.
- `process/ROUND-NOTES-1.md`: unchanged.
- Payload reconciliation: 56 files / 610,399 bytes, 0 mismatches.
- These notes are the evidence artifact for the `s2_publication_qa` closure.

## 7. Boundaries

- Only `process/` was modified. The private source workspace was not read or
  written during this step.
- No commit, tag, or push was made.
- The PASS verdicts cover the repository's defined gates plus the scans above;
  they do not establish that the private sources matched these copies at copy
  time, because no per-file source mapping exists.
