# Reproducibility

## Deterministic

- template rendering for the same inputs and master version;
- `OPENRIG-BRIDGE.json` schema and bundle-relative paths;
- `doc_consistency.py --check`;
- workflow/adapter tests;
- repository hygiene checks.

## Non-deterministic

- live model output and token/cost usage;
- seat readiness and timing;
- OpenRig daemon/session state.

SCTG does not claim deterministic model output. It claims reproducible
transactions: card, submission, gate result, evidence hashes, decision records,
and a bridge that maps control-plane facts to execution-plane artifacts.
