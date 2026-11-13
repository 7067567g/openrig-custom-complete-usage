**English** | [简体中文](OPENRIG.zh-CN.md)

# OpenRig integration

## Preflight

Inject mandatory rules into a seat workspace:

```bash
python3 scripts/openrig_preflight.py --json --no-monitor
python3 scripts/openrig_preflight.py \
  --run-id demo-001 --rig openrig-demo-001 --seat control-main@openrig-demo-001 \
  --workspace /tmp/seat-workspace --no-monitor --json
```

`--no-monitor` is the default-safe public path. A monitor can be enabled with
`OPENRIG_MONITOR_TARGETS`, `OPENRIG_MONITOR_URL`, and optionally
`OPENRIG_MONITOR_SERVICE`.

## Render

```bash
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-001 \
  --project-root /tmp/demo-project \
  --output-dir runs/demo-001/openrig
```

## Bridge

```bash
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor --run-dir runs/demo-001
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py status --run-dir runs/demo-001
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py capture --run-dir runs/demo-001
```

## Hard rules

- unique rig name / workflow id;
- isolated `OPENRIG_HOME` and daemon port;
- no direct SQLite/queue mutation;
- archive before teardown;
- never use a fresh seat as a fake resume.
