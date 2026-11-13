# BASELINE — refactor-decompose

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M2` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `research@1.0.0, diff@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

在代码仓/文档集/资产的结构重整前，先完成 100% 清点、唯一归属、冻结基线与门禁基线，再按波次保持行为不变地执行。

## 2. 特点

- 清点覆盖 100%，每个对象有唯一归属；不允许“未分类”被静默吞掉。
- 先冻结接口/行为/门禁基线，再 refactor；old→new 映射可机械核验。
- 按分区/波次推进，一片一 owner；行为变更与结构变更分开。
- 必须准备回滚；默认不改对象语义，只改结构。

## 3. 默认管线（原子轮型组合）

1. research/diff/architecture：清点、分区、唯一归属、冻结基线
2. optimize：分区波次重整，行为不变
3. verify：门禁与语义回归 + 回滚核验

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- 清点表：path → partition → owner → old→new
- 冻结基线 hash + 门禁基线 + 回滚脚本/清单
- 分区覆盖对账与最终 diff 统计；未处置项必须有去向

## 6. 特化重点参考（现有 template/run）

- `60-外部仓库:research-decompose`
- `templates/specialized/openrig-local-refit`
- `obsidian-localization:nutstore-refactor-prep`
- `obsidian-localization:nutstore-sandbox-refactor`
- `60-外部仓库:lingshu-code-reorg`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/refactor-decompose@1.0.0`；`contracts: research@1.0.0, diff@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 中高：代表 run 仍有 plan-ready；模板重、周期长，必须限制批次与预算。
- 当前标记：**M2**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
