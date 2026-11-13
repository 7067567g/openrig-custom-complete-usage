# Post-QA hardening notes

- Date: 2026-11-14
- Base QA: `tools/lead-guide/QA-REPORT.md` (PASS)
- Workflow instance: `01M7B02R502V70PXZ6R42YEEW9`

The independent QA passed the guide and left five non-blocking notes. Four were
cheap to harden and are fixed here; the test-harness race is a repo observation,
not a guide defect.

## Fixed

1. **Content-index anchor.** `safety` now points at the rendered GitHub slug
   `#8-preflightbridgeteardown`, and `version.json` re-pins the new
   `contentIndexSha256`.
2. **Tests wired into the repo test target.** `make test` now runs
   `tools/lead-guide/tests/test_lead_guide.py` before pytest, and `make check`
   compiles `tools/lead-guide`.
3. **Missing `VERSION` is drift, not an exception.** `check_version` returns
   `缺少 OpenRig VERSION 文件` and the CLI exits 3 instead of raising.
4. **Reviewer exit code is checked.** A non-zero reviewer exit now fails closed
   as `未完成：审查命令失败...` even if the text contains a PASS block.
5. **Benchmark target is budget-gated.** `make bench-smoke` now prints
   `BENCHMARK NOT RUN: budget unavailable` and exits 0; it does not call the paid
   harness. The real harness remains at `benchmark/harness/run_benchmark.py` for
   a future explicitly budgeted run.

## Evidence

```text
$ python3 tools/lead-guide/guide.py check-version
VERSION_OK
guideVersion=1.0.1
openrigGuideVersion=0.1.12
mainDocSha256=c6fcab4b0c11befb8457e55ff0e7a8bd06bae66e0cac866cffb7234c08e9871c

$ python3 tools/lead-guide/tests/test_lead_guide.py
Ran 17 tests in 0.289s
OK

$ make test PY=/tmp/ocu-venv2/bin/python
check_repo / check_content / check_sanitization: PASS
lead-guide tests: 17/17 PASS
pytest: 154 passed, 1 skipped

$ python3 tools/lead-guide/guide.py review \
    --workdir /tmp/openrig-lead-guide-test2 \
    --answers tools/lead-guide/answers.example.md
审查结论: PASS
引导完成
```

The final `RESULT.txt` is exactly `引导完成` as UTF-8 bytes with no trailing
newline. The review archive contains `answers.md`, `review.txt`, `RESULT.txt`,
and `meta.json`.

## Not changed

- The guide does not implement 40-guide stable-window polling; answers are
  written synchronously and review reads a supplied file. This is documented in
  `README.md` and `ROUND-NOTES.md`.
- The onboarding gate does not grant permissions, approve publication, or
  replace QA.
