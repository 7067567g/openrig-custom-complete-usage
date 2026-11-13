[English](README.md) | **简体中文**

# 多轮示例

```bash
python3 scripts/wf.py new-run demo-rounds \
  --template templates/specialized/openrig-workflow-master \
  --goal "Run three document-driven rounds" \
  --project-root "$PWD" \
  --scope 'runs/demo-rounds/**' \
  --tdo 1

python3 scripts/wf.py brief --role pmo --run demo-rounds
python3 scripts/wf.py doctor demo-rounds
```

然后按 `docs/MULTI-ROUND.zh-CN.md`：

```text
PMO 计划 -> TDO 执行 -> QA 复核 -> PMO 收轮 -> MAIN 决策 -> new-round
```
