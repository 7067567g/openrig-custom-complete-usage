# Round notes — Lead onboarding guide review

- Workflow instance: `01M7B02R502V70PXZ6R42YEEW9` (step `s1_builder_review`, builder)
- Date: 2026-11-14
- Scope: `tools/lead-guide/**` only; `AGENTS.md` untouched; no commit or push
- Reference: `40-ai-stage-guide` (`guide.py`, `README.md`) and the round brief

## 0. Summary

The guide already met the core contract: version pin + drift blocking, a
headless reviewer (default `dsh --profile headless`), strict final strings, and
no paid-model calls in tests. The review found four hardening gaps and one
documentation mismatch:

1. End-to-end tests asserted stdout, not `RESULT.txt`, so the exact-string
   contract was not actually covered.
2. The guide accepted a reviewer block missing `MISSING` / `QUESTIONS` /
   `EXPLANATION`, although the brief requires all five fields.
3. `SMALL_DEVIATION` with an empty `QUESTIONS` line fell through to a generic
   “unrecognized output” path instead of writing `FOLLOWUP-QUESTIONS.md`.
4. No per-run archive existed, although the 40 guide pattern keeps a history.
5. The persona’s content-index table listed a `commands` entry that does not
   exist and omitted the shipped `safety` and `patch` entries.

All five are fixed. The suite is now 15 tests (up from 10), all pass; the four
gates and `py_compile` pass; mock paths produce the exact required strings.

## 1. Design mapping: 40 guide -> Lead guide

| 40 guide element | Lead guide implementation | Deliberate difference |
|---|---|---|
| Single interaction file `引导词.txt` | `stages.json` questions -> `answers.md`; `review` accepts a file | The Lead answers a staged questionnaire, not a free-form prompt file |
| Program-controlled stage advance | Five stages in `stages.json`; one headless review at the end | The reviewer owns the verdict; the script does not advance or grade |
| Stable-window polling after an external AI edit | Not implemented | There is no concurrent editor: `run` writes answers synchronously, or `review` reads a supplied file. Polling would be cargo-culting the 40 guide |
| `history/<timestamp>/` archive | `workdir/history/<timestamp>/` with answers, review, `RESULT.txt`, optional follow-up, and `meta.json` | One archive per review, not one per stage |
| Version pin and drift blocking | `VERSION` + main-doc SHA-256 + content-index SHA-256 in `version.json`; `check-version` and every run block on drift | Guide-file version has priority; drift exits 3 before questions/review |
| Final completion string | `RESULT.txt` exactly `引导完成` / `请重新运行引导` / `未完成：...` | No extra prose or trailing newline |
| Image-business fields | None | Replaced by OpenRig layers, units, governance, aliases, clarification gate, safety, evidence/QA, patch boundary |

## 2. What changed

- `guide.py`
  - `parse_review` now tracks which required lines were actually present and
    parses keys case-insensitively; a missing `VERDICT` / `MISSING` /
    `QUESTIONS` / `EXPLANATION` / `FINAL` fails closed with
    `未完成：审查输出缺少必需字段 ...`.
  - `SMALL_DEVIATION` always writes `FOLLOWUP-QUESTIONS.md`; if the reviewer
    left `QUESTIONS` empty, the file asks for confirmation using `MISSING` or
    `EXPLANATION` instead of silently falling through.
  - `write_result` writes exactly the contract string (no trailing newline).
  - `archive_run` / `finalize` archive each review bundle under
    `history/<timestamp>/` with a `meta.json` (verdict, exit code, timestamp).
  - `check_version` takes optional `root` / `guide_dir` so drift blocking can be
    tested without touching the real repo.
  - Removed unused `re` / `time` imports; `ruff check tools/lead-guide` passes.
- `tests/test_lead_guide.py`
  - End-to-end tests now inspect the real `RESULT.txt` in the workdir.
  - Added a `SMALL_DEVIATION` path test (`FOLLOWUP-QUESTIONS.md`, no pass), and
    a variant that returns `FINAL: 引导完成` to prove the small-deviation path
    still cannot pass directly.
  - Added a missing-required-fields test (fails closed).
  - Added a content-index-drift test and a review-blocks-on-drift test.
  - Test count: 10 -> 15.
- `persona/LEAD-ONBOARDING.md`
  - Content-index table now matches `content-index.json`: removed `commands`,
    added `safety` and `patch`.
- `README.md`
  - Documents run artifacts, the per-run archive, all-five-fields enforcement,
    and why stable-window polling is intentionally not copied.

## 3. Verification evidence

Exact commands from the repo root:

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
Ran 15 tests in 0.251s
OK
```

Mock reviewer paths (temporary scripts; no paid model):

| Path | Exit | `RESULT.txt` content |
|---|---:|---|
| PASS | 0 | `引导完成` |
| LARGE_DEVIATION | 2 | `请重新运行引导` |
| INCOMPLETE | 4 | `未完成：缺少关键维度` |
| SMALL_DEVIATION | 5 | `偏差较小，但尚未确认关键问题。请回答 FOLLOWUP-QUESTIONS.md 后重新运行 review。` + `FOLLOWUP-QUESTIONS.md` |
| PASS with missing fields | 4 | `未完成：审查输出缺少必需字段 MISSING, QUESTIONS, EXPLANATION...` |

Version-drift blocking, exercised against a temporary repo copy:

```text
check_version rc=3
review rc=3
no RESULT written (blocked)
workdir not created
```

Repo-level checks:

```text
$ make test PY=/tmp/ocu-venv2/bin/python
check_repo / check_content / check_sanitization: PASS
pytest: 154 passed, 1 skipped

$ make render-dry
render plan produced under /tmp; no repo files changed
```

`ruff check tools/lead-guide`: all checks passed.

## 4. What the reviewer does not do

- It does not fabricate a verdict or a final string; it only copies the
  reviewer’s parsed verdict and requires an exact `FINAL` for PASS.
- It does not call a model in tests; tests use `LEAD_GUIDE_REVIEWER_CMD` mocks.
- It does not modify `AGENTS.md`, commit, or push.
- It does not implement 40-guide polling; that choice is documented in
  `README.md` and in section 1 above.

## 5. Boundaries and remaining notes

- Only `tools/lead-guide/**` was modified.
- The default `dsh --profile headless` reviewer was not invoked in this round
  (would require the live profile); mocks exercise the CLI contract.
- The guide is an onboarding gate, not a QA replacement or permission grant.
- `RESULT.txt` is now exactly the contract string; consumers that assumed a
  trailing newline should read it with `.strip()` if needed.
- No commit or push. The Lead owns publication.

## 6. Handoff

Ready for `s2_qa`: re-run `check-version`, the 15 tests, `py_compile`, and the
mock PASS / LARGE_DEVIATION / INCOMPLETE paths; verify exact `RESULT.txt`
strings and drift blocking.

## 7. QA follow-up (non-blocking)

Independent QA (`s2_qa`, `work-qa@openrig-publish-20261114`) returned **PASS**
and reproduced all required contracts, including the small-deviation
confirmation flow (SMALL -> follow-up -> second PASS -> exact `引导完成`).
Full evidence is in `QA-REPORT.md`.

Non-blocking notes recorded there and not fixed in this round:

1. `content-index.json` `safety` anchor does not resolve after GitHub slugging
   (unused by `guide.py`; fixing it would also require re-pinning
   `contentIndexSha256`).
2. The guide tests are not wired into `make test`/CI.
3. A missing repo `VERSION` raises instead of reporting `VERSION_DRIFT` (not
   reachable in the shipped repo).
4. The guide does not check the reviewer command's exit code.
5. Concurrent repo pytest can transiently expose a `_run` artifact to
   `check_sanitization.py`; serial `make test` is clean.

None of these changes the current onboarding verdict. `AGENTS.md` untouched; no
commit or push.
