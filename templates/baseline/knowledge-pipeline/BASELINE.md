# BASELINE — knowledge-pipeline

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M3` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `research@1.0.0, optimize@1.0.0, verify@1.0.0, audit@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

把知识从来源整理到 canonical，再到可检索、可度量、可被真实任务消费，并把实战反馈回写知识库。

## 2. 特点

- 来源→canonical→视图/检索→消费日志是一条链，不能用“文档已写”代替“已被消费”。
- 全内容覆盖：每篇/每条待入库材料有采用/取代/桥接/不动的处置。
- 检索需要有金问题/阈值/命中率；接口/投影门禁用反例。
- 知识消费必须记录真实查询/真实任务，不得用维护性 grep 冒充。

## 3. 默认管线（原子轮型组合）

1. research/audit：来源盘点、欠账/断言/检索基线
2. optimize：入库、接口、别名、消费闭环
3. verify：命中率、投影门禁、真实查询日志、validate/genviews

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- 来源处置表 + canonical 落点
- hit@1/2/3 或其它可复算指标 + 命令/输出
- router/frontmatter/视图门禁反例与通过证据
- 真实查询日志 ≥阈值，不能由维护性 grep 次数填充

## 6. 特化重点参考（现有 template/run）

- `templates/specialized/kb-debt-burn`
- `templates/specialized/kb-consume-interface`
- `templates/specialized/kb-method-action`
- `templates/specialized/kb-claim-verify`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/knowledge-pipeline@1.0.0`；`contracts: research@1.0.0, optimize@1.0.0, verify@1.0.0, audit@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 中：可能触碰 KB 正式域；每次豁免需显式记录并限制写权限。
- 当前标记：**M3**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
