# 总参谋部 · 思考 Playbook

- 版本：`v1.0.0`（2026-11-14）
- 适用：任何分析/设计/治理/研究类 thinking workflow
- 前置：`docs/general-staff/GENERAL-STAFF.md`、`reports/general-staff/THINKING-DIMENSIONS.json`、`THINKING-ROUNDS.json`、`ROUND-EVALUATIONS.json`
- 铁律：**先咨询参谋部，再进入分析；全扩展不留死角，定向扩展必须有选择理由。**

## 0. 两种扩展

| 模式 | 何时用 | 做法 | 输出 |
|---|---|---|---|
| **全扩展（full）** | 新领域/高风险/方案设计/复盘 | 24 维逐个过；不适用写 `N/A + 理由` | 24 维 checklist + 结论 |
| **定向扩展（targeted）** | 时间盒/单一问题/补洞 | 先咨询，按风险/未知选 3–5 维，其余写 `not-applicable` | 选择理由 + 3–5 维深挖 |

禁止：只写“已考虑”不写证据；用 10 维评分代替 24 维分析；跳过咨询直接给方案。

## 1. 强制咨询（consult-before-analyze）

1. 读 `THINKING-ROUNDS.json`、`ROUND-EVALUATIONS.json`、`THINKING-DIMENSIONS.json`、本 playbook。
2. 选 1 个 seat（默认）或 2 个 seat（高风险/跨域/复杂）。
3. 输出 `STAFF-CONSULTATION-<workflow>.json`：
   - 读了什么（路径/版本/条目数）
   - 命中哪些维度、哪些高分轮次可借鉴
   - 哪些角度缺失/不适用
   - 建议扩展路线（full/targeted + 维度）
4. 咨询完成前，**不得**进入 analyze/synthesize。

协议：`docs/general-staff/THINKING-CONSULTATION-PROTOCOL.md`。

## 2. 全扩展 checklist（24 维）

逐项打勾；`N/A` 必须写理由。

- [ ] `problemDefinition` 问题定义：一句问题 + 成功/失败
- [ ] `boundariesNonGoals` 边界/非目标：不做什么/谁不负责
- [ ] `stakeholders` 干系人：受益/受损/批准/维护
- [ ] `constraints` 约束：时间/预算/合规/平台/依赖
- [ ] `assumptions` 假设：关键假设 + 验证/失效条件
- [ ] `firstPrinciples` 第一性原理：根因/最小机制
- [ ] `systemsArchitecture` 系统/架构：组件/边界/数据流/单点
- [ ] `dataState` 数据/状态：状态机/schema/迁移/一致性
- [ ] `failureModes` 失败模式：哪里错/如何发现/降级
- [ ] `riskRollback` 风险/回滚：最坏后果/止损/回滚
- [ ] `securityPrivacy` 安全/隐私：token/权限/截图/聊天/越权
- [ ] `performanceCost` 性能/成本：延迟/吞吐/内存/费用/预算
- [ ] `uxHumanFactors` UX/人因：场景/误操作/可理解/可恢复
- [ ] `operationsMaintainability` 运维/可维护：部署/监控/排障/升级
- [ ] `testingVerification` 测试/验证：可复跑/反例/独立 QA
- [ ] `releaseMigration` 发布/迁移：灰度/兼容/迁移/回滚
- [ ] `governanceOwnership` 治理/ownership：决策/签字/维护/升级
- [ ] `alternativesTradeoffs` 替代方案/取舍：多方案 + 量化
- [ ] `secondOrderEffects` 二阶效应：长期副作用/反馈环
- [ ] `metricsMeasurement` 指标/度量：基线/目标/采集
- [ ] `reversibility` 可逆性：回滚成本/触发条件
- [ ] `timeBudget` 时间/预算：deadline/预算/裁剪
- [ ] `unknownsBlindSpots` 未知/盲区：未知清单/验证计划
- [ ] `crossDomainAnalogies` 跨域类比/反例：类比 + 不适用边界

## 3. 定向扩展标准步骤

1. **咨询**：staff-reader 输出命中/缺失/建议。
2. **选维**：按任务风险选 3–5 个维度；写选择理由 + 不选维度的 `N/A`。
3. **深挖**：每维给结论/证据/反例/残余风险。
4. **综合**：方案/决策 + 边界 + 回滚 + 未知。
5. **QA**：检查是否漏掉安全/数据/回滚/未知；必要时补维。
6. **记录**：把 `dimensionRefs` 写回 evaluation/registry。

## 4. 人才方法样板

从 `ROUND-EVALUATIONS.json` 选 1–2 个高分轮次作为“做得好”的方法样板：

| 样板 | 分数 | 为什么 | 适用边界 |
|---|---|---|---|
| `THINK-20261114-07` STOP-SWEEP | 47 | 场景/分类/证据/回滚完整；决策质量高 | 命令多为草案；宿主 systemd/PID 未验证；不要直接执行破坏性命令 |
| `THINK-20261114-05` compare | 46 | 广度/替代方案/决策矩阵强；证据可复核 | 只读分析，未做代码验证；旧桥语义可能变化 |
| `THINK-20261114-01` g3d（runner-up） | 45 | 模拟/验收/限制清单完整 | 全部为推演，不是实测 |

用法：不是复制结论，而是复制**方法结构**：

- STOP-SWEEP：冻结 → 盘点 → 分类 → 动作 → 回滚 → 验收。
- compare：能力矩阵 → 差异判定 → 建议分级 → 证据/核查。
- g3d：场景矩阵 → 模拟 → 验收 → 限制/未观测。

最终人才结论不在本 playbook；见 `TALENT-LEDGER.json`（暂定）。

## 5. 反模式

- 先写方案再补维度（事后合理化）。
- 24 维只写“已考虑”；无证据/无反例。
- 用“用户没要求”跳过安全/数据/回滚。
- 把 first-pass 评分当绝对真理；用分数替代证据。
- 没有 consult 就直接 analyze；咨询只在最后补一句。
- 全扩展变成 24 段空话；定向扩展变成只做舒服的维度。

## 6. 输出模板

```text
1. 咨询摘要（读了什么/命中/缺失/建议）
2. 扩展模式（full/targeted）+ 维度清单
3. 每维：结论/证据/反例/残余风险
4. 综合方案/决策
5. 回滚/未知/下一步
6. QA 检查
```

## 7. 引用

- `docs/general-staff/GENERAL-STAFF.md`
- `reports/general-staff/THINKING-DIMENSIONS.json` / `.md`
- `reports/general-staff/THINKING-ROUNDS.json`
- `reports/general-staff/ROUND-EVALUATIONS.json`
- `reports/general-staff/TALENT-LEDGER.json`
- `docs/general-staff/THINKING-CONSULTATION-PROTOCOL.md`
- `templates/thinking-workflow.yaml` / `templates/thinking-workflow-2seat.yaml`
