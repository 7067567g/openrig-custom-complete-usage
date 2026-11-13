# BASELINE — two-plane-orchestration

> **基准模板（base reference template）** ｜ 版本 `1.0.0` ｜ 成熟度 `M3` ｜ 基础母版 `workflow-group-base@1.2.0` ｜ 原子契约 `strategy@1.0.0, research@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0, audit@1.0.0`
> 本文件是复合类型的重点参考，不是可直接实例化的 run 模板。真正跑 run 请使用 `templates/specialized/<domain-template>`，并在其 `SPEC.md` §0 声明本 baseline id/version。

## 1. 主攻方向

把目标、决策、验收和证据留在 workflow-group，把 seat、queue、workflow、transcript 和恢复状态交给 OpenRig；两边通过 bridge/证据指针同步。

## 2. 特点

- 双权威：控制面管目标/决策/验收，执行面管实时执行状态；不允许一边冒充另一边。
- 每个 run 独立 OPENRIG_HOME/端口/rig 名；默认 managed isolated，不碰 live daemon。
- workflow 图允许分支 QA + join + 有界返工（静态回边 + max_hops），不新增引擎 API。
- 严格归档顺序：capture/status/archive 到 COMPLETE 后才允许 rig down/daemon stop；历史 PARTIAL 仅作缺口记录。

## 3. 默认管线（原子轮型组合）

1. preflight：隔离 home/端口/bridge/预算
2. strategy/research/architecture：控制面目标与方案
3. optimize：多 seat 执行；执行者只声明证据
4. verify/audit：分支 QA + join + 有界返工
5. close：归档→teardown→复盘

## 4. 适用 / 不适用

- **适用**：当任务属于本复合类型，且领域 adapter 能提供明确的写权限、证据入口和风险修饰时。
- **不适用**：任务只需要一个原子轮型；或领域边界/证据入口尚未明确。此时先用 `research`/`audit` 或单轮专项，不要硬套复合类型。

## 5. 强制证据与 DoD

- OPENRIG-BRIDGE.json + rig/workflow validate/instantiate/show
- queue packet + transcript + local STATUS 证据指针
- pre/post baseline、workflow trace、archive MANIFEST/RECORD
- teardown 后无残留的 hygiene 证据

## 6. 特化重点参考（现有 template/run）

- `templates/specialized/openrig-workflow-master@1.2.0`
- `runs/openrig-master-v12-20261020`
- `runs/openrig-unparsed-bytes-20261020`
- `runs/openrig-master-selfopt-20261020`

## 7. 实例化规则

1. 选择一个领域 `templates/specialized/<name>`，不要直接用本目录当 `--template`。
2. 在该 `SPEC.md` §0 写：`baseline: composite/two-plane-orchestration@1.0.0`；`contracts: strategy@1.0.0, research@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0, audit@1.0.0`。
3. 按 `templates/contracts/_shared/PLAN-GATE.md` 做 7/7 计划门；若领域 SPEC 额外门更严，从严执行。
4. 在 `ROUND-PLAN.md` 按默认管线拆轮次；每轮只用一个原子契约，交 `_shared/VERDICT.md`。
5. 收口时把本 baseline 的“特点/证据”逐条映射到实际产物；缺项必须进 ISSUES 或 DECISIONS。

## 8. 风险与成熟度边界

- 高：双平面状态漂移、生产 live rig、secrets、archive PARTIAL；所有执行必须绑定隔离环境。
- 当前标记：**M3**。M2 表示仍需要更多 run 或参数化；M3 表示接口和证据已可复用。
