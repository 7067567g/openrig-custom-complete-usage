# CONTRACT — research@1.0.0（研究与对标/候选产出）

> **状态：frozen**。属于 `atomic-contract-set@1.0.0`，建立在 `workflow-group-base@1.0.0` 之上。
> 本契约只定义接口，不规定具体 WS 切分、模型、工具或领域路径；这些由 run 的 `SPEC.md` / `ROUND-PLAN.md` 特化。
> 不可覆盖的四条通用约束仍然有效：文档即接口、单一写者、STATUS 加锁逐条提交、分歧不落地。

## purpose

在方向与取舍约束下做只读取证和对标，产出有证据的候选目标与 backlog。

## requires（必读输入）

- `reports/CYCLE-PLAN.md` 或等价方向输入
- `reports/TRADEOFF.md`（或声明替代）
- 指定的研究对象/参考仓/issue 源；只读
- 上轮 backlog

## produces（必产文件 + schema）

- `reports/RESEARCH.md`：研究总述与结论
- `reports/CANDIDATES.md`：≤3 个候选，每个含做什么/为什么/验收/成本/风险
- `reports/BACKLOG.md`：未入选候选，必须有 owner/去向/最晚复核轮
- `reports/SOURCES.md`：来源、时间窗、命令/证据

## mandatory_gates（强制门）

- 每个候选五字段齐全且验收可判定。
- backlog 逐条有 owner、去向、最晚复核轮，禁止写“下一 run”。
- 关键结论有 source/path/command 之一；不得用二手摘要冒充一手证据。
- 默认只读；不写业务代码、不改对象仓。

## hard_boundaries（硬边界）

- 不把研究结论直接当实施授权。
- 不越过只读边界；需要写入时转 optimize / baseline 复合流程。
- 不收录无法核实的来源或伪造引用。

## budget_defaults

默认 TDO ≤4；单轮 ≤2h；候选 ≤3；来源门槛由领域 adapter 声明。

## done（完成定义）

RESEARCH + CANDIDATES + BACKLOG + SOURCES 落盘；PLAN-GATE 7/7；QA 通过；若为最后一轮则写 VERDICT。

## handoff（交接）

CANDIDATES + BACKLOG → diff / architecture / optimize。

## domain_adapter_hooks

领域 adapter 负责来源清单、来源最小数、参考对象和不可触碰边界。

## plan_gate / verdict

- 执行前必须通过 `templates/contracts/_shared/PLAN-GATE.md` 的 7/7。
- 每轮结束由 MAIN 写 `reports/VERDICT.md`（`CONTINUE | ADJUST | STOP`）；规则见 `_shared/VERDICT.md`。
- 如果本类型是该 run 的最后一轮，VERDICT 与 DONE/BLOCKED 必须同时存在。
