# BASELINE — postmortem-meta-governance

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M2` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `audit@1.0.0, strategy@1.0.0, optimize@1.0.0, verify@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

从完整运行记录、失败模式和角色冲突中提炼可执行规则、文档或模板改动，并验证回写有效。

## 2. 特点

- 数据先行：成本/轮次/失败率/开放项必须有可复核表或来源。
- 失败模式要能回到具体日志/文件/行，改进要有观察出处→改动文件/位置→改法。
- 治理变更需红队/影子验证；非规范文档必须标清边界。
- 至少 N 处有效回写（默认 ≥3），且不把“下一 run”当行动。

## 3. 默认管线（原子轮型组合）

1. audit：数据/失败模式/角色权责/开放项
2. strategy：决定改什么/不改什么/复杂度预算
3. optimize：写回规则或模板
4. verify：机械冒烟、影子验证、红队复核

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- 复盘数据表 + 失败模式清单（带日志/路径）
- 改进清单：观察→改动→验证
- 红队/影子验证报告；非规范边界声明

## 6. 特化重点参考（现有 template/run）

- `templates/specialized/burn-postmortem`
- `templates/specialized/wf-docs-distill`
- `runs/role-boundary-audit-20261015`
- `runs/so-necessity-research-20261015`
- `runs/master-adoption-20261015`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/postmortem-meta-governance@1.0.0`；`contracts: audit@1.0.0, strategy@1.0.0, optimize@1.0.0, verify@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 中：容易产出无证据建议或过度制度；必须控制规则复杂度预算。
- 当前标记：**M2**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
