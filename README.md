**English** | [简体中文](README.zh-CN.md)

# OpenRig Custom Complete Usage

**A complete, runnable example of SCTG + workflow-group multi-round orchestration + OpenRig hybrid execution.**

This repository is the "full usage" companion to the distilled
[`SCTG-public`](https://github.com/7067567g/SCTG-public) reference kit:

- `SCTG-public` = the small, stable kit: task card, gates, submission schema, ledger, minimal examples.
- **this repository** = the operational layer: roles, multi-round state machine, templates, headless adapters, OpenRig preflight/render/bridge, and end-to-end examples.

> Status: release candidate. 154 workflow/adapter tests pass; twelve independent OpenRig
> bundles passed render + bridge doctor + `rig workflow validate` + `rig up --plan`.
> No live 5-seat execution is claimed yet; see [`VALIDATION.md`](VALIDATION.md).

## What is inside

```text
WORKFLOW.md                         canonical multi-round workflow
roles/                              MAIN / PMO / TDO / QA / SAFETY contracts
templates/                          four-layer templates + OpenRig hybrid master
scripts/wf.py                       run / round / state / lock / brief / doctor / serve
scripts/adapters/headless.py        OpenCode v2 and DSH headless adapter
scripts/openrig_preflight.py        inject mandatory preflight into a seat workspace
scripts/wf_close_lint.py            close-semantics linter
scripts/doc_consistency.py          template/index/reference consistency checker
sctg-kit/                           SCTG reference kit (gates, schema, ledger, decision)
examples/                           local multi-round, SCTG minimal, OpenRig minimal
docs/                               quickstart, architecture, multi-round, publishing
tests/                              workflow and adapter tests
```

## Quick start

### 1. Install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2. Run the local multi-round workflow

```bash
python3 scripts/wf.py new-run demo-001 \
  --template templates/specialized/openrig-workflow-master \
  --goal "Build a tiny, verifiable feature" \
  --project-root "$PWD" \
  --scope 'runs/demo-001/**' \
  --tdo 1

python3 scripts/wf.py brief --role pmo --run demo-001
python3 scripts/wf.py doctor demo-001
```

This creates the four-document control surface:

```text
runs/demo-001/
  PROJECT.md
  DECISIONS.md
  STATUS-Round-1.md
  ISSUES.xlsx
  SPEC.md
  .locks/
```

The normal round loop is:

```text
PMO plan -> TDO execute -> QA review -> PMO close -> MAIN decision -> new-round
```

See [`docs/MULTI-ROUND.md`](docs/MULTI-ROUND.md). Full bilingual index: [`docs/INDEX.md`](docs/INDEX.md).

### 3. Render an OpenRig bundle

```bash
mkdir -p /tmp/demo-project

python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-001 \
  --project-root /tmp/demo-project \
  --output-dir runs/demo-001/openrig \
  --opencode-model deepseek/deepseek-flash \
  --dsh-profile headless
```

Generated files:

```text
runs/demo-001/openrig/
  rig.yaml
  workflow.yaml
  agents/worker/agent.yaml
  guidance/team.md
  OPENRIG-BRIDGE.json
```

### 4. Start the hybrid rig (requires OpenRig)

```bash
export OPENRIG_HOME=/tmp/openrig-workflow-demo-001
rig daemon start --no-kernel --port 47890
rig up runs/demo-001/openrig/rig.yaml \
  --cwd /tmp/demo-project --non-interruptive --yes --json
rig workflow validate runs/demo-001/openrig/workflow.yaml --json
rig workflow instantiate runs/demo-001/openrig/workflow.yaml \
  --root-objective 'Execute run demo-001' \
  --created-by control-main@openrig-demo-001 --json
```

Check the bridge before/after launch:

```bash
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor \
  --run-dir runs/demo-001
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py status \
  --run-dir runs/demo-001
```

### 5. Test

```bash
make test
```

## Documentation

- Bilingual index: [`docs/INDEX.md`](docs/INDEX.md)
- Sanitized control-plane sample: [`examples/sanitized-run/`](examples/sanitized-run/)
- Three complete 12-round workflow cases: [`examples/round-cases/`](examples/round-cases/)
- Validation report: [`VALIDATION.md`](VALIDATION.md)

## Three execution modes

| Mode | What runs | Use when |
|---|---|---|
| `local-only` | workflow documents + gates only | planning, review, static validation |
| `hybrid` | workflow-group control plane + OpenRig seats | real multi-agent execution |
| `attached` | reuse an existing OpenRig daemon/rig | explicitly requested only |

Never write a `local-only` result as a real hybrid E2E pass.

## Two-repository policy

- **`SCTG-public`** — stable reference kit, minimal examples, public case studies.
- **`openrig-custom-complete-usage`** — complete operational usage, OpenRig integration, multi-round scripts, benchmark harness.

See [`docs/PUBLISHING.md`](docs/PUBLISHING.md) for what is intentionally excluded
(secrets, real run data, personal paths, internal dashboard configs).

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
