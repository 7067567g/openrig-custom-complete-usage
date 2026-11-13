**English** | [简体中文](01-render-smoke.zh-CN.md)

# Case 01 — Render and bridge smoke (12 rounds)

## Question

Can the complete usage repository generate consistent OpenRig bundles across
repeated runs without leaking test/oracle state or hand-editing generated files?

## Method

For 12 rounds:

1. render a unique run id and daemon port;
2. run `openrig_bridge.py doctor`;
3. run `rig workflow validate`;
4. run `rig up --plan`.

## Result

```text
12/12 render                 PASS
12/12 bridge doctor          PASS
12/12 workflow validate      ok=true (7 steps, expected warnings)
12/12 rig up --plan          status=planned (5 seats resolved)
```

## What it proves

- The template renderer is deterministic for the same inputs.
- The bridge schema is stable across run ids/ports.
- The workflow spec is accepted by the local OpenRig CLI.
- No live seat is required for this layer.

## What it does not prove

- Live model quality or token/cost.
- Seat readiness or transcript delivery.
- A live 5-seat E2E pass.

See `VALIDATION.md` and `reports/openrig_smoke.md`.
