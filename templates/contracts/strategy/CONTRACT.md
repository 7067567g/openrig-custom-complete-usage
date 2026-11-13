# CONTRACT — strategy@1.0.0（方向/取舍/目标组合）

> **状态：frozen**。属于 `atomic-contract-set@1.0.0`，建立在 `workflow-group-base@1.0.0` 之上。
> 本契约只定义接口，不规定具体 WS 切分、模型、工具或领域路径；这些由 run 的 `SPEC.md` / `ROUND-PLAN.md` 特化。
> 不可覆盖的四条通用约束仍然有效：文档即接口、单一写者、STATUS 加锁逐条提交、分歧不落地。

## purpose

把项目目标收敛成 ≤3 个有证据的目标组合，明确取舍、预算和 NOT-DOING，为后续 research/diff/architecture/optimize 提供输入。

## requires（必读输入）

- 项目目标与范围（PROJECT.md §1–§2）
- 已有 audit/RETRO/backlog（若有）
- 已有 TRADEOFF / CAPABILITY-MAP / 方向文件（若有）
- 本轮 baseline 与领域 adapter 的指标口径

## produces（必产文件 + schema）

- `reports/STRATEGY.md`：方向结论、候选目标、取舍理由
- `reports/TRADEOFF.md`：候选 × evidence/impact/cost/risk/fit/decision
- `reports/CYCLE-PLAN.md`：轮次菜单、预算、NOT-DOING
- `reports/VERDICT.md`：CONTINUE / ADJUST / STOP（若本类型是最后一轮）

## mandatory_gates（强制门）

- ≥3 个候选有来源/证据；最终入选 ≤3 个目标。
- 每个候选有 evidence / impact / cost / risk / fit / decision 六字段。
- CYCLE-PLAN 含预算、NOT-DOING、依赖与终止判据。
- 本契约默认只读，不写代码；若要实施必须交给 optimize。

## hard_boundaries（硬边界）

- 不自行扩大项目目标或写权限。
- 不把未验证的候选写成已选目标。
- 不越过 baseline/领域 SPEC 的硬边界。

## budget_defaults

默认 TDO ≤4；单轮 ≤2h；原子轮次只输出决策素材，不承担实施。

## done（完成定义）

STRATEGY + TRADEOFF + CYCLE-PLAN 落盘；PLAN-GATE 7/7；QA 已核对；若为最后一轮则写 VERDICT。

## handoff（交接）

TRADEOFF + CYCLE-PLAN → research / diff / architecture / optimize。

## domain_adapter_hooks

领域 adapter 负责填候选来源、指标阈值和风险白名单；契约不写领域路径。

## plan_gate / verdict

- 执行前必须通过 `templates/contracts/_shared/PLAN-GATE.md` 的 7/7。
- 每轮结束由 MAIN 写 `reports/VERDICT.md`（`CONTINUE | ADJUST | STOP`）；规则见 `_shared/VERDICT.md`。
- 如果本类型是该 run 的最后一轮，VERDICT 与 DONE/BLOCKED 必须同时存在。
