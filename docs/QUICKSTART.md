# Quickstart

## 0. Environment

- Python 3.12+
- Node.js 24 (for OpenCode/OpenRig tooling)
- `rig` CLI (for hybrid mode)
- OpenCode and/or DSH installed for the selected seats

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
make test
```

## 1. Local-only workflow

```bash
python3 scripts/wf.py new-run demo-001 \
  --template templates/specialized/openrig-workflow-master \
  --goal "Build a tiny, verifiable feature" \
  --project-root "$PWD" \
  --scope 'runs/demo-001/**' \
  --tdo 1
python3 scripts/wf.py doctor demo-001
```

Use `brief` to produce role messages:

```bash
python3 scripts/wf.py brief --role pmo --run demo-001
python3 scripts/wf.py brief --role tdo --run demo-001 --agent tdo-a1
python3 scripts/wf.py brief --role qa --run demo-001
```

The round cycle is documented in `docs/MULTI-ROUND.md`.

## 2. Render OpenRig bundle

```bash
mkdir -p /tmp/demo-project
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-001 \
  --project-root /tmp/demo-project \
  --output-dir runs/demo-001/openrig \
  --opencode-model deepseek/deepseek-flash \
  --dsh-profile headless
```

## 3. Hybrid launch

```bash
export OPENRIG_HOME=/tmp/openrig-workflow-demo-001
rig daemon start --no-kernel --port 47890
rig up runs/demo-001/openrig/rig.yaml --cwd /tmp/demo-project --non-interruptive --yes --json
rig workflow validate runs/demo-001/openrig/workflow.yaml --json
rig workflow instantiate runs/demo-001/openrig/workflow.yaml \
  --root-objective 'Execute run demo-001' \
  --created-by control-main@openrig-demo-001 --json
```

## 4. Verify the bridge

```bash
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor --run-dir runs/demo-001
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py status --run-dir runs/demo-001
```

## 5. Close

Follow `templates/specialized/openrig-workflow-master/ENTRYPOINTS.md`:
archive first, then `rig workflow close/abort`, then `rig down`, then `rig daemon stop`.
