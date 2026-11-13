# QA report — Lead onboarding guide (`s2_qa`)

- Workflow instance: `01M7B02R502V70PXZ6R42YEEW9`
- Step: `s2_qa` (qa)
- Date: 2026-11-14
- Reviewer: `work-qa@openrig-publish-20261114`
- Scope: independent review of `tools/lead-guide/` against
  `lead-guide-20261114/BRIEF.md`; no private source read or modified; no commit,
  tag, or push; no paid model call.

## 0. Verdict

**PASS.**

Every required contract was reproduced independently: version pin and
three-way drift blocking, headless-reviewer output parsing, exact `RESULT.txt`
strings, small-deviation follow-up, and fail-closed behaviour. The script does
not fabricate a verdict. Non-blocking notes are in section 6.

| Check | Result |
|---|---|
| `check-version` baseline | **PASS** (`VERSION_OK`, rc 0) |
| Version / main-doc / content-index drift | **PASS** (all three block, rc 3) |
| `py_compile` | **PASS** (rc 0) |
| Unit tests | **PASS** (15 tests, OK) |
| `ruff check tools/lead-guide` | **PASS** (All checks passed) |
| Mock reviewer paths | **PASS** (PASS / LARGE / INCOMPLETE / SMALL / missing fields) |
| Exact `RESULT.txt` strings | **PASS** (no trailing newline) |
| Persona ↔ content-index IDs | **PASS** (same 10 IDs) |
| Repo gates (`check_repo`, `check_content`, `check_sanitization`, `doc_consistency`) | **PASS** |
| `make test` (gates + pytest) | **PASS** |
| `make render-dry` | **PASS** (no repo files changed) |

## 1. Acceptance commands (re-run independently)

From the repo root:

```text
$ python3 tools/lead-guide/guide.py check-version
VERSION_OK
guideVersion=1.0.0
openrigGuideVersion=0.1.12
mainDocSha256=c6fcab4b0c11befb8457e55ff0e7a8bd06bae66e0cac866cffb7234c08e9871c
rc=0

$ python3 -m py_compile tools/lead-guide/guide.py
rc=0

$ python3 tools/lead-guide/tests/test_lead_guide.py
Ran 15 tests in 0.252s
OK
rc=0

$ ruff check tools/lead-guide
All checks passed!

$ python3 scripts/check_repo.py
{"verdict": "PASS", "errors": []}
$ python3 scripts/check_content.py
{"verdict": "PASS", "pairs": 23, "examples": 11, "errors": []}
$ python3 scripts/check_sanitization.py
{"verdict": "PASS", "errors": []}
$ python3 scripts/doc_consistency.py --check
doc_consistency: 0 error(s), 0 warning(s)

$ make test PY=/tmp/ocu-venv2/bin/python
check_repo / check_content / check_sanitization: PASS
pytest: 154 passed, 1 skipped
```

The three pinned hashes were also recomputed by hand: `VERSION` = `0.1.12`,
main-document SHA-256 and `content-index.json` SHA-256 both match
`version.json`.

## 2. Exact `RESULT.txt` contract (independent mocks)

Each row used a fresh workdir and a local mock reviewer via
`LEAD_GUIDE_REVIEWER_CMD`; no model was called. "Trailing newline" is checked on
the raw bytes of `RESULT.txt`.

| Reviewer output | rc | `RESULT.txt` | trailing NL | follow-up | archive `meta.verdict` |
|---|---:|---|---|---|---|
| PASS, `FINAL: 引导完成` | 0 | `引导完成` | no | no | `PASS` |
| LARGE_DEVIATION | 2 | `请重新运行引导` | no | no | `LARGE_DEVIATION` |
| INCOMPLETE | 4 | `未完成：缺少关键维度` | no | no | `INCOMPLETE` |
| SMALL_DEVIATION | 5 | `偏差较小，但尚未确认关键问题。请回答 FOLLOWUP-QUESTIONS.md 后重新运行 review。` | no | yes | `SMALL_DEVIATION` |
| SMALL_DEVIATION with `FINAL: 引导完成` | 5 | same non-pass string | no | yes | `SMALL_DEVIATION` |
| PASS with `MISSING`/`QUESTIONS`/`EXPLANATION` absent | 4 | `未完成：审查输出缺少必需字段 MISSING, QUESTIONS, EXPLANATION，请重新运行引导或检查审查命令。` | no | no | `INCOMPLETE` |

The PASS row is exact after `rstrip`; no trailing newline is written. The
small-deviation row proves `SMALL_DEVIATION` cannot pass directly even when the
reviewer writes `FINAL: 引导完成`. Every review also produced exactly one
`workdir/history/<timestamp>/` bundle containing `RESULT.txt` and `meta.json`.

Additional paths exercised:

- `run --answers FILE` with a mock PASS → rc 0, `RESULT.txt` exactly
  `引导完成`, no trailing newline.
- `review` with a missing answers file → rc 4, `RESULT.txt` =
  `未完成：缺少答题文件，无法开始审查。`
- **Small-deviation confirmation flow (two reviews on one workdir):** first
  review with a `SMALL_DEVIATION` mock → rc 5, `FOLLOWUP-QUESTIONS.md` written,
  `RESULT.txt` not `引导完成`; second review with a `PASS` mock → rc 0,
  `RESULT.txt` exactly `引导完成` (no trailing newline). The workdir archived
  both review bundles (`history/` count 2), so the confirmation is auditable.

## 3. Version-drift blocking (independent temp repo)

A throwaway copy (`/tmp/qa-drift`) containing `VERSION`, the main document, and
`tools/lead-guide/` was mutated three ways:

| Mutation | `check-version` | `review` | Workdir / `RESULT.txt` |
|---|---|---|---|
| `VERSION` → `9.9.9` | rc 3, `VERSION_DRIFT` | rc 3, `VERSION_DRIFT` | workdir not created; no `RESULT.txt` |
| main document changed | rc 3, `主文档哈希漂移` | — | — |
| `content-index.json` changed | rc 3, `内容索引哈希漂移` | — | — |

`run --answers FILE` under the same drift also returns rc 3 and does not create
the workdir. The baseline (unmutated copy) reports `VERSION_OK`. This matches
brief item 1: both answering and review are blocked, and the guide-file version
has priority.

## 4. No fabricated verdicts

Reviewed the control flow in `guide.py` and exercised each branch:

- `PASS` is written as `引导完成` only when the reviewer output contains both
  `VERDICT: PASS` **and** `FINAL: 引导完成`. A `PASS` verdict with any other
  `FINAL` falls through to the fail-closed INCOMPLETE path.
- `LARGE_DEVIATION` copies the contract string `请重新运行引导`; it does not
  invent a pass.
- `INCOMPLETE` writes `未完成：` plus the reviewer's `EXPLANATION` (falling back
  to `MISSING`), not a guide-authored verdict.
- `SMALL_DEVIATION` always writes `FOLLOWUP-QUESTIONS.md` and returns rc 5; it
  cannot emit `引导完成`.
- Missing required fields, unrecognized output, timeout, and unavailable
  reviewer command all fail closed with `INCOMPLETE` and `未完成：...`.
- The reviewer output is written verbatim to `review.txt` before parsing, so the
  source of every verdict is auditable.

The script never calls a model itself; it only invokes the configured
`LEAD_GUIDE_REVIEWER_CMD` (default `dsh --profile headless`) and parses its
output.

## 5. Persona, content index, and stages

- `content-index.json` has 10 entries; the persona table lists the same 10 IDs
  (`layers`, `units`, `clarification`, `governance`, `aliases`, `safety`,
  `memory`, `patch`, `benchmark`, `version`) — set-equal, no missing or extra.
- All non-empty `path` targets exist. Anchors match the guide for layers, units,
  clarification, governance, and aliases. The `safety` anchor is the one
  mismatch noted in section 6.
- `stages.json` has 5 stages × 2 questions = 10 questions; `answers.example.md`
  carries the same 10 question strings in the same order and 10 non-empty
  answers, so the example is directly usable for a dry run.

## 6. Non-blocking notes (recorded, not blockers)

1. **One content-index anchor does not resolve.** The `safety` entry points at
   `#8-preflightbridge-teardown`, but the heading is
   `## 8. Preflight、bridge、teardown`; the rendered GitHub slug drops the
   ideographic comma and yields `#8-preflightbridgeteardown`. `guide.py` uses
   only `id`/`title`/`mustKnow` from the index, not `path`, so this does not
   affect onboarding. Fixing it would also require re-pinning
   `contentIndexSha256` in `version.json`.
2. **The guide tests are not wired into `make test`/CI.** They live in
   `tools/lead-guide/tests/` and `make test` runs only `pytest tests`, so a
   future regression in the guide would not be caught by the repo's test target.
3. **Missing repo `VERSION` raises instead of reporting drift.** If
   `$REPO_ROOT/VERSION` is absent, `check_version` raises and `main` returns rc 2
   with `ERROR: ...`, not `VERSION_DRIFT`. Not reachable in the shipped repo.
4. **Reviewer exit code is not checked.** The guide trusts the reviewer's
   stdout; a non-zero reviewer exit that still prints a valid PASS block would
   pass. Low risk, but checking `returncode` would be stricter.
5. **Test-run race during gate checks.** Running the repo pytest suite while
   `check_sanitization.py` scans the tree can transiently expose
   `examples/sctg-minimal/_run/...` and fail the gate; the artifact is removed
   when pytest finishes. Serial `make test` (the documented order) is clean.
   This is a repo test-harness observation, not a `tools/lead-guide/` defect.

## 7. Boundary compliance

- Reviewed `tools/lead-guide/` only; did not modify the private source workspace.
- Added this report only. `AGENTS.md` is untouched (`git diff AGENTS.md` empty).
- `tools/` remains untracked; no commit, tag, or push.
- No paid model call was made by this review; all reviewer paths used local mocks.
- Repo gates and `make test` were re-run serially after the review; all pass.

## 8. Final verdict

**PASS — the guide is safe to publish.** The required contract is verified at
the source, including exact final strings and three-way drift blocking. The
section 6 items are documentation/robustness nits and do not affect the current
onboarding gate.
