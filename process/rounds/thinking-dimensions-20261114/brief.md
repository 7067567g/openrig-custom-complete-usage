# SOLO-20261114-10 · 总参谋部思考维度/人才/咨询机制

- 类型：单独轮（STANDALONE）
- 别名：离散轮 / 零散轮
- 主策略：ANALYZE + GOVERN
- Anchor：R15；Rejoin：R16
- 前置：`docs/general-staff/GENERAL-STAFF.md`、`reports/general-staff/THINKING-ROUNDS.json`、`ROUND-EVALUATIONS.json`
- 目标：
  1. 基于 13 条思考轮评估，建立思考维度索引；
  2. 定义“全扩展不留死角”和“定向扩展标准过程”；
  3. 从高分轮次中选拔人才（1–2 个“做得好”的轮次）作为全轮数据分析方法样板；
  4. 定义总参谋部咨询机制：每次思考流程强制 1–2 个 seat 查阅参谋部，再综合判断；
  5. 提供可复制的 thinking workflow 模板（1 seat / 2 seat 变体）。

## 强制咨询规则

- 任何思考类 workflow 必须有 `consult_staff` 步骤，先读：
  - `THINKING-ROUNDS.json`
  - `ROUND-EVALUATIONS.json`
  - `THINKING-DIMENSIONS.json`
  - `THINKING-PLAYBOOK.md`
- 咨询 seat 数：1–2；默认 1，复杂/高风险 2。
- 咨询输出必须记录：读了什么、命中哪些维度、建议哪些扩展、哪些角度不适用。
- 未咨询不得进入分析/方案步骤。

## 输出

- `reports/general-staff/THINKING-DIMENSIONS.json` / `.md`
- `reports/general-staff/THINKING-PLAYBOOK.md`
- `reports/general-staff/TALENT-LEDGER.json`
- `docs/general-staff/THINKING-CONSULTATION-PROTOCOL.md`
- `templates/thinking-workflow.yaml`（1 seat 默认）
- `templates/thinking-workflow-2seat.yaml`（复杂任务）
- `reports/general-staff/STAFF-CONSULTATION-20261114-10.json`
- 更新 `THINKING-ROUNDS.json`/`ROUND-EVALUATIONS.json` 的 talent/dimension refs
- 更新 `STANDALONE-ROUNDS.json` 登记 SOLO-09/SOLO-10

## 维度至少包含

问题定义、边界/非目标、干系人、约束、假设、第一性原理、系统/架构、数据/状态、
失败模式、风险/回滚、安全/隐私、性能/成本、UX/人因、运维/可维护性、测试/验证、
发布/迁移、治理/ownership、替代方案/取舍、二阶效应、指标/度量、可逆性、时间/预算、
未知/盲区、跨域类比/反例。

## 约束

- 不改产品代码；不移动源目录；不读原始截图/聊天正文/token；
- 不把评估分数当绝对真理；人才选拔必须写证据和适用边界；
- 咨询协议是标准件，长期复用，不是一次性的。
