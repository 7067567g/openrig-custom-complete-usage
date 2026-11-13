# BASELINE — ops-hardening

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M3` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `audit@1.0.0, optimize@1.0.0, verify@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

提高分发、同步、调度和日常入口的可靠性：先证明能恢复、能 clone、能解回，再证明改动不会破坏现有入口。

## 2. 特点

- 先做只读健康报告，再做写修复；多仓/无版本控制路径必须留文件清单和 diff 摘要。
- 恢复性优先：归档可解回、bundle 可 clone 复验、篡改/缺失反例必须 FAIL。
- 先红后绿；入口检查要有命令、退出码和耗时。
- 不 push、不改数据本体、不用形式通过代替真实验证。

## 3. 默认管线（原子轮型组合）

1. audit：盘点分发/同步/调度入口与恢复路径
2. optimize：加固脚本、门禁、负向测试
3. verify：复跑入口健康、恢复演练和反例

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- 恢复演练记录（解压/解回/clone/rollback）
- 篡改 1 字节、缺条目、remote 空等反例输出
- 入口健康报告与 FAIL→PASS 对照

## 6. 特化重点参考（现有 template/run）

- `templates/specialized/dist-ops-hardening`
- `templates/specialized/ops-reliability`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/ops-hardening@1.0.0`；`contracts: audit@1.0.0, optimize@1.0.0, verify@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 中：可能跨仓/无版本控制；禁止把未纳管改动写成“无需提交”。
- 当前标记：**M3**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
