# AGENTS

This repository is a public, sanitized usage example.

## Rules for agents working here

1. Never add real credentials, tokens, cookies, or `.dsh` auth files.
2. Never add real project `runs/` data or transcripts.
3. Keep absolute personal paths out of docs and examples; use `$REPO_ROOT` or relative paths.
4. Do not change `sctg-kit/` gate semantics without a test.
5. Run `make test` before proposing changes.
6. For OpenRig changes, run the render dry-run and bridge doctor smoke.

## Project-local governance layers

OpenRig core is rigs/seats/queue/workflows. If a project repo contains
`docs/command-center/`, `docs/general-staff/`, `docs/rounds/` or
`docs/medical-center/`, those are project-local governance layers, not OpenRig
kernel features. Read `docs/OPENRIG-WORKFLOW-GUIDE.md` section 0.2 before classifying
such a problem.

Names are not authoritative: **组织部 is an alias of 总指挥部 (Command Center)**.
Match by governance dimension (Command Center / General Staff / SOLO / Medical
Center); if a name matches nothing or could change scope/cost/irreversible
action, ask once with A/B/C/D options before acting.

## Clarification gate for automated multi-round runs

For a complete multi-round automated flow, ask all material clarifying
questions once before the run starts (layer, rounds-vs-steps, output/acceptance,
irreversible actions, budget). After the run starts, do not ask the user
anything: use documented defaults, record assumptions in `DECISIONS.md` or
`STATUS`, and write `BLOCKED`/`NEED_MAIN` if a decision is required.
