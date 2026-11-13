[English](OPENRIG.md) | **简体中文**

# OpenRig 集成

## Preflight

```bash
python3 scripts/openrig_preflight.py --json --no-monitor
python3 scripts/openrig_preflight.py \
  --run-id demo-001 --rig openrig-demo-001 --seat control-main@openrig-demo-001 \
  --workspace /tmp/seat-workspace --no-monitor --json
```

公开路径默认使用 `--no-monitor`。如需监测台，配置
`OPENRIG_MONITOR_TARGETS`、`OPENRIG_MONITOR_URL`，可选
`OPENRIG_MONITOR_SERVICE`。

## 渲染

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

## 硬规则

- rig 名 / workflow id 唯一；
- 独立 `OPENRIG_HOME` 和 daemon 端口；
- 不直接改 SQLite/queue；
- 先归档再 teardown；
- 不用 fresh seat 冒充 resume。
