# BASELINE — product-redesign-live

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M2` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `research@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

在单窗口/多端产品上先做反目标与信息架构判断，再多 seat 评审、实现、staging QA，最后安全地应用到 live 并可回滚。

## 2. 特点

- 先写“不该补/反目标”，防止功能齐全变成复杂；菜单/状态/长回复是产品约束而非实现细节。
- 研究/设计/QA 由独立 seat 或角色完成，MAIN 负责整合与 live 决策。
- staging→QA→统一合并→finalize live，live 动作有快照、回滚、通知和证据。
- 上线后保留真机待观察项，不把一次测试通过当永久稳定。

## 3. 默认管线（原子轮型组合）

1. research/architecture：现状/历史/竞品/信息架构/反目标
2. optimize：实现与集成
3. verify：staging QA + 真机/离线测试
4. live：finalize + 快照/回滚/通知/观察

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- 反目标/功能取舍表 + 设计报告
- staging 测试结果 + QA 独立报告
- finalize 日志、live 状态、回滚脚本/演练、通知证据

## 6. 特化重点参考（现有 template/run）

- `templates/specialized/<your-domain>`
- `snapshot:<your-domain>-example`
- `snapshot:<your-domain>-example`
- `snapshot:<your-domain>-example`
- `snapshot:<your-domain>-example`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/product-redesign-live@1.0.0`；`contracts: research@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 高：生产服务/live 用户；必须 staging-first、回滚优先、不在桥内跑辅助功能。
- 当前标记：**M2**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
