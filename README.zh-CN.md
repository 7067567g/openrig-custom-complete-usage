[English](README.md) | **简体中文**

# OpenRig Custom Complete Usage

**SCTG + workflow-group 多轮编排 + OpenRig 混合执行 的完整使用例。**

本仓库是 [`SCTG-public`](https://github.com/7067567g/SCTG-public) 的“完整用法”配套仓：

- `SCTG-public`：稳定的 reference kit（task card、gates、submission schema、ledger、最小示例）。
- 本仓库：操作层（roles、多轮状态机、templates、headless adapters、OpenRig preflight/render/bridge、端到端示例）。

## 文档

- **OpenRig + workflow 完整指引：** [`docs/OPENRIG-WORKFLOW-GUIDE.zh-CN.md`](docs/OPENRIG-WORKFLOW-GUIDE.zh-CN.md)
- **LLM 常见用户误读速查：** [`docs/LLM-MISREAD-QUICKREF.zh-CN.md`](docs/LLM-MISREAD-QUICKREF.zh-CN.md)
- **项目侧治理层**（总指挥部 / 总参谋部 / 单独轮 / 医护中心）：见主指引 §0.2。
- **脱敏过程档案：** [`process/README.md`](process/README.md)——OpenRig 实践如何演进、关键决策、踩坑、轮次记录、trace 与来源说明。
- **Benchmark 状态：** **因预算原因未跑**；见 [`process/BENCHMARK-STATUS.md`](process/BENCHMARK-STATUS.md)，不声称任何 benchmark 结果。
  - 默认说法：**“用 OpenRig 跑工作流。”** 最精确：**“用 OpenRig 执行 SCTG 工作流，单线跑。”**

- 中英双语索引：[`docs/INDEX.md`](docs/INDEX.md)
- 脱敏控制面样例：[`examples/sanitized-run/`](examples/sanitized-run/)
- 内存安全与 cgroup 限制：[`docs/MEMORY-SAFETY.zh-CN.md`](docs/MEMORY-SAFETY.zh-CN.md)
- 验证记录：[`VALIDATION.zh-CN.md`](VALIDATION.zh-CN.md)

## 快速开始

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt

make check
make test
make render-dry
```

## 本地多轮

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

## OpenRig 渲染

```bash
mkdir -p /tmp/demo-project

python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-001 \
  --project-root /tmp/demo-project \
  --output-dir runs/demo-001/openrig \
  --opencode-model deepseek/deepseek-flash \
  --dsh-profile headless

python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor \
  --run-dir runs/demo-001
```

## 验证

- 142 workflow/adapter tests；
- `doc_consistency` 0 error；
- 12 轮 OpenRig render + bridge doctor + workflow validate + rig up --plan 全部 PASS。

详见 [`VALIDATION.md`](VALIDATION.md)、[`docs/INDEX.md`](docs/INDEX.md) 和 [`examples/sanitized-run`](examples/sanitized-run/)。
