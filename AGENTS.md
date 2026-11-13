# AGENTS

This repository is a public, sanitized usage example.

## Rules for agents working here

1. Never add real credentials, tokens, cookies, or `.dsh` auth files.
2. Never add real project `runs/` data or transcripts.
3. Keep absolute personal paths out of docs and examples; use `$REPO_ROOT` or relative paths.
4. Do not change `sctg-kit/` gate semantics without a test.
5. Run `make test` before proposing changes.
6. For OpenRig changes, run the render dry-run and bridge doctor smoke.

## Clarification gate for automated multi-round runs

For a complete multi-round automated flow, ask all material clarifying
questions once before the run starts (layer, rounds-vs-steps, output/acceptance,
irreversible actions, budget). After the run starts, do not ask the user
anything: use documented defaults, record assumptions in `DECISIONS.md` or
`STATUS`, and write `BLOCKED`/`NEED_MAIN` if a decision is required.
