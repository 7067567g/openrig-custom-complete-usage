# CONTRACT — diff@1.0.0（逐项差异与横向矩阵）

> **状态：frozen**。属于 `atomic-contract-set@1.0.0`，建立在 `workflow-group-base@1.0.0` 之上。
> 本契约只定义接口，不规定具体 WS 切分、模型、工具或领域路径；这些由 run 的 `SPEC.md` / `ROUND-PLAN.md` 特化。
> 不可覆盖的四条通用约束仍然有效：文档即接口、单一写者、STATUS 加锁逐条提交、分歧不落地。

## purpose

把候选落到文件/函数/能力级的差异，并做多对象横向矩阵，为取舍和实施提供可比较证据。

## requires（必读输入）

- `reports/CANDIDATES.md` 或等价候选输入
- 1–3 个只读参考对象
- 统一比较维度与口径
- 写权限边界（本类型默认只读）

## produces（必产文件 + schema）

- `reports/DIFF-LEDGER.md`：对象/参考的 path:line、状态、gap、effort、risk
- `reports/BENCHMARK-MATRIX.md`：≥3 对象 × 统一维度矩阵；空格必须标 gap
- `reports/DIFF-SUMMARY.md`：取舍建议（≤3 条）

## mandatory_gates（强制门）

- DIFF-LEDGER 每行至少有对象侧与参考侧 path:line；缺失须显式标 gap。
- 矩阵维度先冻结、逐格有证据或 gap；禁止留空。
- 只读，不写业务代码、不 push。
- 结论不得超出矩阵与差分证据。

## hard_boundaries（硬边界）

- 不修改研究对象。
- 不把单对象评审伪装成横向比对。
- 不引用未版本锚定的上游状态。

## budget_defaults

默认 TDO ≤4；单轮 ≤2h；比较对象 1–3；矩阵维度由领域 adapter 声明。

## done（完成定义）

DIFF-LEDGER + BENCHMARK-MATRIX + DIFF-SUMMARY 落盘；PLAN-GATE 7/7；QA 通过；若为最后一轮则写 VERDICT。

## handoff（交接）

DIFF-LEDGER + BENCHMARK-MATRIX → strategy / architecture / optimize。

## domain_adapter_hooks

领域 adapter 提供对象路径、参考仓、矩阵维度和上游 commit/version 锚。

## plan_gate / verdict

- 执行前必须通过 `templates/contracts/_shared/PLAN-GATE.md` 的 7/7。
- 每轮结束由 MAIN 写 `reports/VERDICT.md`（`CONTINUE | ADJUST | STOP`）；规则见 `_shared/VERDICT.md`。
- 如果本类型是该 run 的最后一轮，VERDICT 与 DONE/BLOCKED 必须同时存在。
