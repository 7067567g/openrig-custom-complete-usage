[English](QUICKSTART.md) | **简体中文**

# 快速开始

## 0. 环境

- Python 3.12+
- Node.js 24（OpenCode/OpenRig 工具链）
- `rig` CLI（hybrid 模式）
- 已配置的 OpenCode 和/或 DSH seat

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
make test
```

## 1. 本地多轮

```bash
python3 scripts/wf.py new-run demo-001 \
  --template templates/specialized/openrig-workflow-master \
  --goal "Build a tiny, verifiable feature" \
  --project-root "$PWD" \
  --scope 'runs/demo-001/**' \
  --tdo 1
python3 scripts/wf.py doctor demo-001
```

生成委派消息：

```bash
python3 scripts/wf.py brief --role pmo --run demo-001
python3 scripts/wf.py brief --role tdo --run demo-001 --agent tdo-a1
python3 scripts/wf.py brief --role qa --run demo-001
```

完整轮次循环见 `docs/MULTI-ROUND.zh-CN.md`。

## 2. 渲染 OpenRig bundle

```bash
mkdir -p /tmp/demo-project
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-001 \
  --project-root /tmp/demo-project \
  --output-dir runs/demo-001/openrig \
  --opencode-model deepseek/deepseek-flash \
  --dsh-profile headless
```

## 3. Hybrid 启动

```bash
export OPENRIG_HOME=/tmp/openrig-workflow-demo-001
rig daemon start --no-kernel --port 47890
rig up runs/demo-001/openrig/rig.yaml --cwd /tmp/demo-project --non-interruptive --yes --json
rig workflow validate runs/demo-001/openrig/workflow.yaml --json
rig workflow instantiate runs/demo-001/openrig/workflow.yaml \
  --root-objective 'Execute run demo-001' \
  --created-by control-main@openrig-demo-001 --json
```

## 4. 检查 bridge

```bash
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor --run-dir runs/demo-001
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py status --run-dir runs/demo-001
```

## 5. 收口

遵循 `templates/specialized/openrig-workflow-master/ENTRYPOINTS.md`：
先归档，再 `rig workflow close/abort`，再 `rig down`，最后 `rig daemon stop`。
