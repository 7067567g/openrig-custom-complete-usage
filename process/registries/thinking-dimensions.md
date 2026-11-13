# 总参谋部 · 思考维度索引（24 维）

- 日期：2026-11-14
- 版本：`v1.0.0`
- 机器可读：`reports/general-staff/THINKING-DIMENSIONS.json`
- 协议：`docs/general-staff/GENERAL-STAFF.md`
- 用途：全扩展 checklist、定向扩展选择、咨询命中维度、考评证据提示。

## 维度表

| ID | 维度 | 组 | 要回答的问题 | 1 / 3 / 5 锚点 | 证据提示 |
|---|---|---|---|---|---|
| `problemDefinition` | 问题定义 | framing | 要解决的真实问题是什么？成功/失败如何定义？ | 目标含糊 / 目标清楚 / 精确定义 + 非目标 | 写一句问题陈述 + 验收 |
| `boundariesNonGoals` | 边界/非目标 | framing | 哪些明确不做？哪些不是本轮责任？ | 无边界 / 列主要非目标 / 边界 + 排除理由 | 写 non-goals 清单 |
| `stakeholders` | 干系人 | framing | 谁受益/谁受损/谁批准/谁维护？ | 未识别 / 列主要角色 / 角色 + 利益/权力/冲突 | stakeholder map |
| `constraints` | 约束 | framing | 时间/预算/合规/平台/依赖限制？ | 未提 / 列主要约束 / 约束 + 可调整性 | constraint table |
| `assumptions` | 假设 | framing | 哪些前提未验证？错了会怎样？ | 隐含假设 / 列关键假设 / 假设 + 验证/失效条件 | assumption register |
| `firstPrinciples` | 第一性原理 | framing | 去掉惯例后，最小必要机制是什么？ | 类比/惯例 / 拆到机制 / 根因 + 反例 + 最小方案 | first-principles note |
| `systemsArchitecture` | 系统/架构 | system | 组件/边界/数据流/依赖/单点？ | 黑盒 / 主要组件 / 架构图 + 失败边界 | component/data-flow |
| `dataState` | 数据/状态 | system | 状态存哪/谁写/版本/迁移/一致性？ | 未提状态 / 列主要状态 / 状态机 + schema/迁移 | state/schema table |
| `failureModes` | 失败模式 | system | 哪里会错？如何发现/降级/恢复？ | 只写 happy path / 列主要失败 / FMEA/失败矩阵 + 检测 | failure list |
| `riskRollback` | 风险/回滚 | system | 最坏后果？回滚路径/止损点？ | 无回滚 / 列风险 + 回滚 / 风险矩阵 + 可逆步骤 | rollback plan |
| `securityPrivacy` | 安全/隐私 | safety | token/权限/截图/聊天/越权/泄露？ | 未提 / 列主要面 / 威胁模型 + 最小权限 | privacy/security checklist |
| `performanceCost` | 性能/成本 | safety | 延迟/吞吐/内存/费用/预算？ | 无数字 / 目标/预算 / 目标 + 实测/包络 | budget table |
| `uxHumanFactors` | UX/人因 | safety | 谁在什么场景用？误操作/可理解性？ | 只看功能 / 主要场景 / 场景 + 误操作/可恢复 | user journey |
| `operationsMaintainability` | 运维/可维护性 | safety | 谁部署/监控/排障/升级？ | 未提 / 列运维面 / runbook + ownership | runbook/owner |
| `testingVerification` | 测试/验证 | delivery | 怎么证明对？反例/回归/真机？ | 自述通过 / 有测试 / 可复跑 + 反证/独立 QA | test evidence |
| `releaseMigration` | 发布/迁移 | delivery | 灰度/兼容/迁移/回滚/版本？ | 直接上线 / 列步骤 / 分阶段 + 迁移/回滚 | release plan |
| `governanceOwnership` | 治理/ownership | delivery | 谁决策/谁签字/谁维护/如何升级？ | 无 owner / 有 owner / RACI + 门禁/审计 | ownership table |
| `alternativesTradeoffs` | 替代方案/取舍 | choice | 还有哪些方案？为什么不选？ | 单方案 / 2–3 方案 / 多方案 + 量化取舍 | option matrix |
| `secondOrderEffects` | 二阶效应 | choice | 短期修好后会引发什么长期影响？ | 未提 / 列主要二阶 / 反馈环 + 副作用/对策 | impact map |
| `metricsMeasurement` | 指标/度量 | choice | 用什么指标判断好坏？基线/目标？ | 无指标 / 有指标 / 指标 + 基线/目标/采集 | metric table |
| `reversibility` | 可逆性 | choice | 决策/迁移/合并能否撤回？成本？ | 不可逆 / 可回滚 / 回滚成本 + 触发条件 | reversibility note |
| `timeBudget` | 时间/预算 | choice | 最迟何时？预算/人力/机会成本？ | 无期限 / 有 deadline / 时间盒 + 预算/裁剪 | timebox |
| `unknownsBlindSpots` | 未知/盲区 | unknown | 我们不知道什么？谁可能不同意？ | 未列未知 / 列主要未知 / 未知清单 + 验证计划 | unknowns list |
| `crossDomainAnalogies` | 跨域类比/反例 | unknown | 别的领域怎么解？哪里不适用？ | 无类比 / 1–2 类比 / 类比 + 反例/边界 | analogy note |

## 使用

- **全扩展不留死角**：24 维逐个过；不适用写 `N/A + 理由`，不能空白。
- **定向扩展**：按任务风险/未知选 3–5 维，先咨询参谋部，再进入分析。
- **咨询**：输出必须写命中/缺失维度；未咨询不得进入 analyze。
- **考评**：10 维评分是质量分；本 24 维是分析覆盖清单，二者不混用。

## 分组

- `framing`：问题定义/边界/干系人/约束/假设/第一性原理
- `system`：架构/数据状态/失败模式/风险回滚
- `safety`：安全隐私/性能成本/UX 人因/运维可维护
- `delivery`：测试验证/发布迁移/治理 ownership
- `choice`：替代方案/二阶效应/指标/可逆性/时间预算
- `unknown`：未知盲区/跨域类比

## 引用

- `reports/general-staff/THINKING-DIMENSIONS.json`
- `docs/general-staff/GENERAL-STAFF.md`
- `reports/general-staff/THINKING-PLAYBOOK.md`
- `docs/general-staff/THINKING-CONSULTATION-PROTOCOL.md`
