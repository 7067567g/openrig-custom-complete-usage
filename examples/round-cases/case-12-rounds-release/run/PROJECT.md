<!-- wf-doc
run: case-12-rounds-release
round: 12
doc: PROJECT
owner: PMO
state: closed
updated: 2026-11-13
tags: template/openrig-workflow-master, baseline/two-plane-orchestration
primary_type: composite/two-plane-orchestration
maturity: M3
baseline: composite/two-plane-orchestration@1.0.0
contracts: strategy@1.0.0, research@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0, audit@1.0.0
-->

# PROJECT — OpenRig 混合编排母版实例

> 写者：PMO ｜ 主会话只读 §6 ｜ 本文件是控制面权威；OpenRig queue/workflow 是执行面权威。

## 0. 元信息

| 项 | 值 |
| --- | --- |
| run-id | `case-12-rounds-release` |
| 一句话目标 | `Prepare a release over 12 rounds` |
| 项目根 | `<repo-root>` |
| 写权限白名单 | `runs/case-12-rounds-release/**` |
| OpenRig 工作目录 | `runs/case-12-rounds-release/openrig/`（由 render_master.py 生成） |
| 隔离 home | `<openrig-home>` |
| 默认 rig/workflow | 生成的 rig.yaml / workflow.yaml（唯一名字） |
| 编制 | PMO×1 / TDO×1 / QA×1 |
| 当前轮次 | Round 1 |
| 终止判据 | 工作包闭环或明确 blocker；无 open S1/S2；bridge/证据/teardown 完整 |

## 1. 目标与成功判据

- **G1 双平面契约**：控制面四件套、bridge、OpenRig rig/workflow、seat map 一致。
- **G2 接入**：隔离 daemon + rig 启动成功，5 seats ready；workflow instantiate 成功，entry packet 到 PMO。
- **G3 执行**：至少一个 OpenCode 分支和一个 DSH 分支收到 packet 并产生证据；需要时支持多行 envelope。
- **G4 管理**：queue/workflow/transcript/session id 可追踪；失败可恢复；无跨 run 污染。
- **G5 QA**：独立 QA 对照 SPEC 给出 PASS/WARN/FAIL/SKIP，开 ISSUE 有证据。
- **G6 优化**：记录模型选择、并发、token/成本、延迟、失败率和一条可执行优化建议。
- **G7 收口**：DECISIONS/STATUS 完成；rig/down/daemon stop；无残留进程/tmux；bridge 与实际一致。

**反目标**：

- 不把 OpenRig queue 当项目目标或决策账本；
- 不用 fresh seat 冒充恢复；
- 不修改 OpenRig 数据库；
- 不在本 run 内删除旧 runtime 或重写 UI；
- 不泄露 provider key。

## 2. 范围

### 2.1 范围内

- workflow-group 四件套 + `OPENRIG-BRIDGE.json`；
- 每个 run 生成独立 rig/workflow spec；
- 隔离 OpenRig daemon/rig/workflow 运行面；
- 执行、证据、QA、收口、复盘。

### 2.2 范围外

- 产品代码的大规模重写（由项目自己的 WS 决定）；
- 非本 run 的 OpenRig 租户/daemon；
- 全局配置或跨用户数据清理；
- 未授权删除/发布/权限变更。

### 2.3 假设与依赖

- OpenRig CLI/daemon 已构建，OpenCode/DSH runtime 可用；
- 默认 Node24；具体 bin 路径写入 bridge；
- 5 seats 在 4 vCPU/5.8GB 下可启动，但同时活跃 agent 建议 ≤2；
- 真实模型调用需要 runtime 自己的认证；认证缺失如实阻断。

## 3. 指标

| # | 指标 | 目标 | 当前 | 证据 |
| --- | --- | --- | --- | --- |
| M1 | 双平面映射完整率 | 100% | 待采集 | bridge + seat map |
| M2 | rig ready | 5/5 | 待采集 | `rig ps --nodes` |
| M3 | workflow instantiate | entry packet 到 PMO | 待采集 | workflow show |
| M4 | 工作包证据覆盖 | 每个 packet 有 receipt/transcript/结果 | 待采集 | queue + evidence |
| M5 | QA 覆盖 | 100% 判据有结果 | 待采集 | QA report |
| M6 | 连续性 | resume 可用或明确 fresh | 待采集 | sidecar/snapshot |
| M7 | 清理 | 0 残留 | 待采集 | hygiene 报告 |
| M8 | 优化记录 | ≥1 条可执行建议 | 待采集 | retro |

## 4. 分任务（Workstreams）

| WS | 任务 | 产出物 | 验收判据 | 依赖 | 执行体 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| WS-1 | 接入配置与 render | `openrig/rig.yaml`、`workflow.yaml`、`OPENRIG-BRIDGE.json` | render + validate PASS | — | TDO | 待开始 |
| WS-2 | 隔离启动与实例化 | daemon/rig/workflow 状态证据 | 5 seats ready；entry PMO | WS-1 | TDO | 待开始 |
| WS-3 | 执行分支 | OC/DSH packet/transcript/结果 | 两分支有证据 | WS-2 | TDO | 待开始 |
| WS-4 | QA 与恢复 | QA report、resume/hygiene 证据 | 判据覆盖；恢复验证 | WS-3 | QA | 待开始 |
| WS-5 | 收口与优化 | 决策、复盘的优化建议 | doctor PASS；无残留 | WS-4 | PMO/MAIN | 待开始 |

## 5. 轮次计划与结论

### Round 1 计划

- 先 render + validate，再隔离启动；执行阶段按预算选择并行/串行。
- 所有队列工作包必须有 owner 和 evidence 指针。
- 结束时必须给出接入、管理、优化三方面的复盘。

### Round 1 结论

- 待采集。

## 6. PMO 上报区

- **本轮结论**：12 轮全部完成；每轮 STATUS 为 qa-done，QA 无阻塞项，证据指针写入 `ROUNDS.md` 与 `evidence/round-N.log`。
- **待拍板**：无；建议 MAIN 接受收口，并关闭 PROJECT / STATUS / DECISIONS。
- **指标变化**：12/12 轮有证据指针；12/12 条决策已登记；0 个 open S1/S2；0 个阻塞项。
- **优化建议**：保留每轮证据日志、ROUNDS.json 与 DECISIONS 切片，作为后续真实项目的复用模板；下一批案例可加入真实模型调用与 token/成本记录。
- **风险提示**：这是合成案例，不代表真实项目结果；只证明 workflow-group 的 12 轮状态机与文档合同可以完整跑通。


## 7. 变更日志

| 时间 | 轮次 | 变更 | 由谁 |
| --- | --- | --- | --- |
| 2026-11-13 | R1 | 从 OpenRig 混合编排母版实例化 | 主会话 |
