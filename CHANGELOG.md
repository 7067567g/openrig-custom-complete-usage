# Changelog

## Unreleased

- Added project-local governance layers to the OpenRig + workflow guide
  (Command Center / General Staff / SOLO / Medical Center), including aliases
  such as “组织部” = Command Center and semantic-matching rules for unfamiliar
  names.
- Added a sanitized `process/` archive: story, decisions, pitfalls, governance
  protocols, registries, round briefs, workflow specs, stamps, traces, case
  studies, provenance, and round/QA notes from a real OpenRig publication run.
- Added an explicit benchmark status: **not run due to budget**; no benchmark,
  cost, latency, or model-quality result is claimed.
- Added a public index link and validation note for the process archive and
  benchmark status.

## 0.1.12

- Replaced per-turn question budgeting with a clarification gate:
  one consolidated batch before an automated multi-round run starts, then zero
  questions after start.
- Added the gate to the LLM misread quick reference, the OpenRig + workflow
  guide, `AGENTS.md`, and MULTI-ROUND.
- Mid-flow blockers are written to `BLOCKED`/`NEED_MAIN` instead of asked.


## 0.1.11

- Added fuzzy-tolerance and question-budget policy to the LLM misread quick
  reference and the OpenRig + workflow guide:
  - small deviation: proceed and state the assumption;
  - cross-layer / irreversible / costly: ask one consolidated question;
  - at most one question per turn.


## 0.1.10

- Added bilingual `docs/LLM-MISREAD-QUICKREF.md` / `.zh-CN.md`: common user
  misreads, default interpretation, deviation thresholds, and concrete
  clarification templates.
- Linked the quick reference from README, the OpenRig + workflow guide, and the
  docs index.


## 0.1.9

- Added a “how to ask for this” phrase table to the OpenRig + workflow guide
  (English and Chinese).
- Documented the default ask **“用 OpenRig 跑工作流。”** and the precise ask
  **“用 OpenRig 执行 SCTG 工作流，单线跑。”**
- Added the same short note to README / README.zh-CN.


## 0.1.8

- Added bilingual `docs/OPENRIG-WORKFLOW-GUIDE.md` / `.zh-CN.md`:
  one-page decision table, three-layer model, step-vs-round, one-line
  `rig workflow run`, queue closure, preflight side effects, memory/concurrency,
  and troubleshooting matrix.
- Linked the guide from README, QUICKSTART, OPENRIG, ARCHITECTURE, and
  MULTI-ROUND.
- Expanded CONCEPTS with rig, qitem/packet, workflow instance, step, and closure.
- Tests: 154 passed, 1 skipped; content audit: 22 pairs, 11 examples.


## 0.1.7

- Added global `dsh.slice` example (8G/9G/2G).
- Documented heavy/light concurrency profiles and lock-based degradation.
- Added `examples/memory-limits/dsh.slice`.
- Tests: 154 passed, 1 skipped.


## 0.1.6

- Added long-running service memory guidance: shared agent host and app service
  drop-ins.
- Added `examples/memory-limits/agent-host-memory.conf` and
  `app-service-memory.conf`.
- Clarified global user-service limits vs per-run seat scopes.
- Tests: 154 passed, 1 skipped.


## 0.1.5

- Added `docs/MEMORY-SAFETY.md` + Chinese counterpart: cgroup semantics,
  5G/6G/1G seat limits, and pressure-order guidance.
- Added `examples/memory-limits/`: seat launch and non-destructive guard
  examples.
- Added case study 03: cgroup page cache and a sanitized host OOM.
- Documented that `MemoryHigh` is not additive with `MemoryMax`/`MemorySwapMax`
  and that disposable GUI/image workloads are reclaimed before the agent
  workflow.
- Tests: 154 passed, 1 skipped.


## 0.1.4

- Added runnable `multi-card`, `decision`, `rollback`, and `two-seat-handoff` examples.
- Added a benchmark mechanics harness, synthetic task pack, and smoke result.
- Added a real single-step OpenRig workflow evidence sample (`examples/live-run/`).
- Added three complete 12-round workflow-group cases under `examples/round-cases/`.
- Added local `docs/CONCEPTS.md` + Chinese counterpart.
- Added `scripts/check_sanitization.py` to `make check` / CI.
- Removed OpenRig-managed `.agents/` seat artifacts and restored authored `AGENTS.md`.
- Rewrote the public git history as a clean single commit for v0.1.4.
- Tests: 154 passed, 1 skipped.

## 0.1.3

- Added `reports/content_gap_audit.md` and its Chinese counterpart.
- Added `docs/REFERENCE.md` and `docs/cases/` (bilingual).
- Added a sanitized generated OpenRig bundle and plan/validate/doctor evidence
  samples under `examples/sanitized-run/`.
- Added a runnable SCTG demo (`examples/sctg-minimal/run_demo.py`) and test.
- Integrated `check_content.py` (14 bilingual pairs, 4 examples) into CI.
- Tests: 147 passed, 1 skipped.


## 0.1.2

- Added bilingual documentation pairs for README, quickstart, architecture,
  multi-round, OpenRig, publishing, versioning, environment, reproducibility,
  limitations, validation, and examples.
- Added `examples/sanitized-run/`: a synthetic, sanitized control-plane sample.
- Added `scripts/check_content.py` and wired it into `make check` / CI.
- Added English/Chinese switches and `docs/INDEX.md`.
- Removed remaining internal project names and personal paths from template docs.


## 0.1.1

- Renamed the public repository to `openrig-custom-complete-usage`.
- Updated README, CITATION, package metadata, and release links.
- CI passes on Python 3.11 and 3.12.


## 0.1.0

- Initial complete-usage release candidate.
- Added workflow-group core: `WORKFLOW.md`, roles, templates, `wf.py`, linters, adapters.
- Added OpenRig hybrid master: preflight, render, bridge, rig/workflow templates.
- Added SCTG reference kit under `sctg-kit/`.
- Added local multi-round and OpenRig minimal examples.
- Added docs for quickstart, architecture, multi-round, OpenRig, publishing.
- Tests: 142 passed, 1 skipped in the local validation environment.
