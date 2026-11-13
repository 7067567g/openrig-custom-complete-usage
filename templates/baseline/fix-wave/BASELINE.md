# BASELINE — fix-wave

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M3` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `audit@1.0.0, optimize@1.0.0, verify@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

把已有审计票源/缺陷清单变成批量、可回归、可门禁化的修复成果，而不是“改完文件就算完成”。

## 2. 特点

- 每条票必须先有失败/复现证据，再修订，再复跑，最后进入门禁。
- 一 WS 一域/一文件边界；全内容覆盖，不抽样。
- 每个修复必须带回归或反例；门禁不得低于基线。
- 票源去向必须闭合：修复/合并/降级/排除各有 owner 和证据。

## 3. 默认管线（原子轮型组合）

1. audit：核验票源、确认可复现与优先级
2. optimize：按票修订并补回归
3. verify：独立复跑与门禁化确认

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- 每票的失败命令/输出 → 修订路径 → 复跑输出 → 门禁步骤
- 反例或变异必须点红；否则判假守卫
- reports/VERIFY.md + 最终 DoD；关票状态与证据一一对应

## 6. 特化重点参考（现有 template/run）

- `templates/specialized/kb-fix-wave`
- `templates/specialized/geophysics-correctness`
- `templates/specialized/project-freeze-facts`
- `obsidian-localization:nutstore-cache-fix`
- `obsidian-localization:nutstore-tools-wave1`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/fix-wave@1.0.0`；`contracts: audit@1.0.0, optimize@1.0.0, verify@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 中高：可能跨仓、改测试/门禁；必须保留“不能为绿删测试”的负向门。
- 当前标记：**M3**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
