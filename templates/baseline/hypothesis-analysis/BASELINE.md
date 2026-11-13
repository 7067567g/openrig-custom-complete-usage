# BASELINE — hypothesis-analysis

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M3` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `research@1.0.0, verify@1.0.0, audit@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

面对未知数据/字节/语义，不做“猜语义”，而是建立逐字段/逐项的假设矩阵、置信度与可证伪实验，并通过双分支 QA 汇合。

## 2. 特点

- 事实/推断/建议严格分层；不得把观察结构直接写成固件语义。
- 每个未解析项必须有偏移/长度/样本/候选含义/支持与反证/置信度/区分实验。
- 分支专属 QA + join；任何语义命名要有证据或保留未知。
- 源数据只读；结论用可复现实验而非“看起来像”。

## 3. 默认管线（原子轮型组合）

1. research：盘点未知项、分分支并做逐项差分实验
2. verify：分支 QA + join + 一致性复核
3. audit：最终矩阵、残余未知与下一轮探针排序

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- 逐项假设矩阵（offset/length/samples/candidates/evidence/confidence/test）
- 差分/实验命令与结果；事实 vs 假设分栏
- 分支 QA verdict + join 报告 + 残余未知清单

## 6. 特化重点参考（现有 template/run）

- `templates/specialized/openrig-unparsed-bytes-analysis`
- `runs/openrig-unparsed-bytes-20261020`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/hypothesis-analysis@1.0.0`；`contracts: research@1.0.0, verify@1.0.0, audit@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 中：容易过度声称语义/被样本误导；必须保留反证与可证伪实验。
- 当前标记：**M3**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
