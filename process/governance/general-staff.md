# 总参谋部 · 思考类单独轮索引与评估标准

- **版本**：`v1.0.0`（standard，2026-11-14）
- **状态**：`standard / reusable` —— 长期复用的思考类轮次索引/评估标准，不是一次性的名单。
- **Owner**：Lead/MAIN + QA lead；日常维护由 Lead 指定。
- **范围**：已登记 `SOLO-*` 中 `primary`/`secondary` 思考成分的轮次；不登记长运行分支（command center 管理）、正式轮、out-of-scope 输出物。
- **配套**：
  - 索引：`reports/general-staff/THINKING-ROUNDS.json` / `.md`
  - 考评模板：`reports/general-staff/ROUND-EVALUATION-TEMPLATE.json`
  - 第一轮评估：`reports/general-staff/ROUND-EVALUATIONS.json` / `.md`（s2）
  - 24 维索引：`reports/general-staff/THINKING-DIMENSIONS.json` / `.md`
  - Playbook：`reports/general-staff/THINKING-PLAYBOOK.md`
  - 人才台账：`reports/general-staff/TALENT-LEDGER.json`
  - 强制咨询：`docs/general-staff/THINKING-CONSULTATION-PROTOCOL.md`
  - Workflow 模板：`templates/thinking-workflow.yaml`、`templates/thinking-workflow-2seat.yaml`
  - 标戳：源目录 `.staff-thinking.json`（当前 13 条 in-place）

## 0. 总参谋部是什么

总参谋部是**思考类任务**的索引、评估、人才选拔和维度复用中心：

- 以单轮 OpenRig（SOLO）为主；
- 不替代 command center（登记长运行轮/主支）、正式 30 轮、分支协议；
- 不移动/重命名旧内容，只在原目录加/镜像 `.staff-thinking.json` 并建索引；
- 不选最终人才结论；第一轮只做索引 + 标准考评 + 初评，下一轮再做维度/人才分析。

### 0.1 不是什么

- 不是“所有 SOLO 都算思考轮”：纯操作/执行可标 `none`，不纳入。
- 不是 branch/command center 的替代；长运行轮仍看 `ROUND-REGISTRY.json`。
- 不是产品验收；不改产品代码，不读原始截图/聊天/token。
- 不是永久名单；轮次状态/分类变化时更新索引。

## 1. 分类

| 类 | 定义 | 处理 |
|---|---|---|
| `primary` | 主要工作是思考/分析/设计/治理方案；交付以文档/决策/协议为主 | 入索引，分配 THINK ID，写 staff stamp，参与评估 |
| `secondary` | 有思考成分，但主要交付是运维/实现/审计/工具 | 入索引，分配 THINK ID，写 staff stamp，参与评估（标注次要） |
| `none` | 纯操作/执行，无可复用思考产出 | 不入索引；不分配 THINK ID；不写 stamp |

判定以“主要交付”而不是“是否写了文档”为准；有争议时 Lead/QA 决定并写 rationale。

## 2. THINK ID

- 格式：`THINK-20261114-NN`
- 一次性分配，不复用；与 `sourceSoloId` 一一绑定。
- 索引字段：`thinkingId` / `sourceSoloId` / `sourcePath` / `staffClass` / `title` / `status` / `stampPath` / `stampMode`。
- 不修改原 `.solo-round.json`；staff stamp 是补充，不是替换。

## 3. 索引字段

```json
{
  "thinkingId": "THINK-20261114-01",
  "sourceSoloId": "SOLO-20261026-01",
  "sourcePath": "<absolute sourceRoot>",
  "title": "<short title>",
  "staffClass": "primary|secondary|none",
  "strategy": "<source strategy>",
  "status": "<CLOSED|RUNNING|...>",
  "rationale": "<why this class>",
  "stampPath": "<absolute .staff-thinking.json>",
  "stampTarget": "<sourceRoot>/.staff-thinking.json",
  "stampMode": "in_place|mirror",
  "owner": "<owner>",
  "notes": "<short>"
}
```

## 4. 考评维度（1–5 分）

| 维度 | 含义 | 1 分 | 3 分 | 5 分 |
|---|---|---|---|---|
| `problemFraming` | 问题定义/边界 | 目标含糊 | 目标清楚 | 精确定义 + 非目标 |
| `breadth` | 视角/方案广度 | 单一路径 | 2–3 方案 | 多方案 + 取舍 |
| `depth` | 分析深度 | 表面 | 有机制 | 根因/反例/边界 |
| `alternatives` | 备选方案质量 | 无备选 | 有备选 | 有量化/裁决 |
| `evidence` | 证据/可复核 | 断言 | 有路径/命令 | 可复跑 + 反证 |
| `riskEdgeCases` | 风险/边界 | 未提 | 列主要风险 | 风险矩阵 + 回滚 |
| `decisionQuality` | 决策/建议 | 无结论 | 有建议 | 明确裁决 + 条件 |
| `reproducibility` | 可复现/可交接 | 只靠记忆 | 有文档 | 模板/命令/记录齐全 |
| `executionClosure` | 收口/生命周期 | 漂移 | 有 closeout | QA/证据/归档完整 |
| `transferability` | 可复用/迁移 | 一次性 | 部分复用 | 标准/模板/维度可复用 |

总分 = 10 维之和（10–50）。等级建议：

- `A`：40–50，可作标杆/人才候选
- `B`：32–39，可复用
- `C`：24–31，有亮点但需补
- `D`：10–23，不建议复用

`talentCandidate` 只作初评标记（总分 ≥40 且 evidence/decisionQuality ≥4），最终人才结论下一轮做。

## 5. 考评表字段

`ROUND-EVALUATION-TEMPLATE.json` 包含：

- `thinkingId` / `sourceSoloId` / `staffClass`
- `scores`（10 维，1–5）
- `totalScore` / `grade` / `talentCandidate`
- `strengths[]` / `blindSpots[]` / `reusableIdeas[]`
- `evidenceRefs[]` / `evaluator` / `evaluatedAt` / `notes`

## 6. 流程

```text
SOLO registry (13)
  → classify primary/secondary/none
  → assign THINK ID + sourceSoloId/sourcePath
  → write .staff-thinking.json (in-place or mirror)
  → THINKING-ROUNDS.json/.md
  → evaluate primary/secondary with template
  → ROUND-EVALUATIONS.json/.md
  → next round: dimension index / talent analysis (not here)
```

## 7. 与其它对象

| 对象 | 关系 |
|---|---|
| `STANDALONE-ROUNDS.json` | 源台账；staffThinkingId/staffClass 回写，不删原字段 |
| `SOLO-STAMP-PROTOCOL` | `.solo-round.json` 是身份主真值；`.staff-thinking.json` 是参谋部补充，不改原 stamp |
| `COMMAND-CENTER` | 长运行轮/主支登记；总参谋部不替代 |
| `STOP-SWEEP` / `CLOSEOUT` | 停止/归档时更新 staff 索引状态；不移动源目录 |
| R15/R16 | anchor R15，rejoin R16；不跳过 R16 |

## 8. 隐私/边界

- 索引/考评只写标题、路径、评分、理由；不写聊天正文、token、原始截图。
- 不读图片/截图内容；证据只引用文档/命令/报告。
- 不移动/重命名源目录；mirror 需标注并后续复制。

## 9. 验收

- [ ] 13 条 SOLO 全部有 `staffClass`；primary/secondary 有 THINK ID。
- [ ] `THINKING-ROUNDS.json` 可解析，ID 唯一，sourceSoloId/sourcePath 绑定。
- [ ] 入选轮有 `.staff-thinking.json`（in-place 或 mirror）。
- [ ] 考评模板 10 维 + 总分/等级/人才候选字段。
- [ ] 第一轮评估覆盖所有 primary/secondary。
- [ ] 未修改 `.solo-round.json`；未移动/改名源目录。
- [ ] 未读/写原始截图、聊天正文、token。

## 10. 变更记录

| 版本 | 日期 | 作者/角色 | 变更 |
|---|---|---|---|
| v1.0.0 | 2026-11-14 | builder / MAIN review | 建立总参谋部：分类、THINK ID、索引字段、10 维考评、流程、边界。 |
| v1.0.1 | `<YYYY-MM-DD>` | `<maintainer>` | `<change>` |


## 11. 追加：总参谋部自身登记（2026-11-14）

- `SOLO-20261114-09` / `THINK-20261114-14`：总参谋部与思考类单独轮索引。
- `SOLO-20261114-10` / `THINK-20261114-15`：思考维度/人才/咨询机制。
- 当前索引 15 条，全部 in-place staff stamp；13 条已评估，THINK-14/15 待下一周期评估。
