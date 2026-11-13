# CONTRACT — architecture@1.0.0（架构评估与能力地图）

> **状态：frozen**。属于 `atomic-contract-set@1.0.0`，建立在 `workflow-group-base@1.0.0` 之上。
> 本契约只定义接口，不规定具体 WS 切分、模型、工具或领域路径；这些由 run 的 `SPEC.md` / `ROUND-PLAN.md` 特化。
> 不可覆盖的四条通用约束仍然有效：文档即接口、单一写者、STATUS 加锁逐条提交、分歧不落地。

## purpose

评估边界、耦合、数据流、扩展点和上游同步成本，形成能力地图与核心缺口排名。

## requires（必读输入）

- `reports/DIFF-LEDGER.md` / `BENCHMARK-MATRIX.md`（或声明替代）
- 能力地图/取舍表（若有）
- 目标对象的版本锚与只读快照

## produces（必产文件 + schema）

- `reports/ARCH-ASSESSMENT.md`：边界/耦合/数据流/扩展点/上游成本，逐条证据+处置
- `reports/CAPABILITY-MAP.md`：核心/外围能力地图、baseline parity、特化深度
- `reports/GAP-SCORE.md`：评分口径、核心缺口 Top、下一轮建议

## mandatory_gates（强制门）

- 领域 adapter 声明的核心维度必须全覆盖；每格有结论+证据。
- 每条发现四字段：结论/证据/处置/去向。
- 默认只读，不写代码；若提出实施项必须进入 backlog 或 optimize。
- 架构结论必须带版本锚；不能把文档愿望当现状。

## hard_boundaries（硬边界）

- 不通过架构评估顺手重构。
- 不把外围增强伪装成核心缺口。
- 不越过对象仓只读边界。

## budget_defaults

默认 TDO ≤4；单轮 ≤2h；核心维度由领域 adapter 预先声明。

## done（完成定义）

ARCH-ASSESSMENT + CAPABILITY-MAP + GAP-SCORE 落盘；PLAN-GATE 7/7；QA 通过；若为最后一轮则写 VERDICT。

## handoff（交接）

ARCH-ASSESSMENT + CAPABILITY-MAP + GAP-SCORE → strategy / optimize。

## domain_adapter_hooks

领域 adapter 负责核心维度清单、parity 基准和版本锚。

## plan_gate / verdict

- 执行前必须通过 `templates/contracts/_shared/PLAN-GATE.md` 的 7/7。
- 每轮结束由 MAIN 写 `reports/VERDICT.md`（`CONTINUE | ADJUST | STOP`）；规则见 `_shared/VERDICT.md`。
- 如果本类型是该 run 的最后一轮，VERDICT 与 DONE/BLOCKED 必须同时存在。
