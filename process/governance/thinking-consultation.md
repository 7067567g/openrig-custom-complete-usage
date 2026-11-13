# 思考流程强制咨询协议（THINKING CONSULTATION）

- **版本**：`v1.0.0`（standard，2026-11-14）
- **状态**：`standard / reusable`
- **适用**：任何分析/设计/治理/研究类 thinking workflow（包括 SOLO 与长运行轮的分析步骤）。
- **Owner**：Lead/MAIN；staff-reader seat 执行；QA 复核。
- **前置**：`docs/general-staff/GENERAL-STAFF.md`、`reports/general-staff/THINKING-DIMENSIONS.json`、`THINKING-ROUNDS.json`、`ROUND-EVALUATIONS.json`、`THINKING-PLAYBOOK.md`。
- **铁律**：**没有 `consult_staff` 输出，不得进入 analyze/synthesize。**

## 1. 为什么强制

思考流程最容易犯的错不是“不会分析”，而是**漏维度**：只从熟悉的角度出发，忽略干系人、数据、安全、回滚、未知。总参谋部把 13 条历史思考轮的维度/盲点/方法沉淀成索引；每次先咨询，能把“个人视角”变成“组织记忆”。

## 2. 咨询 seat 数

| 任务 | seat 数 | 角色 |
|---|---|---|
| 默认/低风险/单域 | **1** | staff-reader（可由 builder 兼，但必须先读后写） |
| 高风险/跨域/高不确定/主链决策 | **2** | staff-reader A（维度/历史）+ staff-reader B（反例/风险） |
| 正式轮/R16/隐私门 | 2 + MAIN | 独立 QA + MAIN 签字 |

- 1 seat 也必须是**独立步骤**，不能“边分析边想”。
- 2 seat 输出两份 consultation，再合并；不一致处写分歧，不强行一致。

## 3. 输入（必须读）

- `reports/general-staff/THINKING-ROUNDS.json`
- `reports/general-staff/ROUND-EVALUATIONS.json`
- `reports/general-staff/THINKING-DIMENSIONS.json`
- `reports/general-staff/THINKING-PLAYBOOK.md`
- 当前任务 brief/context（只读；不读原始截图/聊天/token）

## 4. 输出字段

写入 `reports/general-staff/STAFF-CONSULTATION-<workflow>.json`：

```json
{
  "schema": "example-staff-consultation/v1",
  "consultationId": "CONSULT-YYYYMMDD-NN",
  "workflowId": "<workflow>",
  "consultedAt": "<ISO>",
  "seatCount": 1,
  "seatRole": "staff-reader",
  "status": "complete",
  "filesRead": [{"path": "...", "version": "...", "entries": 13}],
  "dimensionsHit": [{"id": "riskRollback", "strength": "high", "evidence": "..."}],
  "highScoreRounds": [{"thinkingId": "...", "score": 47, "grade": "A"}],
  "talentSuggestions": [{"thinkingId": "...", "use": "...", "boundary": "..."}],
  "missingAngles": ["stakeholders", "..."],
  "recommendedExpansion": [{"order": 1, "action": "..."}],
  "limits": ["first-pass; not absolute truth"],
  "privacy": {"rawScreenshots": "not read", "chatBody": "not read/output", "tokens": "not read/output"}
}
```

必填：`consultationId/workflowId/consultedAt/seatCount/filesRead/dimensionsHit/missingAngles/recommendedExpansion/limits`。

## 5. 门禁

| Gate | 要求 |
|---|---|
| G1 咨询存在 | 有 consultation JSON，status complete |
| G2 读了参谋部 | filesRead 含 THINKING/EVALUATIONS/DIMENSIONS/PLAYBOOK |
| G3 命中/缺失 | 至少 1 个命中维度 + 1 个缺失/不适用角度 |
| G4 建议 | 明确 full/targeted + 3–5 维或 24 维 |
| G5 前置 | analyze 步骤 `depends_on: consult_staff` |
| G6 记录 | `dimensionRefs` 回写 evaluation/registry |

未过 G1–G5，不得进入 analyze；G6 在收口前完成。

## 6. 与模板

- `templates/thinking-workflow.yaml`：1 seat，`consult_staff` 先于 `analyze`。
- `templates/thinking-workflow-2seat.yaml`：2 seat，`consult_a`/`consult_b` 先于 `merge_consult`，再 `analyze`。
- 模板只给结构；不写死具体项目/分支。

## 7. 质量检查

- 咨询是否只复述索引，没有“对本任务”的判断？
- 是否漏掉安全/数据/回滚/未知？
- 是否把 first-pass 分数当绝对真理？
- 人才建议是否写证据 + 适用边界？
- 2 seat 是否真的独立，而不是互相抄？

## 8. 与其它协议

| 对象 | 关系 |
|---|---|
| `GENERAL-STAFF` | 咨询的上位标准；本协议是其强制步骤 |
| `THINKING-DIMENSIONS` | 命中/缺失维度的词典 |
| `THINKING-PLAYBOOK` | full/targeted 扩展方法 |
| `TALENT-LEDGER` | 咨询可引用方法样板；不选最终人才 |
| `STANDALONE-ROUND-PROTOCOL` | 思考类 SOLO 必须走本咨询 |
| `COMMAND-CENTER` | 长运行轮登记；咨询不替代 command center |
| R15/R16 | anchor R15，rejoin R16；不跳过 |

## 9. 变更记录

| 版本 | 日期 | 作者/角色 | 变更 |
|---|---|---|---|
| v1.0.0 | 2026-11-14 | builder / MAIN review | 建立强制咨询：1/2 seat、输入/输出字段、门禁、模板、质量检查。 |
| v1.0.1 | `<YYYY-MM-DD>` | `<maintainer>` | `<change>` |
