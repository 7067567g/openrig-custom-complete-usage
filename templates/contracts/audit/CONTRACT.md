# CONTRACT — audit@1.0.0（全量审核、机械重整与复盘）

> **状态：frozen**。属于 `atomic-contract-set@1.0.0`，建立在 `workflow-group-base@1.0.0` 之上。
> 本契约只定义接口，不规定具体 WS 切分、模型、工具或领域路径；这些由 run 的 `SPEC.md` / `ROUND-PLAN.md` 特化。
> 不可覆盖的四条通用约束仍然有效：文档即接口、单一写者、STATUS 加锁逐条提交、分歧不落地。

## purpose

对一个周期/对象做全量审核，逐条处置发现，执行可机械验证的重整，并产出 RETRO 与下一周期输入。

## requires（必读输入）

- 本周期全部 run/证据
- 能力地图/取舍表/backlog
- 对象仓可写边界（若包含重整）
- 基线门禁与回滚路径

## produces（必产文件 + schema）

- `reports/AUDIT-*.md`：按域的全量审核结论
- `reports/REFACTOR-PLAN.md`：文件级重整清单 + old→new 映射 + 回滚
- `reports/CLOSEOUT.md`：周期收口、未决项 owner/去向
- `reports/RETRO.md`：失败模式、指标、下一周期菜单建议
- `reports/VERDICT.md`：CONTINUE / ADJUST / STOP

## mandatory_gates（强制门）

- 发现 100% 处置：改/合/降/观/排除；禁止只记不改或“下一 run”。
- 重整必须可机械验证：old→new 映射、grep/链接断言、回滚。
- 门禁不得低于基线；版本与发布事实按项目规则记录。
- 已知游离项必须有 owner + 去向 + 最晚复核轮。

## hard_boundaries（硬边界）

- 不借审计扩大对象范围。
- 不在无回滚/无基线的情况下做结构重整。
- 不把 RETRO 写成无行动建议的总结。

## budget_defaults

默认 TDO ≤6；单轮 ≤2h；重整批次 ≤3；审计覆盖 100%。

## done（完成定义）

AUDIT×N + REFACTOR-PLAN + CLOSEOUT + RETRO + VERDICT 落盘；PLAN-GATE 7/7；QA 通过。

## handoff（交接）

RETRO + CLOSEOUT + 更新后的路线输入 → 下一周期 strategy。

## domain_adapter_hooks

领域 adapter 负责审核维度、可机械重整范围、发布规则和“发现取舍”分类。

## plan_gate / verdict

- 执行前必须通过 `templates/contracts/_shared/PLAN-GATE.md` 的 7/7。
- 每轮结束由 MAIN 写 `reports/VERDICT.md`（`CONTINUE | ADJUST | STOP`）；规则见 `_shared/VERDICT.md`。
- 如果本类型是该 run 的最后一轮，VERDICT 与 DONE/BLOCKED 必须同时存在。
