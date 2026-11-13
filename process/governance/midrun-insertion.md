# the assistant project · 中途插入内容标准协议（INSERT-GUARD）

- **协议版本**：`v1.0.0`（standard，2026-11-14）
- **状态**：`standard / reusable` —— 长期复用的标准协议，不是某次 INSERT-GUARD 的个案报告。
- **适用范围**：任意 rig / workflow / qitem / branch / 多轮支线 / 文档分析轮在运行中途收到新内容、新要求、新 bug、验收变化时的分类、排队、插入、回归。
- **维护者**：Lead/MAIN + QA lead；见 §12 变更记录。
- **配套模板**：`reports/operations/INSERTION-LEDGER-TEMPLATE.json`；示例分析：`reports/operations/MIDRUN-INSERTION.md` / `.json`。
- **铁律**：**插入不是重写当前轮：先记录，再分类；默认排队到下一轮；只有硬条件才打断当前轮/走 STOP-SWEEP。**

---

## 0. 如何使用本协议

### 0.1 三步

```text
收到插入
  → 写 INSERTION 记录（不直接改当前 packet）
  → 分类：CLARIFY / INLINE_EXTEND / NEXT_ROUND / SIDE_BRANCH / URGENT_STOP / GATE_CHANGE
  → 默认 NEXT_ROUND（或 owner 批准的 CLARIFY/INLINE_EXTEND）；当前轮继续
  → 硬条件命中 → URGENT_STOP / STOP-SWEEP
```

### 0.2 标准版如何复用

1. 不要复制本协议；它是标准件。
2. 复制 `reports/operations/INSERTION-LEDGER-TEMPLATE.json` 到 `reports/operations/insertions/<INSERT-ID>/INSERTION.json`，写 `INSERTION.md`。
3. 按下表替换占位符；不确定写 `UNKNOWN` + 负责人，不要猜。
4. 当前轮只读引用 `insertId`；不改当前 packet body/scope。
5. 分类/动作完成后更新 ledger；协议本身只在流程变化时升版。

### 0.3 占位符

| 占位符 | 含义 | 示例 |
|---|---|---|
| `<INSERT-ID>` | 插入 ID | `INSERT-20261114-01` |
| `<SOURCE>` | 来源 | `human` / `Lead` / `QA` / `MAIN` / `host` |
| `<RECEIVED-AT>` | 收到时间 | `2026-11-14T00:30:00+08:00` |
| `<ANCHOR>` | 主链锚点 | 当前默认 `R15` |
| `<CURRENT-ROUND>` | 当前轮/step | `R16` / `UX6-R15-02a` |
| `<BRANCH>` | 分支 + base/HEAD | `feat/... @ <commit>` |
| `<SCOPE>` | 受影响 write scope | `sim/app.js` / `U2a` |
| `<OWNER>` | 决策/执行 owner | `main-lead@...` / `QA` |
| `<INSERTION-POINT>` | 插入点 | `current-round` / `next-round` / `side-branch` / `stop-sweep` |
| `<REJOIN>` | 回归点 | 当前默认 `R16` |
| `<QA-REQUIRED>` | 是否 QA | `yes/no` + 原因 |
| `<STOP-SWEEP-REF>` | STOP-SWEEP/closeout | `STOP-...` / `null` |
| `<EVIDENCE>` | 证据 | path/command/summary |
| `<CONSUMED-BY>` | 消费方 | qitem/card/PR |

---

## 1. 六类插入

| 类 | 一句话 | 默认插入点 | 打断当前轮 | QA |
|---|---|---|---|---|
| `CLARIFY` | 澄清当前轮，不扩 scope | 当前轮 | 否 | 通常不需要 |
| `INLINE_EXTEND` | 当前轮可吸收的小扩展 | 当前轮（更新卡/证据） | 否（需 owner 确认） | 验收变则要 |
| `NEXT_ROUND` | 新内容排当前分支下一轮 | 下一轮 | 否 | 按下一轮卡 |
| `SIDE_BRANCH` | 独立支线/新分支 | 新支线 | 否 | 按支线门 |
| `URGENT_STOP` | 当前轮已不安全/会污染结论 | STOP-SWEEP | **是** | 必须 |
| `GATE_CHANGE` | 验收/契约变更，当前结果失效 | 冻结 + 重开/重跑 | **是** | 必须 |

### 1.1 `CLARIFY`

- **触发**：对当前卡/验收/命令/术语的疑问；不改变目标/scope/gate。
- **允许**：当前轮回答；卡/证据追加 clarification note；更新 notes/evidence。
- **禁止**：偷换成新需求；改验收/代码范围；以澄清跳过 gate。
- **插入点**：当前轮。**Owner**：当前 builder/Lead。**证据**：insertion record + answer/note。**回归**：当前轮原验收。
- **QA**：通常不需要；影响验收时转 `GATE_CHANGE`。

### 1.2 `INLINE_EXTEND`

- **触发**：与当前轮同源、当前 write scope 内可完成；不改 gate/验收；小 bug/边界/文案/测试补充。
- **允许**：当前 builder 评估后吸收；更新卡/验收/证据/测试；记录 `decision=absorbed_inline` + owner approval。
- **禁止**：扩 write scope；改 gate/主链编号；未 owner 确认静默塞入；把插入当原始验收。
- **插入点**：当前轮（更新卡/证据）。**Owner**：当前 builder + Lead 确认。**证据**：record/card change/test/diff。**回归**：当前轮验收 + 小回归。
- **QA**：验收变化必须介入；否则当前轮 QA 回归覆盖。

### 1.3 `NEXT_ROUND`

- **触发**：新需求/新 bug/改进，当前轮不宜吸收；需要新卡/新 write scope/新验收；当前轮接近收口。
- **允许**：创建 record + qitem；排当前分支下一轮；下一轮卡引用 `insertId`。
- **禁止**：直接改当前 packet body/scope；塞当前轮证据；未记录口头承诺；跳过下一轮 QA。
- **插入点**：下一轮。**Owner**：Lead/PM 排轮；下一轮 builder 消费。**证据**：record/qitem/next card。**回归**：下一轮验收。
- **默认**：绝大多数插入走这类。

### 1.4 `SIDE_BRANCH`

- **触发**：新内容独立于当前分支/轮次；跨仓库/原生/较长周期；需要独立 write scope/QA/合并路径；硬塞会 scope drift。
- **允许**：按 `docs/BRANCHING-PROTOCOL.md` 建支线；锚定最后闭合轮；记录 base/owner/rejoin；更新 ledger/reference index。
- **禁止**：当前分支混做；未锚定/未 ledger 就开分支；跨 `bridge-app` 混入 Web 支线；未 QA 合并。
- **插入点**：新支线（`feat/...`/`ANDROID-*`）。**Owner**：Lead/PM 建；支线 owner 执行。**证据**：record/branch doc/ledger/base。**回归**：支线门 + 主链 rejoin（当前 R16）。

### 1.5 `URGENT_STOP`

**硬触发（任一）**

- scope 被破坏/无法界定边界；
- gate/验收被破坏，继续会污染结论；
- 安全/隐私（token/截图/聊天/密钥/未授权）；
- 数据损坏/丢失/不可逆/生产误改；
- 分支基线不明/dirty 冲突/force/rebase 破坏；
- 用户明确立即停止/live 影响。

- **允许**：立即 0–5min 冻结；走 `docs/CLOSEOUT-MANUAL.md` + `reports/operations/STOP-SWEEP.md`；记录 insertion + stop record；交独立 QA。
- **禁止**：继续当前轮“先做完”；静默修数据/重建分支；删证据/清锁；把 URGENT_STOP 当 NEXT_ROUND 排队。
- **插入点**：STOP-SWEEP。**Owner**：orchestrator/Lead 立即；QA/MAIN 决策。**证据**：record/stop record/freeze checklist/QA。**回归**：closeout 后回 R16。

### 1.6 `GATE_CHANGE`

- **触发**：验收标准/契约/API/schema/主链轮次目标变化；当前结果不再有效；用户/MAIN 改需求/gate；发现原 gate 错误。
- **允许**：冻结当前轮；记录 `invalidates_current=true`；MAIN/QA 重定 gate/轮次；旧结果标 `invalidated`；新卡/新轮重跑；必要时 STOP-SWEEP。
- **禁止**：直接改验收后把旧结果算 PASS；复用旧证据；未 MAIN/QA 批准就改 gate；把 GATE_CHANGE 当 INLINE_EXTEND。
- **插入点**：冻结 + 新轮/新 gate。**Owner**：MAIN + QA；builder 只做影响评估。**证据**：gate record/old invalidated/new card/regression。**回归**：新 gate 全量回归 + R16/分支收敛。

---

## 2. 默认策略：先记录，默认排队

```text
收到插入
  → INSERTION record（唯一 ID）
  → 分类（六类）
  → 默认 NEXT_ROUND
  → 当前轮继续；下一轮/支线消费
  → 硬条件 → URGENT_STOP / STOP-SWEEP
```

**为什么**

- 当前轮有卡/验收/证据链；中途改 scope 会让 gate/QA 分不清“原始验收 vs 插入”。
- 插入排队保留来源/owner/时间/锚点，下一轮可审计消费。
- “顺手做”会造成 scope drift；只有硬条件值得停。

**队列形态**

- 文件：`reports/operations/insertions/<INSERT-ID>/INSERTION.json` + `INSERTION.md`。
- qitem：`rig queue create ... --tags insertion:<INSERT-ID>,... --destination <next-owner>`。
- 当前轮只读引用 `insertId`；不改 body/scope。

---

## 3. 硬中止条件

| 条件 | 例子 | 动作 |
|---|---|---|
| scope 破坏 | 改 write scope 外；无法界定 | 冻结 + STOP-SWEEP |
| gate/验收破坏 | 当前结果不满足 gate；继续污染 | 冻结 + QA/MAIN |
| 安全/隐私 | token/截图/聊天/密钥/未授权 | 冻结 + 安全处理 + STOP-SWEEP |
| 数据风险 | 丢数据/不可逆迁移/生产误改 | 冻结 + 备份 + STOP-SWEEP |
| 分支基线 | base/HEAD 不明；dirty 冲突；force/rebase | 冻结 + STOP-SWEEP |
| 用户/live | 明确停止；生产影响 | 冻结 + STOP-SWEEP |

判定：**继续会让结论不可信/不可回滚 → STOP-SWEEP，不是插入队列。**

---

## 4. 插入记录字段

```json
{
  "insertId": "INSERT-YYYYMMDD-NN",
  "source": "<human|seat|host|QA|MAIN>",
  "receivedAt": "<ISO>",
  "anchor": "<R15/R16/branch>",
  "currentRound": "<R16 / UX6-R15-02a>",
  "branch": "<branch + base/HEAD>",
  "scope": "<write scope/files>",
  "classification": "<CLARIFY|INLINE_EXTEND|NEXT_ROUND|SIDE_BRANCH|URGENT_STOP|GATE_CHANGE>",
  "decision": "<absorbed_inline|queued_next|new_branch|stopped|gate_reopened|clarified|rejected>",
  "owner": "<session/role>",
  "status": "<RECEIVED|CLASSIFIED|QUEUED|CONSUMED|STOPPED|REJECTED|CLOSED|GATE_REOPENED>",
  "insertionPoint": "<current-round|next-round|side-branch|stop-sweep>",
  "rejoin": "<R16/branch gate>",
  "qaRequired": "<yes/no + reason>",
  "stopSweepRef": "<STOP-SWEEP/closeout|null>",
  "evidence": ["<path/command/summary>"],
  "consumedBy": "<qitem/card/PR|null>",
  "notes": "<short>"
}
```

完整模板：`reports/operations/INSERTION-LEDGER-TEMPLATE.json`。

---

## 5. 生命周期

```text
RECEIVED → CLASSIFIED → QUEUED → CONSUMED → CLOSED
                     ├→ STOPPED (URGENT_STOP)
                     ├→ REJECTED (不做，记录理由)
                     └→ GATE_REOPENED (GATE_CHANGE)
```

- `RECEIVED`：记录已建；当前轮不动。
- `CLASSIFIED`：owner 已定类/插入点。
- `QUEUED`：qitem/ledger 已排下一轮/支线。
- `CONSUMED`：下一轮/支线已引用并完成。
- `CLOSED`：验收/证据完成。
- `STOPPED`：URGENT_STOP/STOP-SWEEP；记录 closeout ID。
- `REJECTED`：不做；写理由/owner，不删记录。
- `GATE_REOPENED`：GATE_CHANGE；旧结果 invalidated。

---

## 6. QA / STOP-SWEEP / 分支收敛 / R15-R16

### 6.1 QA 何时介入

| 类 | QA |
|---|---|
| CLARIFY | 通常不需要；影响验收时转 GATE_CHANGE |
| INLINE_EXTEND | 验收变化必须；否则当前轮 QA 回归覆盖 |
| NEXT_ROUND | 下一轮 QA 门 |
| SIDE_BRANCH | 支线收敛门 |
| URGENT_STOP | 必须独立 QA |
| GATE_CHANGE | 必须独立 QA/MAIN |

### 6.2 何时 STOP-SWEEP

- `URGENT_STOP` 硬条件命中 → 直接 STOP-SWEEP。
- `GATE_CHANGE` 若当前轮结果失效/需冻结 → STOP-SWEEP 的冻结/收尾，或 MAIN/QA 重开。
- 其他类不默认 STOP-SWEEP。

### 6.3 分支收敛

- `NEXT_ROUND`：当前分支下一轮；不新建分支。可落成单独轮（`SOLO-YYYYMMDD-NN`），按 `docs/rounds/STANDALONE-ROUND-PROTOCOL.md`。
- `SIDE_BRANCH`：按 BRANCHING-PROTOCOL 新建，锚定最后闭合轮；更新 ledger/index。独立的一次性工作也可落成单独轮（见 `docs/rounds/STANDALONE-ROUND-PROTOCOL.md`）。
- `GATE_CHANGE`：可能使当前分支结果失效；QA/MAIN 决定重跑/废弃。
- `URGENT_STOP`：冻结分支；未 QA 前不 merge/delete。

### 6.4 R15/R16

- 主链当前：最后闭合 R15，R16 NEED_MAIN；插入不跳过 R16。
- `NEXT_ROUND` 在 R16 完成后按主链顺序消费；`SIDE_BRANCH` rejoin R16。
- `GATE_CHANGE` 若改主链验收，必须 MAIN 批准，仍回 R16 重新验收。
- 不把插入写进 R15 已完成记录；不篡改历史。

---

## 7. OpenRig 命令

> 草案；执行前先记录 INSERTION，再按分类动作。

### 7.1 通知/读取

```bash
rig send <owner-session> "INSERTION <INSERT-ID>: <one-line>; details reports/operations/insertions/<INSERT-ID>/"
rig queue list --json
rig workflow status --json
```

### 7.2 排队

```bash
# NEXT_ROUND
rig queue create \
  --destination <next-owner> \
  --summary "INSERTION <ID>: <summary>" \
  --body-file reports/operations/insertions/<INSERT-ID>/INSERTION.md \
  --tags insertion:<INSERT-ID>,next-round \
  --priority <routine|urgent> --json

# SIDE_BRANCH
rig queue create \
  --destination <branch-owner> \
  --summary "INSERTION <ID>: new side branch" \
  --body-file reports/operations/insertions/<INSERT-ID>/INSERTION.md \
  --tags insertion:<INSERT-ID>,side-branch --json
```

### 7.3 当前轮正常收口/交下一轮

```bash
rig workflow project --instance <id> --current-packet <qitem> \
  --exit done --actor-session <session> --evidence-ref <path> --json

rig workflow project --instance <id> --current-packet <qitem> \
  --exit handoff --next-owner <next-owner> --json
```

### 7.4 紧急/gate

```bash
# URGENT_STOP
rig workflow abort <instanceId> --reason "URGENT_STOP: <reason>" --actor-session <session> --json
# then CLOSEOUT-MANUAL QA closeout

# GATE_CHANGE
rig queue update <qitem> --state blocked --blocked-on "gate:<what>" \
  --summary "GATE_CHANGE: <what>" --evidence-ref <path> --json
```

### 7.5 不能做什么

- 直接改当前 qitem body/scope 来“吸收”插入；把插入写进当前证据当原始验收。
- 用 `done` 关闭当前轮“腾地方”；用 `rig send` 代替持久记录。
- URGENT_STOP 后继续跑；未 QA merge/delete/清锁。
- 把 NEXT_ROUND 插到 R15 历史或跳过 R16。
- 把 SIDE_BRANCH 混进当前 Web 分支/`bridge-app` 外仓。

---

## 8. 插入验收

- [ ] 唯一 `INSERT-ID` + 持久记录（不是只发消息）。
- [ ] 六类分类明确；默认不打断当前轮。
- [ ] 当前轮 body/scope 未被静默修改。
- [ ] `INLINE_EXTEND` 有 owner 确认 + 验收/回归更新。
- [ ] `NEXT_ROUND` 有 qitem/owner/下一轮卡。
- [ ] `SIDE_BRANCH` 有 branch doc/ledger/base/rejoin。
- [ ] `URGENT_STOP` 已冻结并走 STOP-SWEEP。
- [ ] `GATE_CHANGE` 旧结果 invalidated；MAIN/QA 批准。
- [ ] 证据不含原始截图/聊天/token；index/ledger 已更新。
- [ ] R15/R16 锚点未被跳过。

---

## 9. 当前实例参考（非协议标准依赖）

- `reports/operations/MIDRUN-INSERTION.md` / `.json`（本次分析/示例）
- `docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`（当前支线）
- `reports/sctg/FORMAL-RUN-STATE.json`（R16 NEED_MAIN）
- 当前实例的插入记录放 `reports/operations/insertions/`，不回写本协议。

## 10. 引用

- `docs/BRANCHING-PROTOCOL.md`
- `docs/CLOSEOUT-MANUAL.md`
- `reports/operations/STOP-SWEEP.md` / `.json`
- `reports/operations/INSERTION-LEDGER-TEMPLATE.json`
- `docs/branches/REFERENCE-INDEX.md`
- `docs/rounds/STANDALONE-ROUND-PROTOCOL.md`（NEXT_ROUND/SIDE_BRANCH 可落成单独轮）
- `reports/branches/SYNC-GUARD.md`、`reports/branches/SYNC-MANIFEST.json`
- `reports/sctg/FORMAL-RUN-STATE.json`

## 11. 不做什么

- 本协议不实现产品代码/不改当前轮/不建切分支/不 merge/delete。
- 不替代 `STOP-SWEEP`/`CLOSEOUT-MANUAL`；紧急/验收变更按其执行。
- 不把原始截图/聊天正文/token/logcat 写入插入记录/证据。

## 12. 变更记录

| 版本 | 日期 | 作者/角色 | 变更 |
|---|---|---|---|
| v1.0.0 | 2026-11-14 | builder / MAIN review | 建立标准协议：六类插入、默认排队、硬中止、记录字段/生命周期、QA/STOP-SWEEP/分支/R15-R16、命令草案。 |
| v1.0.1 | `<YYYY-MM-DD>` | `<maintainer>` | `<change>` |

> 版本规则：分类/插入点/硬条件/记录字段变化 → 升版并写记录；仅某次插入数据变化不改协议。
