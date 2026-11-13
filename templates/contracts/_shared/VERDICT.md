# VERDICT — 每轮判词（MAIN 写）

> 写者：主会话（MAIN）。读者：下一轮/loop supervisor/审计。每轮结束必须写；用户保留最高 STOP/PAUSED 权限。

```text
# VERDICT — <RUN-ID> / <ROUND-ID>
decision: CONTINUE | ADJUST | STOP
rationale: <一句话：为什么>
next: <下一轮 run-id 或按 baseline 的下一原子轮型>
contracts_used: <type@version,...>
budget: used=<目标数>/<上限>; tokens=<若可采集>; time=<分钟>
queue_patch: none | <add:...; remove:...; reorder:...>
open_items: <owner + 去向 + 最晚复核轮；无则 none>
notes: <给下一轮的输入/风险>
```

## 规则

- `CONTINUE`：按 plan 或 baseline 默认管线进入下一轮。
- `ADJUST`：只在预算内调整下一轮菜单/目标；`queue_patch` 必须写增删改。
- `STOP`：写 `LOOPS-STOPPED` 或等价终止标记并写明关闭收口；用户可随时覆盖为 `PAUSED`/`STOP`。
- MAIN 不能把未验证项写成通过；不能省略 open_items 的 owner/去向。
- VERDICT 是流程判词，不是四件套之外的第五份台账；证据仍在 STATUS/ISSUES/DECISIONS/证据目录。
