# BASELINE — safe-cleanup

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M3` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `audit@1.0.0, optimize@1.0.0, verify@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

对真实文件系统做可回滚整理/迁移：默认拒绝、move-only、一次一个 action、独立 SAFETY 逐条审核、red 人工批准。

## 2. 特点

- 动作必须结构化（mkdir/move; Windows 仅此二类），禁止 shell 通配符、delete、copy、exec、purge 作为默认路径。
- 每个 action 绑定 digest；改动即失效，必须重新 propose。
- POSIX 与 Windows 后端分开：POSIX 走 hdrive_gate.py，Windows 走 scripts/windows/hgate.py，语义相同、路径/op 能力不同。
- 整理前全量清单、protected manifest、move-ledger、前后差异、回滚路径齐全；失败即停。

## 3. 默认管线（原子轮型组合）

1. audit：只读预检、全量盘点、protected 审核
2. optimize：处置计划→gate→逐条 SAFETY→人工批准→一次一个执行
3. verify：QA 核对账本/前后清单/回滚/无越界

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- inventory 100% + item→action 映射
- actions/gates/reviews/human-approvals/executions 五类账本
- 前后清单、move-ledger、回滚清单、safety_pending=0

## 6. 特化重点参考（现有 template/run）

- `templates/specialized/h-drive-cleanup`
- `runs/h-drive-cleanup-20261018`
- `runs/h-drive-od-dismantle-20261018`
- `runs/h-drive-root-layout-20261018`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/safe-cleanup@1.0.0`；`contracts: audit@1.0.0, optimize@1.0.0, verify@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 最高：真实数据/不可逆风险；默认 move-only、不删除、不 purge。
- 当前标记：**M3**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
