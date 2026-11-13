> Status: historical OpenRig audit (2026-11-13). Addressed in v0.1.4; see `reports/content_gap_audit.md` for current status.

# OpenRig analyst report — public content audit vs SCTG-public

Date: 2026-11-13
Auditor: main-analyst@content-audit-analyst
Target: `$REPO_ROOT`
Reference: `$SCTG_ROOT`
Method: read the five mandated target files, then compared target inventory against
`SCTG-public/docs/` and `SCTG-public/examples/`. One working-tree secret/path scan
was run. No live OpenRig execution was performed.

## 1. Verdict

**READY WITH GAPS**

The repository is publishable as a *usage example*: docs are bilingual, the gate
kit is present, CI is green-path complete, and the validation claim is honest
(`VALIDATION.md:10` and `:53-58` explicitly disclaim live execution). It is not
yet "complete" in the sense the README claims (`README.md:5-11`) because the
benchmark layer is a stub and several SCTG semantic proofs are absent.

Two accuracy nits to fix while publishing:

- `README.md:13` says "147 ... tests pass"; `VALIDATION.md:15` says
  `147 passed, 1 skipped`. State both numbers.
- `README.md:19-32` omits `benchmark/`, `reports/`, and `.agents/` from the
  "What is inside" tree even though `README.md:149` advertises a benchmark harness.

## 2. Top 5 gaps vs SCTG-public

1. **Benchmark harness and published results (largest gap).**
   `SCTG-public/docs/benchmarks/` ships `README.md`, `pilot-2026-11.md`, and
   `results.json` with per-task trials and overhead numbers (e.g. `results.json:6-23`
   multiply: raw median 28.175 s vs SCTG 35.141 s, +24.7%; bugfix +96.6%;
   refactor +64.7%). The target's `benchmark/README.md:8-13` lists the same
   planned layout but no files exist, so `README.md:149` and the "complete usage"
   positioning are unbacked.

2. **Runnable SCTG semantics examples.**
   `SCTG-public/examples/README.md:3-10` advertises five self-contained demos:
   `minimal-run`, `multi-card`, `decision`, `rollback`, `two-seat-handoff`.
   The target has only `examples/sctg-minimal/run_demo.py` plus multi-round,
   openrig-minimal, and sanitized-run. The missing `decision`, `rollback`, and
   `two-seat-handoff` cases are exactly the append-only-ledger, replay, and
   independent-review proofs that `roles/` and `WORKFLOW.md` depend on.

3. **Self-contained reference vocabulary.**
   `docs/REFERENCE.md:8-17` delegates concepts/protocol, ledger, decision model,
   mode policy, security model, glossary/FAQ, performance, and provenance/status
   to `SCTG-public/docs/`. The delegation is correct policy, but the target has no
   local `CONCEPTS`/`GLOSSARY` page, so a reader starting from this repo cannot
   resolve terms used in `roles/*.md` without leaving the repo. SCTG-public also
   has `lessons.md` and `status.md`, which have no target counterpart.

4. **Live OpenRig evidence.**
   The target publishes only derived artifacts: `render-manifest.json`,
   `OPENRIG-BRIDGE.json`, `bridge-doctor.txt`, `rig-up-plan.json`,
   `workflow-validate.json` (`examples/sanitized-run/evidence/`). There is no
   `rig ps --nodes` output, `OPENRIG-STATE.json`, archive manifest, or redacted
   transcript, and `VALIDATION.md:53-58` confirms no live 5-seat run was launched.
   SCTG-public does not own this gap; it is genuinely missing here.

5. **Multi-round and case-study depth.**
   `examples/sanitized-run/` stops at `STATUS-Round-1.md`; there is no Round 2/3,
   no PMO -> TDO -> QA -> MAIN close/decision record, and no `new-round` output.
   `docs/cases/` contains only `01-render-smoke.md`. By contrast SCTG-public ships
   `docs/cases/` and a `decision`/`rollback` example pair that demonstrate the
   transition semantics. The workflow loop in `README.md:70-76` remains asserted
   rather than demonstrated.

## 3. Missing categories (P0/P1/P2)

| Priority | Category | Status | Evidence |
|---|---|---|---|
| P0 | Benchmark harness (`run_suite.py`, `run_pilot.py`, `sandbox.py`, `report_pilot.py`, `local_judge/`, synthetic tasks) | **genuinely missing** | `benchmark/README.md:8-13` is a plan only; no files under `benchmark/` besides it |
| P0 | Published raw-vs-SCTG pilot results | **genuinely missing** | README:149 promises it; SCTG-public `docs/benchmarks/results.json` shows the expected shape |
| P0 | `decision`, `rollback`, `two-seat-handoff` runnable examples | **genuinely missing** (or must be explicitly delegated) | `examples/` has 4 dirs vs SCTG-public `examples/README.md:3-10` |
| P1 | Multi-round Round 2/3 + close/decision cycle | **genuinely missing** | `examples/sanitized-run/STATUS-Round-1.md` only |
| P1 | Live OpenRig run evidence (`rig ps`, `OPENRIG-STATE.json`, transcripts, archive manifest) | **genuinely missing** | `VALIDATION.md:53-58`; no such files in inventory |
| P1 | Second case study (real multi-round) | **genuinely missing** | `docs/cases/` has one smoke case |
| P2 | Core SCTG reference docs (protocol, ledger, decision model, mode policy, security, glossary, FAQ, performance, provenance, status) | **delegated to SCTG-public** | `docs/REFERENCE.md:8-17` |
| P2 | `lessons.md` / `status.md` equivalents | **delegated to SCTG-public** | no local counterpart; SCTG-public `docs/` listing |
| P2 | `minimal-run` / `multi-card` examples | **delegated to SCTG-public** (acceptable duplication boundary) | SCTG-public `examples/README.md:5-6` |
| P2 | Domain-specific templates | **intentionally internal** | only `templates/specialized/openrig-workflow-master/` is public; `reports/content_gap_audit.md:67-70` |
| P2 | `burner/` queue and billing automation, archive/teardown/link-check tools | **intentionally internal** | `reports/content_gap_audit.md:72-76` |
| P2 | Real runs, dashboard configs, copyrighted task statements | **intentionally internal** | `AGENTS.md:1-9`; `benchmark/README.md:16-17` |
| P3 | Bilingual coverage of governance files (`SECURITY`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, `THIRD_PARTY_NOTICES`, `AGENTS`, `CHANGELOG`, release notes) | **genuinely missing (low priority)** | root inventory; `reports/content_gap_audit.md:78-82` |
| P3 | pip-installable packaging | **intentionally out of scope, but undocumented in README** | `reports/content_gap_audit.md:84-87` |

## 4. Concrete file-level recommendations

### P0 — make the benchmark claim true

- Add `benchmark/harness/run_suite.py`, `run_pilot.py`, `sandbox.py`,
  `report_pilot.py`; `benchmark/local_judge/{task.py,scorer.py,oracle_example.py}`;
  `benchmark/tasks/synthetic-v1/{multiply,bugfix,refactor,security}/task.yaml`.
- Add `benchmark/results/pilot-2026-11.md` and `pilot-2026-11.json` using the
  SCTG-public schema (`sctg/benchmark-pilot/v1`), with actual target-repo numbers.
  Do not copy SCTG-public's rows as if they were measured here; either re-run or
  label them as the reference pilot.
- Add `make benchmark-smoke` to `Makefile` and a `benchmark-smoke` job/step to
  `.github/workflows/ci.yml`.
- Correct `benchmark/README.md:16-17`: publishing a synthetic pack and results is
  compatible with not shipping copyrighted statements.

### P0/P1 — close the example gap

- Add `examples/decision/run_demo.py`, `examples/rollback/run_demo.py`,
  `examples/two-seat-handoff/run_demo.py`, and `examples/multi-card/run_demo.py`,
  adapted from SCTG-public (not symlinked) so they remain self-contained.
- Extend `tests/test_examples.py` to parameterize every `examples/*/run_demo.py`;
  update the Examples row in `docs/INDEX.md:14` and `README.md:29`.
- Extend `examples/sanitized-run/` with `STATUS-Round-2.md`, `STATUS-Round-3.md`,
  `sctg/decision-request.json`, `sctg/decision-record.json`, and a close/ack
  ledger excerpt so the loop in `README.md:70-76` is demonstrated.

### P1 — live evidence, without leaking a real environment

- Add `examples/live-run/` (sanitized) containing `rig-ps-nodes.json`,
  `OPENRIG-STATE.json`, `MANIFEST.json`, and `transcripts/*.md` with redaction
  markers. Update `VALIDATION.md` and `docs/LIMITATIONS.md` at the same time.
- While evidence is absent, keep the READY-WITH-GAPS framing; do not let
  `README.md:13-15` drift into implying a hybrid E2E pass.

### P2 — docs and navigation

- Add `docs/CONCEPTS.md` + `.zh-CN.md` (a 1-page local glossary of card, gate,
  seat, round, decision, ledger) that links out to SCTG-public for depth.
- Add `docs/cases/02-multi-round.md` + `.zh-CN.md` once Round 2/3 exists.
- Add missing rows to `docs/INDEX.md`: Validation (`VALIDATION.md`), Releases
  (`docs/releases/`), Security (`SECURITY.md`), and Workflow tags
  (`WORKFLOW-TAGS.md`). `doc_consistency.py` should assert these files exist.
- Pin external references in `docs/REFERENCE.md` to a tag or commit rather than
  `main`, so delegated semantics cannot silently change.

### P2 — CI and repo hygiene

- `.github/workflows/ci.yml`: add `make smoke` (defined at `Makefile:29-30` but
  never run in CI), a `bridge-doctor` step (required by `AGENTS.md:6` but absent),
  and `make bench-smoke` once P0 lands. Avoid running `make check` twice
  (`ci.yml:27` plus `test: check` at `Makefile:12`).
- Decide whether `.agents/skills/` is public. If not, add it to `.gitignore`, the
  publishing exclusions, and `tests/test_public_repo.py`; if yes, mark it as
  dogfooding in `docs/PUBLISHING.md`.
- `templates/ISSUES.xlsx`: document that it is a binary template, or generate it
  from the markdown templates so its metadata can be reviewed in diffs.

## 5. Sanitization risks

Working-tree scan result: one absolute-path hit, no token/private-key patterns.

- **Medium — `.agents/` publishes internal operating doctrine.**
  `.agents/skills/orchestration-team/SKILL.md:10-15` references internal
  `docs/reference/product-journey-sdlc.md` and `$OPENRIG_HOME` precedence rules,
  and the skill set reads as internal methodology rather than usage documentation.
  This looks unintentional for a public usage repo. At audit time `.agents/` was
  untracked (`git status`), so it ships only if someone commits it — either keep
  it ignored or justify it in `docs/PUBLISHING.md`.
- **Low — upstream example path.**
  `.agents/skills/systematic-debugging/root-cause-tracing.md:36` contains
  `<upstream>/project/packages/core`, a generic upstream example. Not a leak,
  but it trips path scanners and will be mistaken for an author path.
- **Medium — binary metadata.** `templates/ISSUES.xlsx` can carry
  `docProps/core.xml` creator/lastModifiedBy values that text scans never see.
  Rebuild it with neutral metadata or strip it before release.
- **Medium — git history is unscanned.** The clean working tree does not prove a
  clean history. Run a full-history scan (`gitleaks`/`trufflehog` plus review of
  deleted paths) before tagging the release; earlier runs or personal paths may
  remain in old commits.
- **Low — evidence artifacts.** `examples/sanitized-run/evidence/*.json` and
  `openrig/render-manifest.json` are clean of `/home` paths, but they embed
  run ids and ports (47901-47912 per `VALIDATION.md:24`). Keep them synthetic and
  add a CI assertion that evidence files contain no `/home/`, `<macOS-home>/`, `.dsh`,
  or hostname values.
- **Low — claimed sanitization has no automated gate.** Add
  `scripts/check_sanitization.py` and wire it into `make check`, covering
  `/home/*`, `/Users/*`, `<dsh-home>`, token prefixes, private-key headers, and
  transcript-like files. `tests/test_public_repo.py` currently is not a
  substitute for a content scan.
- **No secrets found** in the working tree for `sk-*`, `ghp_*`, `gho_*`, `xox*`,
  `AKIA*`, or private-key headers.
