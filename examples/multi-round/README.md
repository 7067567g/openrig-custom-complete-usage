**English** | [简体中文](README.zh-CN.md)

# Multi-round example

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

Then follow `docs/MULTI-ROUND.md`:

```text
PMO plan -> TDO execute -> QA review -> PMO close -> MAIN decision -> new-round
```
