# 单独轮标准协议（STANDALONE ROUND）

- **协议版本**：`v1.0.1`（standard，2026-11-14）
- **状态**：`standard / reusable` —— 长期复用的标准协议，不是某次临时任务说明。
- **规范名**：**单独轮**（STANDALONE）
- **别名**：离散轮（DISCRETE）、零散轮（SCATTERED）
- **ID**：`SOLO-YYYYMMDD-NN`
- **适用范围**：不属于正式 30 轮产品序列、一次一议、目标相对独立、需要明确 anchor/branch/rejoin/scope/gate/QA/evidence 的工作。
- **维护者**：Lead/MAIN + QA lead；见 §11 变更记录。
- **配套模板**：`docs/rounds/STANDALONE-ROUND-TEMPLATE.md`、`reports/rounds/STANDALONE-ROUND-TEMPLATE.json`
- **台账**：`reports/rounds/STANDALONE-ROUNDS.json` / `.md`（初始盘点见 g2）
- **铁律**：单独轮不是“临时做一下”；必须有 ID、边界、策略、gate、QA、证据、生命周期。

---

## 0. 定义

### 0.1 什么是单独轮

- 不属于正式 30 轮（R01–R30），不占用 R 编号。
- 一次一议、目标相对独立；通常 1 个主策略 + 可选次策略。
- 有明确 `anchor`（主链锚点/最后闭合轮）、`branch`（执行分支/工作区）、`rejoin`（回归点）。
- 有 `scope`、`strategy`、`gate`、`qa`、`evidence`、`lifecycle`。
- 完成后必须 `CLOSED` / `ABANDONED` / `ARCHIVED`，不能永久漂移或变成永久 dirty 工作树。

### 0.2 不是什么

- 不是正式 30 轮：不能改 R 编号、不能跳过 R16、不能把 R16 NEED_MAIN 写成 PASS。
- 不是长期支线：需要多轮/持续合并的，按 `docs/BRANCHING-PROTOCOL.md` 建支线，不叫单独轮。
- 不是插入协议：中途插入先按 `docs/MIDRUN-INSERTION-PROTOCOL.md` 分类；`NEXT_ROUND`/`SIDE_BRANCH` 可落成单独轮。
- 不是 STOP-SWEEP：紧急停止/收尾按 `docs/CLOSEOUT-MANUAL.md`；单独轮只在 `RECOVERY` 策略里消费 STOP-SWEEP 结果。
- 不是“无 gate 的随手活”：任何单独轮都要有 gate/QA/evidence。

---

## 1. 与正式 30 轮 / 支线 / 插入 / STOP-SWEEP 的边界

| 对象 | 关系 | 边界 |
|---|---|---|
| **正式 30 轮** | 独立但不越权 | 单独轮不占用 R 编号；anchor 用最后闭合轮（当前 R15），rejoin 用当前回归点（R16）；不改 R16 结论、不跳过 |
| **支线（UX6/QUIET）** | 可消费/可派生 | 多轮、持续合并、需要 branch ledger 的走支线；单独轮是一次性容器，结束即关闭；需要多轮 → 升级为支线 |
| **插入轮（INSERT-GUARD）** | 上游分类 | `CLARIFY`/`INLINE_EXTEND` 不建单独轮；`NEXT_ROUND`/`SIDE_BRANCH` 可建单独轮；`URGENT_STOP`/`GATE_CHANGE` 走 STOP-SWEEP/MAIN |
| **STOP-SWEEP** | 恢复/收尾 | 紧急停止先走 STOP-SWEEP；单独轮 `RECOVERY` 策略消费 closeout 结果；不能用单独轮替代 STOP-SWEEP |
| **监控台/issue 分析等已发生工作** | 可登记 | 已有 discussions/reports 的离散工作可在 registry 标 `confirmed/candidate/out-of-scope`；不追溯改历史 |

---

## 2. 策略（主策略必选一个）

| 策略 | 适用 | 禁止 | 默认 gate | QA |
|---|---|---|---|---|
| `ANALYZE` | 只读分析/调研/对比/盘点 | 改产品代码；无证据断言 | 证据可复核 + 独立 review | 建议独立 QA |
| `GOVERN` | 流程/协议/模板/治理/索引 | 改产品代码；无版本/变更记录 | docs consistency + review + MAIN（涉及标准件） | QA/MAIN |
| `OPS` | 运维/清扫/同步/恢复/巡检 | 未授权破坏性动作；清锁/杀服务 | 命令证据 + 回滚 + QA | QA |
| `QA` | 审查/验收/回归/独立复核 | 实现；改被测代码 | 只读证据 + verdict（PASS/NEED_MAIN/BLOCKED） | 独立 QA |
| `SMALL_FIX` | 小范围代码修复 | 扩 scope；无测试/回滚；跨仓 | 测试 + diff + QA + 回滚 | QA 必须 |
| `RESEARCH` | 技术选型/探索/原型 | 生产代码；伪造实测；无边界 | 决策文档 + 证据/未验证标注 | 建议 review |
| `RECOVERY` | 停止后收尾/恢复/归档 | 未 QA 删除/合并；重写历史 | CLOSEOUT-MANUAL + STOP-SWEEP + QA 分类 | QA 必须 |

**次策略**：可带一个，但必须写清“主策略 + 次策略”；gate 以主策略为准，次策略只补充。

---

## 3. 必填字段

```json
{
  "id": "SOLO-YYYYMMDD-NN",
  "title": "<short title>",
  "aliases": ["DISCRETE", "SCATTERED"],
  "anchor": "<R15/current mainline anchor>",
  "branch": "<branch/worktree@commit>",
  "rejoin": "<R16/current rejoin>",
  "scope": "<write scope / read-only scope>",
  "strategy": "<ANALYZE|GOVERN|OPS|QA|SMALL_FIX|RESEARCH|RECOVERY>",
  "secondaryStrategy": "<optional>",
  "gate": "<what must pass>",
  "qa": "<independent QA owner/required?>",
  "evidence": ["<paths/commands>"],
  "lifecycle": "<PROPOSED|ACTIVE|QA|CLOSED|ABANDONED|ARCHIVED|BLOCKED>",
  "owner": "<session/role>",
  "source": "<discussion/report/issue/insertion>",
  "status": "<current status>",
  "createdAt": "<ISO>",
  "updatedAt": "<ISO>",
  "writeScope": ["<files/dirs>"],
  "rollback": "<command/path>",
  "closeout": "<CLOSE_OUT|ABANDON|ARCHIVE_RECYCLE|pending>",
  "insertionRef": "<INSERT-ID|null>",
  "stopSweepRef": "<STOP-SWEEP/closeout|null>",
  "related": ["<branch/round/issue>"],
  "notes": "<short, no sensitive content>"
}
```

完整模板：`reports/rounds/STANDALONE-ROUND-TEMPLATE.json`。

---

## 4. 生命周期

```text
PROPOSED → ACTIVE → QA → CLOSED
                    ├→ BLOCKED (waiting/need-info; with wake)
                    ├→ ABANDONED (stopped/no merge; reason)
                    └→ ARCHIVED (no active refs; archive + QA)
```

- `PROPOSED`：已登记，未开工；需 owner/anchor/scope。
- `ACTIVE`：执行中；有 qitem/卡/证据。
- `QA`：独立验收；不得 builder 自检。
- `CLOSED`：验收/证据/关闭记录齐全；不留下永久 dirty/分支（需要保留的按支线）。
- `BLOCKED`：等人/外部；写 blocker + wake/continuation，不能静默。
- `ABANDONED`：明确不做/不合并；写理由/证据；不删引用。
- `ARCHIVED`：无活跃引用；归档 + manifest/hash + QA 签字；再回收。

**关闭条件**：`CLOSED` 必须有 gate/QA/evidence/rollback；`ABANDONED` 必须有 reason/owner/evidence；`ARCHIVED` 必须有 archive path/hash/QA。

---

## 5. 模板与台账使用

1. 复制 `docs/rounds/STANDALONE-ROUND-TEMPLATE.md` 到 `reports/rounds/active/<SOLO-ID>.md`（或 qitem body）。
2. 复制 `reports/rounds/STANDALONE-ROUND-TEMPLATE.json` 到 `reports/rounds/active/<SOLO-ID>.json`。
3. 替换所有 `<...>`；不确定写 `UNKNOWN` + owner，不要猜。
4. 在 `reports/rounds/STANDALONE-ROUNDS.json` / `.md` 登记（g2 初始台账；后续追加）。
5. 完成后按生命周期关闭；证据放 `reports/rounds/evidence/<SOLO-ID>/`。
6. 识别标戳：每个单独轮根目录写 `.solo-round.json`；标准见 `docs/rounds/SOLO-STAMP-PROTOCOL.md`，工具 `tools/solo-round-stamp.mjs`。stamp 是主真值；主文档 marker 可选。

---

## 6. 门禁与 QA

- `ANALYZE`/`RESEARCH`：证据可复核 + 独立 review；不伪造实测。
- `GOVERN`：文档一致性（`node tools/check-docs-consistency.mjs` 如适用）+ 版本/变更记录 + review。
- `OPS`：只读命令/回滚/端口/锁证据；破坏性动作需明确授权。
- `QA`：只读 + verdict；不改被测对象。
- `SMALL_FIX`：目标测试 + 回归 + diff + QA + 回滚；write scope 不得扩。
- `RECOVERY`：CLOSEOUT-MANUAL 的 0–5min 冻结 + QA 分类；不跳过。

**QA 独立性**：实现者不能给自己做 QA；单独轮也要独立 QA/Lead。R16/Android/隐私门由 MAIN/人工。

---

## 7. 与 R15/R16 锚点

- 当前主链：最后闭合 `R15`，回归 `R16`（NEED_MAIN）。
- 单独轮 `anchor` 默认 R15，`rejoin` 默认 R16；不得跳过 R16。
- 单独轮不修改 R15 已完成记录；不改 R16 的 NEED_MAIN 状态。
- 需要改主链验收/顺序 → `GATE_CHANGE` + MAIN，不自行改 R 编号。

---

## 8. 防止“永久单独轮”

- 每个单独轮必须有 `closeBy`/计划关闭时间（建议 ≤7 天；长任务升级为支线）。
- 不允许永久分支/永久 dirty 工作树；`CLOSED`/`ABANDONED`/`ARCHIVED` 必须处理工作树/分支。
- 连续 `BLOCKED` 超期 → 升级给 Lead/MAIN；不能静默挂着。
- 同一主题第 2 次单独轮 → 评估升级为支线/正式轮，避免碎片化。

---

## 9. 与其他协议的双向引用

- 分支：`docs/BRANCHING-PROTOCOL.md`
- 插入：`docs/MIDRUN-INSERTION-PROTOCOL.md`
- 收尾：`docs/CLOSEOUT-MANUAL.md`
- 引用索引：`docs/branches/REFERENCE-INDEX.md`
- 标戳：`docs/rounds/SOLO-STAMP-PROTOCOL.md`、`tools/solo-round-stamp.mjs`
- 总参谋部：`docs/general-staff/GENERAL-STAFF.md`、`reports/general-staff/THINKING-ROUNDS.json`（思考类 SOLO 的 THINK ID/评估）
- 同步：`reports/branches/SYNC-GUARD.md`、`reports/branches/SYNC-MANIFEST.json`

## 10. 不做什么

- 不占正式 R 编号、不跳过 R16、不把 NEED_MAIN 写成 PASS。
- 不建永久分支/永久 dirty；不把单独轮当长期支线。
- 不把插入/停止/验收变更硬塞进单独轮；按 INSERT-GUARD/STOP-SWEEP/GATE_CHANGE。
- 不提交原始截图/聊天正文/token/logcat。

## 11. 变更记录

| 版本 | 日期 | 作者/角色 | 变更 |
|---|---|---|---|
| v1.0.0 | 2026-11-14 | builder / MAIN review | 建立标准：定义、别名、ID、与正式轮/支线/插入/STOP-SWEEP 边界、七种策略、必填字段、生命周期、模板/台账、门禁/QA、R15/R16、防漂移。 |
| v1.0.1 | 2026-11-14 | builder / MAIN review | 增加 `.solo-round.json` 识别标戳要求与 `SOLO-STAMP-PROTOCOL`/工具引用。 |

> 版本规则：定义/策略/字段/生命周期变化 → 升版并写记录；单次实例数据只进 registry/ledger，不改协议。
