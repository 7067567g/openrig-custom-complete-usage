# OpenRig Lead onboarding guide

A small guide executable for a Lead agent. The Lead answers a few staged
questions; a **headless reviewer** checks the answers against the pinned OpenRig
content index. The reviewer must end with an exact verdict string, and the guide
copies that string into `RESULT.txt`.

```text
Lead answers -> headless reviewer -> PASS / small deviation / large deviation / incomplete
                                  -> 引导完成 / 请重新运行引导 / explanation
```

## Quick start

```bash
cd openrig-custom-complete-usage
python3 tools/lead-guide/guide.py check-version
python3 tools/lead-guide/guide.py run --workdir /tmp/openrig-lead-guide
```

Or use the wrapper:

```bash
./tools/lead-guide/run.sh run --workdir /tmp/openrig-lead-guide
```

The interactive run asks the questions in `stages.json` and then launches the
reviewer. For a non-interactive run, put answers in a file and call:

```bash
python3 tools/lead-guide/guide.py review \
  --workdir /tmp/openrig-lead-guide \
  --answers tools/lead-guide/answers.example.md
```

## Review contract

The reviewer must print these lines at the end:

```text
VERDICT: PASS | SMALL_DEVIATION | LARGE_DEVIATION | INCOMPLETE
MISSING: ...
QUESTIONS: ...
EXPLANATION: ...
FINAL: 引导完成 | 请重新运行引导
```

- `PASS` -> the guide writes exactly `引导完成`.
- `SMALL_DEVIATION` -> the guide writes `FOLLOWUP-QUESTIONS.md`; after the
  questions are answered, run review again.
- `LARGE_DEVIATION` -> the guide writes exactly `请重新运行引导`.
- `INCOMPLETE` -> the guide writes an explanation of what is missing.

The guide never invents the final string. A malformed reviewer output fails
closed. All five lines are required; a missing field fails closed with
`未完成：审查输出缺少必需字段 ...`.

## Run artifacts

Each review writes `answers.md`, `review.txt`, `RESULT.txt`, and (for a small
deviation) `FOLLOWUP-QUESTIONS.md` in the workdir. It also archives the bundle
under `workdir/history/<timestamp>/` with a `meta.json` recording the verdict
and exit code, so a later audit can reconstruct what was reviewed and returned.

## Relationship to the 40 guide

The 40 guide polls a single `引导词.txt` and advances after the AI's edit is
stable. The Lead guide has no external editor loop: `run` writes the answers
once, or `review` reads a supplied file, then makes one reviewer call. The
stage list, version pin, and per-run archive are kept; polling/stable-window is
deliberately not copied because there is no concurrent writer to settle.

## Version pin and drift

`version.json` pins:

- the OpenRig guide version (`VERSION`),
- the main-document SHA-256,
- the content-index SHA-256.

If any of them moves, `check-version` and every run fail with `VERSION_DRIFT`
before asking questions. Update `version.json`, `content-index.json`, and the
persona first. **Guide-file version handling has priority over onboarding.**

## Files

| Path | Purpose |
|---|---|
| `guide.py` | CLI: `check-version`, `run`, `review` |
| `run.sh` | repo-root wrapper |
| `stages.json` | onboarding questions |
| `content-index.json` | pinned content index and must-know facts |
| `persona/LEAD-ONBOARDING.md` | reviewer persona and output contract |
| `version.json` | version/hash pins |
| `answers.example.md` | example answers for a dry run |

## Reviewer command

Default:

```text
dsh --profile headless "<prompt>"
```

Override with `LEAD_GUIDE_REVIEWER_CMD="<command>"`. The prompt is appended as
the last argument. Use a mock command in tests; do not call a paid model in CI.

## Boundary

This tool is an onboarding gate, not a replacement for QA. It checks that the
Lead's initial mental model is correct enough to start work. It does not grant
permissions, approve publications, or validate a live run.


## After QA

Independent QA passed the first version. Post-QA hardening is recorded in
[`POST-QA-NOTES.md`](POST-QA-NOTES.md): content-index anchor, test wiring,
missing-`VERSION` drift handling, reviewer exit-code fail-closed, and the
budget-gated `make bench-smoke` target.

## Tests and CI

```bash
make test PY=/tmp/ocu-venv2/bin/python
```

`make test` runs `tools/lead-guide/tests/test_lead_guide.py` before the repo
pytest suite. Tests use only local mocks; no paid model is called.
