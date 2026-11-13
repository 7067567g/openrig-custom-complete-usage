**English** | [简体中文](VALIDATION.zh-CN.md)

# Validation — 2026-11-13

Environment:

- repository: `openrig-custom-complete-usage`
- Python: 3.12 (workflow-group venv)
- OpenRig CLI: local `rig` 0.1.4
- no live seats launched for this validation; this is a spec/render/bridge check

## Test suite

```text
154 passed, 1 skipped
```

## Twelve OpenRig render rounds

Rendered twelve independent bundles:

```text
smoke-001 ... smoke-012
daemon ports 47901 ... 47912
```

Each of the 12 rounds:

- `render_master.py` exit 0;
- `OPENRIG-BRIDGE.json` schemaVersion=2;
- `openrig_bridge.py doctor` => `PASS`;
- seat map had 5 seats: main, pmo, tdo_opencode, tdo_dsh, qa.

## OpenRig spec validation

```text
12/12 rounds: workflow validate => ok=true
Each: 7 steps
Warnings: declared_not_enforced_v1 + role_no_live_preferred_target
```

The warnings are expected because no live rig was launched. They are not render
or schema failures.

## Launch plan

```text
12/12 rounds: rig up --plan => status=planned
Each: 5 seats resolved
Warnings: permission_policy absent; launch_posture=floor
```

## What is not claimed

- No live 5-seat execution was performed.
- No model token/cost measurement is claimed.
- No hybrid E2E pass is claimed.
- Live launch requires configured OpenCode/DSH seats and an isolated `OPENRIG_HOME`.

## 12-round workflow cases

Three cases were generated with the real `wf.py` state machine:

```text
case-12-rounds-hardening  12 rounds  closed
case-12-rounds-release    12 rounds  closed
case-12-rounds-docs       12 rounds  closed
```

Each has 12 STATUS files, 12 round decisions, a terminal decision, evidence
logs, `ROUNDS.md`, and `ROUNDS.json`. See `examples/round-cases/`.
