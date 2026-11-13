# Content gap audit — 2026-11-13

Scope: compare the published repository with the local complete usage
(`workflow-group` + `openrig-workflow-master` + SCTG-public) and list content
that is missing, delegated, or intentionally excluded.

## Uploaded

- Bilingual README, quickstart, architecture, multi-round, OpenRig, publishing,
  versioning, environment, reproducibility, limitations, validation, cases,
  reference, concepts, benchmark, examples, and validation docs.
- Runnable SCTG examples: `minimal`, `multi-card`, `decision`, `rollback`,
  `two-seat-handoff`.
- Sanitized control-plane sample (`examples/sanitized-run/`).
- Generated, sanitized OpenRig bundle and evidence samples.
- A **real single-step OpenRig workflow run** with `rig ps`, workflow state, and
  trace evidence (`examples/live-run/`).
- Benchmark mechanics harness with synthetic task pack and smoke result
  (`benchmark/`); not yet a model benchmark.
- Three complete synthetic-but-real 12-round workflow-group cases
  (`examples/round-cases/`).
- CI, repo hygiene, content audit, sanitization gate, release notes, tags, and
  GitHub releases.

## Still missing / intentionally split

### P0 — full model benchmark harness and results

The mechanics harness exists, but the full raw-vs-SCTG model harness and
published model results are still missing:

- model arms / launchers
- local judge, oracle/generator examples, sandbox/preflight audit
- real raw-vs-SCTG results

### P1 — 5-seat live OpenRig evidence

`examples/live-run/` proves a real single-step OpenRig workflow and packet
handoff. Still missing: a sanitized 5-seat hybrid run with `rig ps --nodes`,
transcripts, archive manifest, and close/teardown evidence.

### P1 — multi-round depth

The repository now has three 12-round synthetic cases. Still missing: a real
project case study with 10+ rounds and model-produced artifacts.

### P2 — core SCTG reference docs

Protocol, ledger, decision model, mode policy, security model, glossary, FAQ,
performance, provenance, and status are maintained in `SCTG-public` and linked
from `docs/REFERENCE.md` / `docs/CONCEPTS.md`; intentionally not duplicated.

### P2 — case studies

Only one smoke case (`docs/cases/01-render-smoke.md`) is included. Missing a
real multi-round case study.

### P2 — specialized templates

Only `openrig-workflow-master` is included. Domain-specific templates are
intentionally excluded.

### P2 — internal-only assets

- `burner/` queue and billing automation: intentionally excluded.
- archive/teardown/link-check tools: referenced, not included.
- screenshots and visual assets: none; ASCII diagrams are used instead.

### P3 — bilingual coverage

19 English/Chinese doc pairs are covered. Still English-only: `SECURITY.md`,
`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `THIRD_PARTY_NOTICES.md`, `AGENTS.md`,
`CHANGELOG.md`, and release notes.

### P3 — packaging

`pyproject.toml` is metadata-only; the repository is not a pip-installable
package. It is a usage repository, not a library distribution.

## Sanitization status

- `.agents/` seat artifacts removed and gitignored.
- `scripts/check_sanitization.py` gates author paths, credentials, and private
  keys in CI.
- `templates/ISSUES.xlsx` metadata inspected: neutral (`creator=openpyxl`).
- Public git history is published as a clean single commit for v0.1.4.

## Recommended next steps

1. Add the full model benchmark harness and actual results (P0).
2. Capture one sanitized 5-seat OpenRig run (P1).
3. Add Round 2/3 to the sanitized multi-round sample (P1).
4. Add one real case study when available (P2).
5. Add Chinese versions of governance files if needed (P3).
