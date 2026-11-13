# Architecture

## Two planes

```text
Control plane (workflow-group)
  PROJECT / SPEC / DECISIONS / STATUS / ISSUES
  roles: MAIN, PMO, TDO, QA, SAFETY
  wf.py: state, locks, briefs, rounds, close lint

Execution plane (OpenRig)
  rig / seats / queue / workflow / transcripts / snapshots
  render_master.py -> rig.yaml + workflow.yaml + bridge
  openrig_bridge.py -> doctor / status / capture
```

## Authority

| Fact | Authority |
|---|---|
| Goal, scope, acceptance | control plane |
| Decisions, budget, permissions | control plane |
| Live seat/queue/workflow state | OpenRig |
| Packet delivery / transcript | OpenRig |
| Evidence pointers | both, via bridge + evidence paths |

The two planes are mapped by `OPENRIG-BRIDGE.json`. Neither side silently
overwrites the other.

## Execution modes

- **local-only** — no OpenRig; documents and gates only.
- **hybrid** — render bundle, start isolated OpenRig home/daemon, launch seats,
  instantiate workflow, execute, close, archive.
- **attached** — reuse an existing daemon/rig only when explicitly requested.

## Hard gates

- Unique rig name and workflow id.
- Isolated `OPENRIG_HOME` and daemon port.
- One writer per write scope.
- Snapshot/rollback before changing live state.
- Archive before teardown (`MANIFEST.json.archiveStatus == "COMPLETE"`).
- Never turn a local-only pass into a hybrid E2E claim.
