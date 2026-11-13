[English](MULTI-ROUND.md) | **简体中文**
> 本文只讲 workflow-group 的 round。OpenRig 的 step/packet 和单线路径见 [`OPENRIG-WORKFLOW-GUIDE.zh-CN.md`](OPENRIG-WORKFLOW-GUIDE.zh-CN.md)。


# 多轮工作流

## 角色

- **MAIN**：委派、收账、拍板、关闭；不写 TDO/QA 内容。
- **PMO**：拥有 `PROJECT.md`：目标、范围、指标、工作包、轮次总结。
- **TDO**：拥有 `STATUS-Round-n.md`：进度、证据、阻塞；写前先领锁。
- **QA**：拥有 `ISSUES.xlsx`：问题、严重度、是否需决策。
- **SAFETY**：可选，独立复核失败/破坏性动作。

## 轮次循环

```text
new-run
  -> PMO 计划
  -> brief TDO
  -> TDO 执行 + append STATUS
  -> QA 复核 + ISSUES
  -> PMO 收轮 + PROJECT §6
  -> MAIN 读 §6，写 DECISIONS
  -> new-round
```

## 状态迁移

```bash
python3 scripts/wf.py state <run-id> STATUS qa-pending --by main
python3 scripts/wf.py state <run-id> STATUS qa-done --by qa
python3 scripts/wf.py state <run-id> PROJECT waiting-main --by pmo
```

## 锁

```bash
python3 scripts/wf.py lock <run-id>
# 追加一条 STATUS
python3 scripts/wf.py unlock <run-id>
```

## 关闭

```bash
python3 scripts/wf_close_lint.py --run <run-id>
# ERROR 必须为 0
python3 scripts/wf.py state <run-id> PROJECT closed --by main
```
