# MIDRUN-INSERTION · 中途插入内容分类与边界

- 日期：2026-11-14
- 类型：治理/流程分析；**不改产品代码、不改当前轮、不重写历史**。
- 输入：`discussions/insert-guard-20261114/BRIEF.md`、`docs/BRANCHING-PROTOCOL.md`、`docs/CLOSEOUT-MANUAL.md`、`docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`、`docs/branches/REFERENCE-INDEX.md`、`reports/branches/SYNC-GUARD.md`、`reports/branches/SYNC-MANIFEST.json`、`reports/sctg/FORMAL-RUN-STATE.json`
- 机器可读：`reports/operations/MIDRUN-INSERTION.json`
- 标准版：i2 将写 `docs/MIDRUN-INSERTION-PROTOCOL.md` 与 `reports/operations/INSERTION-LEDGER-TEMPLATE.json`

## 0. 一句话原则

**插入不是重写当前轮：先记录，再分类；默认排队到下一轮，只有硬条件才打断当前轮/走 STOP-SWEEP。**

六类插入：

| 类 | 一句话 | 默认插入点 | 是否打断当前轮 | QA |
|---|---|---|---|---|
| `CLARIFY` | 澄清当前轮，不扩 scope | 当前轮 | 否 | 通常不需要 |
| `INLINE_EXTEND` | 当前轮可吸收的小扩展 | 当前轮（更新卡/证据） | 否（需 owner 确认） | 验收变则要 |
| `NEXT_ROUND` | 新内容排到当前分支下一轮 | 下一轮 | 否 | 按下一轮卡 |
| `SIDE_BRANCH` | 独立支线/新分支 | 新支线 | 否 | 按支线门 |
| `URGENT_STOP` | 当前轮已不安全/会污染结论 | STOP-SWEEP | **是** | 必须 |
| `GATE_CHANGE` | 验收/契约变更，当前结果失效 | 冻结 + 重开/重跑 | **是** | 必须 |

**默认策略**：任何新内容先进入 insertion ledger/queue，不直接改当前 packet body/scope；由 owner 分类后决定当前轮吸收还是下一轮消费。

---

## 1. 插入分类定义

### 1.1 `CLARIFY`（澄清）

**触发**

- 对当前卡/验收/命令/术语的疑问；不改变目标、scope、gate。
- 用户/QA/Lead 要求解释、补充上下文。

**允许**

- 在当前轮回答/补文档；在卡/证据中追加 clarification note。
- 更新 `notes`/`evidence`，不扩 write scope。

**禁止**

- 把澄清偷换成新需求；改验收标准；改代码范围。
- 用澄清名义跳过 gate。

**插入点**：当前轮（对话/卡 note）。
**Owner**：当前 builder/Lead（答复者）；QA 仅在澄清影响验收时介入。
**证据**：插入记录 + 答复/卡 note；不要求新 qitem。
**回归点**：当前轮原验收；不新增回归。

### 1.2 `INLINE_EXTEND`（同轮小扩展）

**触发**

- 新内容与当前轮目标同源、能在当前 write scope 内完成；不改 gate/验收。
- 小 bug/边界/文案/测试补充；预计不改变轮次结论。

**允许**

- 当前 builder 评估后吸收；更新卡/验收/证据；补测试。
- 在插入记录里写 `decision=absorbed_inline` + `owner_approval`。

**禁止**

- 扩 write scope、改 gate、改主链编号；把大需求拆成“顺手做”。
- 未 owner 确认就静默塞入；把插入当当前轮原始验收。

**插入点**：当前轮，更新卡/证据。
**Owner**：当前 builder + Lead（必须确认）。
**证据**：插入记录、卡变更、测试/回归、diff。
**回归点**：当前轮验收 + 新增小回归；QA 在验收变化时介入。

### 1.3 `NEXT_ROUND`（下一轮）

**触发**

- 新需求/新 bug/改进，当前轮不宜吸收；但属于当前分支的下一轮。
- 需要新卡/新 write scope/新验收，或当前轮已接近收口。

**允许**

- 创建 insertion record + qitem（`insertion:<id>`），排到当前分支下一轮。
- 在下一轮卡中引用 insertion ID；当前轮不改。

**禁止**

- 直接改当前 packet body/scope；把新内容塞进当前轮证据。
- 未记录就口头承诺；跳过下一轮 QA。

**插入点**：当前分支下一轮。
**Owner**：Lead/PM 排轮；下一轮 builder 消费。
**证据**：insertion record + qitem + 下一轮卡/证据。
**回归点**：下一轮验收；当前轮不受影响。

### 1.4 `SIDE_BRANCH`（独立支线）

**触发**

- 新内容独立于当前分支/轮次，跨仓库/原生/较长周期；需要独立 write scope/QA/合并路径。
- 与当前支线目标不同，硬塞会造成 scope drift。

**允许**

- 按 `docs/BRANCHING-PROTOCOL.md` 建支线：锚定最后闭合轮，记录 base/owner/rejoin。
- 更新 branch ledger + reference index；当前分支不动。

**禁止**

- 在当前分支混做；未锚定/未 ledger 就开分支；跨 `bridge-app` 混入 Web 支线。
- 未 QA 合并回当前分支。

**插入点**：新支线（`feat/...` 或 `ANDROID-*`）。
**Owner**：Lead/PM 建支线；支线 owner 执行。
**证据**：insertion record + branch doc + ledger + base commit。
**回归点**：支线收敛门 + 主链 rejoin（当前 R16）。

### 1.5 `URGENT_STOP`（紧急中止）

**触发（硬条件，任一）**

- scope 被破坏：当前轮写到了 write scope 外，或无法界定改动边界。
- gate/验收被破坏：当前轮结果已不满足 gate，继续会污染结论。
- 安全/隐私：token/原始截图/聊天正文/密钥泄露风险，或未授权访问。
- 数据：可能损坏/丢失数据，schema/迁移不可逆，或生产数据被误改。
- 分支基线：base/HEAD 不明、dirty 冲突、force push/rebase 破坏、分支被覆盖。
- 用户明确要求立即停止；或 live/生产影响。

**允许**

- 立即冻结（0–5min），走 `docs/CLOSEOUT-MANUAL.md` + `reports/operations/STOP-SWEEP.md`。
- 记录 insertion + stop record；交独立 QA。

**禁止**

- 继续当前轮“先做完再说”；静默修数据/重建分支；删证据/清锁。
- 把 URGENT_STOP 当 NEXT_ROUND 排队。

**插入点**：STOP-SWEEP。
**Owner**：orchestrator/Lead 立即执行；QA/MAIN 决策。
**证据**：insertion record + stop record + 0–5min 冻结清单 + QA 分类。
**回归点**：STOP-SWEEP 收尾后回 R16；不跳过。

### 1.6 `GATE_CHANGE`（验收/契约变更）

**触发**

- 验收标准、契约、API/schema、主链轮次目标变化；当前轮结果不再有效。
- 用户/MAIN 改需求/范围/gate；或发现原 gate 错误。

**允许**

- 冻结当前轮；记录 `invalidates_current=true`；由 MAIN/QA 重新定 gate/轮次。
- 当前轮结果标 `invalidated`；新卡/新轮重跑；必要时 STOP-SWEEP 收尾。

**禁止**

- 直接改当前轮验收后把旧结果算 PASS；复用旧证据。
- 未 MAIN/QA 批准就改 gate；把 GATE_CHANGE 当 INLINE_EXTEND。

**插入点**：当前轮冻结 + 新轮/新 gate。
**Owner**：MAIN + QA；builder 只提供影响评估。
**证据**：gate 变更记录、旧结果 invalidated、新卡/新验收、回归。
**回归点**：新 gate 全量回归 + R16 锚点/分支收敛。

---

## 2. 默认策略：不打断，先排队

```text
收到新内容
  → 写 insertion record（不直接改当前 packet）
  → 分类（CLARIFY / INLINE_EXTEND / NEXT_ROUND / SIDE_BRANCH / URGENT_STOP / GATE_CHANGE）
  → 默认 NEXT_ROUND（或 CLARIFY/INLINE_EXTEND 经 owner 确认）
  → 当前轮继续；下一轮/支线消费
  → 硬条件命中 → URGENT_STOP/STOP-SWEEP
```

**为什么默认不打断**

- 当前轮已有卡/验收/证据链；中途改 scope 会让 gate/QA 无法判断“原始验收 vs 插入”。
- 插入排队可保留来源/owner/时间/锚点，下一轮可审计消费。
- 真正需要停的只有硬条件；其余“顺手做”会造成 scope drift。

**插入队列形态**

- 文件：`reports/operations/insertions/<INSERT-ID>/INSERTION.json` + `INSERTION.md`（由 ledger 模板复制）。
- 队列：`rig queue create` 一条 qitem，tags 含 `insertion:<INSERT-ID>`，destination=下一轮 owner。
- 当前轮只读引用 insertion ID；不改 body/scope。

---

## 3. 硬中止条件（必须走 STOP-SWEEP）

| 条件 | 例子 | 立即动作 |
|---|---|---|
| scope 破坏 | 改了 write scope 外文件；无法界定改动 | 冻结 + STOP-SWEEP |
| gate/验收破坏 | 当前结果已不满足 gate；继续会污染 | 冻结 + QA/MAIN |
| 安全/隐私 | token/截图/聊天/密钥泄露；未授权访问 | 冻结 + 安全处理 + STOP-SWEEP |
| 数据风险 | 可能丢数据/不可逆迁移/生产误改 | 冻结 + 备份 + STOP-SWEEP |
| 分支基线 | base/HEAD 不明；dirty 冲突；force/rebase 破坏 | 冻结 + STOP-SWEEP |
| 用户/live | 明确停止；生产/live 影响 | 冻结 + STOP-SWEEP |

**判定**：只要“继续当前轮会让结论不可信/不可回滚”，就不是插入队列，而是 STOP-SWEEP。

---

## 4. 插入记录字段

每次插入必须有一条记录（不要只靠聊天记忆）：

| 字段 | 说明 |
|---|---|
| `insertId` | `INSERT-YYYYMMDD-NN`，全局唯一 |
| `source` | 人/seat/host/QA/MAIN；不要只写“用户” |
| `receivedAt` | ISO 8601 |
| `anchor` | 主链锚点（当前 R15）/当前轮（R16）/支线 |
| `currentRound` | 当前轮/step，如 `R16` / `UX6-R15-02a` |
| `branch` | 当前分支 + base/HEAD |
| `scope` | 受影响的 write scope/文件/模块 |
| `classification` | 六类之一 |
| `decision` | `absorbed_inline` / `queued_next` / `new_branch` / `stopped` / `gate_reopened` / `clarified` |
| `owner` | 决策/执行 owner |
| `status` | `RECEIVED`/`CLASSIFIED`/`QUEUED`/`CONSUMED`/`STOPPED`/`REJECTED`/`CLOSED` |
| `insertionPoint` | 当前轮/下一轮/新支线/STOP-SWEEP |
| `rejoin` | 回归轮/支线门（当前 R16） |
| `qaRequired` | `yes/no` + 原因 |
| `stopSweepRef` | URGENT/GATE 时的 STOP-SWEEP/closeout ID |
| `evidence` | 路径/命令/摘要；不含敏感内容 |
| `consumedBy` | 下一轮 qitem/卡/PR |
| `notes` | 简短说明 |

---

## 5. 与 QA / STOP-SWEEP / 分支收敛 / R15-R16 的关系

### 5.1 QA

- `CLARIFY`：通常不需要 QA；影响验收时按 `GATE_CHANGE`。
- `INLINE_EXTEND`：验收变化 → QA 必须介入；否则当前轮 QA 回归覆盖。
- `NEXT_ROUND`/`SIDE_BRANCH`：按下一轮/支线 QA 门。
- `URGENT_STOP`/`GATE_CHANGE`：QA 必须独立复核；不能 builder 自检。

### 5.2 STOP-SWEEP

- `URGENT_STOP` 直接进入 `docs/CLOSEOUT-MANUAL.md` 的 0–5min 冻结 + QA 分类。
- `GATE_CHANGE` 若当前轮结果失效/需冻结，也走 STOP-SWEEP 的冻结/收尾；否则只做 gate 重开。
- STOP-SWEEP 的分类结果（CLOSE_OUT/ABANDON/ARCHIVE_RECYCLE）可反过来决定插入是否继续。

### 5.3 分支收敛

- `NEXT_ROUND` 归属当前分支；不新建分支。
- `SIDE_BRANCH` 按 BRANCHING-PROTOCOL 新建，锚定最后闭合轮；更新 ledger/index。
- `GATE_CHANGE` 可能使当前分支结果失效；需 QA/MAIN 决定重跑/废弃。
- `URGENT_STOP` 冻结分支；未 QA 前不 merge/delete。

### 5.4 R15/R16 锚点

- 主链当前：最后闭合 R15，R16 NEED_MAIN；插入不得跳过 R16。
- `NEXT_ROUND` 应在 R16 完成后按主链顺序消费；`SIDE_BRANCH` rejoin R16。
- `GATE_CHANGE` 若改主链验收，必须 MAIN 批准，仍回 R16 重新验收。
- 不把插入内容写进 R15 已完成记录；不篡改历史。

---

## 6. OpenRig 命令草案

> 只读/草案；i1 不执行。所有“插入”先记录，再按分类动作。

### 6.1 通知/澄清

```bash
# 只通知，不是持久记录；持久记录必须落 insertion ledger
rig send <owner-session> "INSERTION <INSERT-ID>: <one-line>; 详情见 reports/operations/insertions/<INSERT-ID>/"

# 读当前状态
rig queue list --json
rig workflow status --json
```

### 6.2 排队（NEXT_ROUND / SIDE_BRANCH）

```bash
# 下一轮：创建 qitem，不碰当前 packet
rig queue create \
  --destination <next-owner> \
  --summary "INSERTION <ID>: <summary>" \
  --body-file reports/operations/insertions/<INSERT-ID>/INSERTION.md \
  --tags insertion:<INSERT-ID>,next-round \
  --priority <routine|urgent> --json

# 独立支线：先记录 + 建 branch doc/ledger；qitem 给支线 owner
rig queue create \
  --destination <branch-owner> \
  --summary "INSERTION <ID>: new side branch" \
  --body-file reports/operations/insertions/<INSERT-ID>/INSERTION.md \
  --tags insertion:<INSERT-ID>,side-branch --json
```

### 6.3 当前轮关闭/交下一轮

```bash
# 当前轮正常完成，插入排下一轮
rig workflow project --instance <id> --current-packet <qitem> \
  --exit done --actor-session <session> --evidence-ref <path> --json

# 当前轮交给下一 owner/下一轮（不是把插入塞进当前 body）
rig workflow project --instance <id> --current-packet <qitem> \
  --exit handoff --next-owner <next-owner> --json
```

### 6.4 紧急/gate 变更

```bash
# URGENT_STOP：先冻结，走 STOP-SWEEP；不是普通排队
rig workflow abort <instanceId> --reason "URGENT_STOP: <reason>" --actor-session <session> --json
# 然后按 docs/CLOSEOUT-MANUAL.md 建 QA 收尾任务

# GATE_CHANGE：冻结/标旧结果 invalidated，由 MAIN/QA 重开
rig queue update <qitem> --state blocked --blocked-on "gate:<what>" \
  --summary "GATE_CHANGE: <what>" --evidence-ref <path> --json
```

### 6.5 不能做什么

- 不能直接改当前 qitem body/scope 来“吸收”插入；不能把插入写进当前轮 evidence 当原始验收。
- 不能用 `done` 关闭当前轮来“腾地方”；不能用 `rig send` 代替持久记录。
- 不能在 URGENT_STOP 时继续跑；不能未 QA 就 merge/delete/清锁。
- 不能把 `NEXT_ROUND` 插到 R15 历史或跳过 R16。
- 不能把 SIDE_BRANCH 混进当前 Web 分支/`bridge-app` 外仓。

---

## 7. 插入生命周期

```text
RECEIVED -> CLASSIFIED -> QUEUED -> CONSUMED -> CLOSED
                         └-> STOPPED (URGENT_STOP)
                         └-> REJECTED (不做，记录理由)
                         └-> GATE_REOPENED (GATE_CHANGE)
```

- `RECEIVED`：记录已建，尚未分类；当前轮不动。
- `CLASSIFIED`：owner 已定类/插入点。
- `QUEUED`：qitem/ledger 已排下一轮/支线。
- `CONSUMED`：下一轮/支线已引用并完成。
- `CLOSED`：验收/证据完成，insertion 关闭。
- `STOPPED`：URGENT_STOP/STOP-SWEEP；记录 closeout ID。
- `REJECTED`：不做；写理由/owner，不删记录。

---

## 8. 验收/检查清单（插入本身）

- [ ] 有唯一 `INSERT-ID` 和持久记录（不是只发消息）。
- [ ] 六类分类明确；默认不打断当前轮。
- [ ] 当前轮 body/scope 未被静默修改。
- [ ] `INLINE_EXTEND` 有 owner 确认 + 验收/回归更新。
- [ ] `NEXT_ROUND` 有 qitem/owner/下一轮卡。
- [ ] `SIDE_BRANCH` 有 branch doc/ledger/base/rejoin。
- [ ] `URGENT_STOP` 已冻结并走 STOP-SWEEP；不是普通排队。
- [ ] `GATE_CHANGE` 旧结果已 invalidated；MAIN/QA 批准。
- [ ] 证据不含原始截图/聊天/token；引用索引/ledger 已更新。
- [ ] R15/R16 锚点未被跳过。

## 9. 本轮不做什么

- 不改产品代码、不改当前轮 packet/body/scope、不建/切分支、不 merge/delete。
- 不执行 `rig send`/`queue create`/`workflow project`/`workflow abort`；只给草案。
- 不读/提交原始截图、聊天正文、token、logcat。
- 不把本分析当标准协议；i2 写 `docs/MIDRUN-INSERTION-PROTOCOL.md`。

## 10. 引用

- `discussions/insert-guard-20261114/BRIEF.md`
- `docs/BRANCHING-PROTOCOL.md`
- `docs/CLOSEOUT-MANUAL.md`
- `docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`、`docs/branches/REFERENCE-INDEX.md`
- `reports/branches/SYNC-GUARD.md`、`reports/branches/SYNC-MANIFEST.json`
- `reports/sctg/FORMAL-RUN-STATE.json`
- `reports/operations/MIDRUN-INSERTION.json`
