# Changelog

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
