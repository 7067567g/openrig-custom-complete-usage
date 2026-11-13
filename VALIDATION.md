# Validation — 2026-11-13

Environment:

- repository: `openrig-custom-complete-usage`
- Python: 3.12 (workflow-group venv)
- OpenRig CLI: local `rig` 0.1.4
- no live seats launched for this validation; this is a spec/render/bridge check

## Test suite

```text
142 passed, 1 skipped
```

## Three OpenRig render rounds

Rendered three independent bundles:

```text
demo-001  daemon port 47891
demo-002  daemon port 47892
demo-003  daemon port 47893
```

Each round:

- `render_master.py` exit 0;
- `OPENRIG-BRIDGE.json` schemaVersion=2;
- `openrig_bridge.py doctor --run-dir /tmp/demo-00N` => `PASS`;
- seat map had 5 seats: main, pmo, tdo_opencode, tdo_dsh, qa.

## OpenRig spec validation

```text
rig workflow validate /tmp/demo-001/openrig/workflow.yaml --json
=> ok=true
=> 7 steps
=> warnings: declared_not_enforced_v1 + role_no_live_preferred_target
```

The warnings are expected because no live rig was launched. They are not render
or schema failures.

## Launch plan

```text
rig up /tmp/demo-001/openrig/rig.yaml --cwd /tmp/openrig-project-1 --plan --json
=> status=planned
=> 5 seats resolved
=> warnings: permission_policy absent; launch_posture=floor
```

## What is not claimed

- No live 5-seat execution was performed.
- No model token/cost measurement is claimed.
- No hybrid E2E pass is claimed.
- Live launch requires configured OpenCode/DSH seats and an isolated `OPENRIG_HOME`.
