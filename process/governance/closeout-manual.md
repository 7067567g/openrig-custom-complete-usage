# the assistant project · 中途停止收尾手册（QA 版 · 标准版）

- **手册版本**：`v1.0.0`（standard，2026-11-14）
- **状态**：`standard / reusable` —— 长期复用的标准手册，**不是**某一次 STOP-SWEEP 的临时报告。
- **适用范围**：任意 rig / workflow / qitem / branch / 多轮支线 / 文档分析轮在“中途停止”后的冻结、盘点、QA 分类与收尾。
- **维护者**：QA lead + MAIN（见 §13 变更记录）；每次流程变化或每季度复核一次。
- **参数化**：本手册中的 `<...>` 是占位符；复制/执行前按下表替换，不要把当前实例值写死。当前实例的现场数据只放 `reports/operations/STOP-SWEEP.md` / closeout ledger，不写进本手册正文。
- **配套（标准件）**：
  - 边界与分类分析（当前实例的 reference implementation）：`reports/operations/STOP-SWEEP.md`
  - 机器规则：`reports/operations/STOP-SWEEP.json`
  - QA 任务标准模板：`reports/operations/QA-CLOSEOUT-TASK.md`
  - 收尾台账模板：`reports/operations/CLOSEOUT-LEDGER-TEMPLATE.json`
- **铁律**：**停止不是 done；先冻结，后盘点，再让独立 QA 分类，最后才允许动作。**

---

## 0. 谁在用、什么时候用

### 0.1 角色

| 角色 | 职责 |
|---|---|
| **Stop initiator** | 人/Lead/MAIN 发起停止；写停止原因、时间、范围 |
| **Builder/owner** | 停止前保存现场；停止后只读配合，不给自己做 QA |
| **Independent QA** | 盘点、分类、验证、给 PASS/NEED_MAIN/BLOCKED；不实现 |
| **MAIN/operator** | `<REJOIN-ROUND>`、Android、隐私门、删除/归档/回收的最终批准 |

### 0.2 触发

- 用户主动停/中止、预算/时间/内存/并发上限、gate FAIL/BLOCKED/NEED_MAIN、seat 卡死/watchdog/qitem 超时、进程崩溃/断电/重启、多轮支线中途停止、显式停 rig/daemon。
- 如果只是“暂时不继续”，用 `waiting/blocked` + continuation，不要走收尾删除。

### 0.3 本手册的使用顺序

```text
0–5min 冻结 → 写 stop record → 盘点 → 新建/保留/重启 QA → QA 分类 →
CLOSE_OUT / ABANDON / ARCHIVE_RECYCLE SOP → 验证 → 回 <REJOIN-ROUND>
```

### 0.4 标准版如何复用到任意停止事件

1. **不要复制本手册**（它是标准件）；复制 `QA-CLOSEOUT-TASK.md` 和 `CLOSEOUT-LEDGER-TEMPLATE.json` 到 `reports/operations/closeout/<STOP-ID>/`。
2. 按下表把 `<...>` 替换为该次停止事件的值；无法确定的值写 `UNKNOWN` + 负责人，不要猜。
3. `STOP-SWEEP.md` 只作为**当前实例的示例/边界分析**；不要把它的 branch/HEAD/dirty/日期复制到别的停止事件。
4. 如果流程变化，修改本手册并更新 §13 变更记录 + 版本号；不要在一次事件里临时改标准。
5. 收尾完成后把实例数据写进 ledger，不把实例数据回写本手册。

**占位符表**

| 占位符 | 含义 | 示例 |
|---|---|---|
| `<STOP-ID>` | 停止事件 ID | `STOP-20261114-01` |
| `<STOP-AT>` | 停止时间（ISO 8601） | `2026-11-14T00:20:00+08:00` |
| `<STOP-ACTOR>` | 发起人/角色 | `MAIN` / `Lead` / `user` |
| `<STOP-REASON>` | 停止原因 | `user stop` / `budget` / `gate FAIL` / `NEED_MAIN` / `seat stuck` / `crash` |
| `<SCOPE>` | 停止范围 | `workflow:...` / `rig:...` / `branch:...` / `U2a` |
| `<BRANCH>` | 当前/目标分支 | `feat/...` |
| `<HEAD>` | 当前 commit | `280de35`（示例，按实际填） |
| `<DIRTY-COUNT>` | 工作树 dirty 文件数 | `0` / `77` |
| `<RIG>` | rig 名/ID | `monitor-lite` |
| `<WORKFLOW-INSTANCE>` | workflow instance | `01M7...` |
| `<PACKET-ID>` | 当前 qitem | `qitem-...` |
| `<QA-SEAT>` | 独立 QA seat | `assurance.qa@...` |
| `<ANCHOR-ROUND>` | 主链锚点轮 | 当前默认 `R15` |
| `<REJOIN-ROUND>` | 回归轮 | 当前默认 `R16` |
| `<AFFECTED-BRANCHES>` | 受影响支线 | `UX6-R15` / `QUIET-200` / `无` |
| `<EVIDENCE-DIR>` | 证据目录 | `reports/operations/closeout/<STOP-ID>/evidence/` |
| `<ARCHIVE-DIR>` | 归档目录 | `reports/operations/archive/<STOP-ID>/` |
| `<VERDICT>` | QA 结论 | `PASS` / `NEED_MAIN` / `BLOCKED` |

> 本手册的“当前默认 R15/R16”只是本仓当前主链状态；换项目/换主链时按 `<ANCHOR-ROUND>/<REJOIN-ROUND>` 替换。

---

## 1. 停止后 0–5 分钟冻结清单

> 这一节由 stop initiator + builder 执行；QA 可复核。**只读/保存，不删除。**

| 时间 | 步骤 | 命令/检查 | 记录字段 |
|---|---|---|---|
| 0–1m | 停止发起新轮次/新请求 | 口头/消息确认；不要重启服务 | `stop_reason`, `stop_actor`, `stop_at`, `scope` |
| 0–1m | 记录当前代码现场 | `git branch --show-current`, `git rev-parse --short HEAD`, `git status --porcelain` | `branch`, `head`, `dirty_count` |
| 1–2m | 记录 rig/seat | `rig status`, `rig ps --nodes -A --json` | `rigs`, `nodes`, `running_seats`, `attention` |
| 1–2m | 记录 workflow | `rig workflow status --json`, `rig workflow list --json` | `active`, `aborted`, `failed`, `waiting`, `frontier` |
| 2–3m | 记录 queue | `rig queue list --all --json`, `rig queue undelivered --json`, `rig queue overdue --json` | `active_qitems`, `pending`, `blocked`, `undelivered`, `overdue` |
| 2–3m | 记录 watchdog/parked | `rig parked --json`, `rig watchdog list --json` | `parked_seats`, `watchdogs`, `stale_jobs` |
| 3–4m | 记录 git 残留 | `git worktree list`, `git stash list`, `git tag --list` | `worktrees`, `stash`, `tags` |
| 3–4m | 记录端口/锁 | `ss -ltnp`；`stat` 锁文件（不读内容） | `ports`, `locks`, `mtime` |
| 4–5m | 写 stop record + 建/保留 QA | 使用 `CLOSEOUT-LEDGER-TEMPLATE.json` | `ledger_path`, `qa_owner`, `qa_packet`, `deadline` |

**冻结期禁止**：`rig down --force`、`rig workflow abort` 前删除、`rm`、`git branch -D`、`git worktree remove`、`git clean`、`rig archive`、`rig watchdog stop`、`systemctl stop`、`kill`、清空 queue/lock。

**示例 stop record**：

```json
{
  "stop_at": "<STOP-AT>",
  "stop_actor": "<STOP-ACTOR>",
  "stop_reason": "<STOP-REASON>",
  "scope": "<SCOPE>",
  "branch": "<BRANCH>",
  "head": "<HEAD>",
  "dirty_count": "<DIRTY-COUNT>",
  "workflow": "<WORKFLOW-INSTANCE>",
  "qa_owner": "<QA-SEAT>",
  "qa_packet": "<PACKET-ID>"
}
```

---

## 2. 停止声明与状态映射

### 2.1 先声明真实状态

| 真实情况 | 用什么状态 | 不要用 |
|---|---|---|
| 用户中止 | workflow `aborted`；qitem `canceled`/`failed` | `done` |
| 执行失败 | workflow `failed`；qitem `failed` | `done` |
| 等人/外部 | qitem `blocked`；workflow `waiting` | `done` |
| 人工检查点未过 | `<REJOIN-ROUND>` `NEED_MAIN`/blocked | `PASS` |
| 交付下一阶段 | qitem `handed-off` | `done`（除非下一阶段验收） |
| 被替代 | qitem `canceled` + `closure-reason superseded` + target | `done` |
| rig 停止 | `stopped`/`detached`/`recoverable` | workflow done |
| rig 归档 | `archivedAt`（soft） | 删除 |

### 2.2 命令草案

```bash
# 整个 workflow 中止（保留 packet/证据）
rig workflow abort <instanceId> \
  --reason "user stop / budget / gate / seat stuck" \
  --actor-session <session> --json

# 单个 packet
rig queue update <qitemId> --state failed --resolution "<what remains>" --json
rig queue update <qitemId> --state blocked \
  --blocked-on "human:<seat>" --summary "<summary>" --evidence-ref <path> --json
rig queue update <qitemId> --state canceled \
  --closure-reason superseded --closure-target <successor> --json

# 暂停等条件（不是 done）
rig workflow project --instance <id> --current-packet <qitem> \
  --exit waiting --blocked-on <ref> --actor-session <session> --json

# 停整个 rig：先确认无人工作，再快照
rig ps --nodes --rig <rig> --json
rig down <rig> --snapshot --json
```

**禁止**：`rig workflow project --exit done` 用于停止；`rig queue update --state done` 用于中止；`rig down --delete/--force` 未授权。

---

## 3. 盘点清单（QA 必须逐项过）

### 3.1 Workflow / qitem / queue

| 检查 | 命令 | 记录 |
|---|---|---|
| 活跃/失败/中止/等待 | `rig workflow status --json`；`rig workflow list --json` | 每个 instance 的 status/frontier/step |
| 当前 qitem | `rig queue list --json` | qitemId/state/owner |
| 全部历史 | `rig queue list --all --json` | done/handed-off/canceled/recovery |
| 未送达/超时 | `rig queue undelivered --json`；`rig queue overdue --json` | 空/非空、原因 |
| 恢复 row | `rig queue show qitem-recovery-* --json` | 是否 canceled/superseded |
| parked | `rig parked --json` | 是否有 held/needsInput |

### 3.2 Seat / rig / watchdog

| 检查 | 命令 | 记录 |
|---|---|---|
| rig 列表 | `rig status` | 6 rigs / lifecycle |
| 节点 | `rig ps --nodes -A --json` | running/detached/recoverable/attention |
| 资源 | `rig ps --resources --json` | runningSeats / capture / load |
| 分配工作 | `rig ps --nodes -A --fields canonicalSessionName,hasAssignedWork,assignedWorkCount --json` | 谁还有活 |
| watchdog | `rig watchdog list --json` | active/stale/old-rig jobs |
| daemon/kernel | `rig daemon status`；`rig status` | daemon healthy / kernel auth_blocked |

### 3.3 Git / branch / docs

| 检查 | 命令 | 记录 |
|---|---|---|
| branch/HEAD | `git branch --show-current`；`git rev-parse --short HEAD` | 当前 branch/commit |
| branch heads | `git rev-parse --short <branches>` | 是否同 commit/无独有 commit |
| dirty | `git status --porcelain` | 文件数/类别 |
| worktree | `git worktree list` | 额外 worktree |
| stash | `git stash list` | 是否有未收 stash |
| tag | `git tag --list` | 是否已打 done/abandoned |
| docs/ledger | `docs/branches/*`、`reports/branches/BRANCH-LEDGER.json`、`reports/issues/*` | 是否一致 |

### 3.4 Temp / locks / services

| 检查 | 命令 | 记录 |
|---|---|---|
| 临时区 | 宿主 `tmp` 目录只读列举类别/数量 | 原始截图/聊天/令牌 **不读、不复制** |
| 锁 | `stat` 锁文件（不读内容） | path/size/mtime/owner（宿主 QA 确认） |
| 端口 | `ss -ltnp` | 7433/3080/3090 等 |
| 健康 | `curl -sS -o /dev/null -w '%{http_code}'` | 200/401/失败 |
| systemd | 宿主 `systemctl --user is-active ...` | 沙箱不可用，不能推断 |

### 3.5 只读目录

| 目录 | 规则 |
|---|---|
| `governance-20261110/staging/bridge repo` | 旧 staging；不可当源；不手改 |
| `governance-20261110/snapshots/**` | 只读；hash/existence |
| `dist/v3 workspace-share-20261025` | 生成物；从 tagged live 重新生成 |
| `bridge-app` | external；独立 Android 工作区 |

---

## 4. QA 收尾任务：新建 / 保留 / 重启

### 4.1 决策

| 情况 | 动作 | Owner |
|---|---|---|
| 没有 QA packet / 未被独立检查 | **新建** `qa-closeout` qitem（模板见 `reports/operations/QA-CLOSEOUT-TASK.md`） | 独立 QA；无 QA 时 Lead/MAIN 指派 |
| 原 workflow 已有 QA 且代码/证据未变 | **保留**，追加残留清单 | 原 QA |
| QA 已开始但代码/base/证据变了，或 QA seat 停止 | **重启** QA；旧结果作废/标注 | 原/新 QA（非实现者） |

### 4.2 任务创建命令

```bash
rig queue create \
  --destination <qa-seat> \
  --summary "QA closeout: <stop reason> @ <branch/HEAD>" \
  --body-file reports/operations/QA-CLOSEOUT-TASK.md \
  --tags qa-closeout,stop-sweep \
  --gate qa \
  --priority urgent --json
```

或 handoff 现有 packet：

```bash
rig queue handoff <qitemId> --to <qa-seat> \
  --summary "QA closeout after stop" \
  --tags qa-closeout --json
```

### 4.3 重启 QA 步骤

1. 记录旧 QA 的 packet/run/证据；标 `invalidated`（不要删）。
2. 新建 QA 输入快照（stop record + 当前 branch/HEAD + 残留清单）。
3. 新 QA 从 §3 重新盘点；旧结果只作参考，不作 PASS 依据。
4. 新 QA 重新分类/验证；结论写入 `CLOSEOUT-LEDGER-TEMPLATE.json` 的 `qa` 段。

### 4.4 QA 独立性

- 实现者不能给自己做 QA。
- 本 rig 的 builder 不能同时充当独立 QA；需 Lead/MAIN 指派。
- `<REJOIN-ROUND>`/Android/隐私门由 MAIN 或人工 QA。

---

## 5. 残留分类表与判定树

### 5.1 分类表（QA 填写）

| 残留 ID | 类别 | 证据 | 分类 | Owner | 动作 | 回滚 | 状态 |
|---|---|---|---|---|---|---|---|
| R-001 | workflow | `rig workflow show ...` | CLOSE_OUT/ABANDON/ARCHIVE_RECYCLE |  |  |  |  |
| R-002 | qitem | `rig queue show ...` |  |  |  |  |  |
| R-003 | branch/worktree | `git ...` |  |  |  |  |  |
| R-004 | docs/report | path/hash |  |  |  |  |  |
| R-005 | temp/lock/service | stat/ss |  |  |  |  |  |

### 5.2 判定树

```text
残留是否仍被活跃引用/需要继续？
├─ 是 → 保留（不回收）；若只是停止 → ABANDON 或继续
└─ 否 → 原任务验收是否已满足？
   ├─ 是 → CLOSE_OUT
   └─ 否 → 是否有明确废弃决定/参考价值？
      ├─ 是 → ABANDON
      └─ 否 → ARCHIVE_RECYCLE
```

### 5.3 三类速查

| 分类 | 一句话 | 允许 | 禁止 |
|---|---|---|---|
| **CLOSE_OUT** | 已完成，只差关单/证据 | 关单、补证据、merge/tag | 无证据关单 |
| **ABANDON** | 有意废弃，保留最小引用 | aborted/canceled、tag/记录、保留证据 | 标 done、删证据 |
| **ARCHIVE_RECYCLE** | 无价值/干扰，归档后回收 | 归档+manifest、QA 签字后移除 | 未归档删除、删 active 引用 |

---

## 6. SOP：CLOSE_OUT

### 6.1 前置条件

- acceptance/验收已满足；测试/证据可复核。
- write scope 内改动已提交/可提交；无越界。
- 无未解决 `NEED_MAIN`/`BLOCKED`/`FAIL`。
- QA 独立复核 PASS。

### 6.2 步骤

1. 把证据放入 `reports/operations/closeout/<stop-id>/`（命令输出/哈希/diff/测试日志；不含敏感内容）。
2. QA 填分类表，所有残留为 CLOSE_OUT 或有明确后续。
3. 关 qitem：`rig queue update <qitem> --state done --closure-reason no-follow-on --resolution "<QA PASS + evidence>" --json`。
4. 关 workflow：`rig workflow project --instance <id> --current-packet <qitem> --exit done --actor-session <qa> --evidence-ref <qa-report> --json`。
5. 更新 branch doc/ledger/index；按 BRANCHING-PROTOCOL merge/tag。
6. 只清临时/可再生文件；保留证据。

### 6.3 回滚

- 合并前：丢弃分支/恢复 snapshot。
- 合并后：`git revert -m 1 <merge-commit>`；缓存 schema 版本化，旧缓存忽略/清理。

---

## 7. SOP：ABANDON

### 7.1 前置条件

- 用户/MAIN 明确停止或改方向；原目标不再需要。
- 工作未达验收，或决定不合并。
- 仍有参考价值；QA 确认无未披露 P0/P1。

### 7.2 步骤

1. 记录决定/理由/时间/owner；写 `ABANDON` 到 ledger。
2. qitem `canceled`/`failed`（按语义）；workflow `aborted`（不是 done）。
3. 分支保留为 `abandoned` 或打 `abandoned-<date>` tag；不 merge。
4. 文档记录可复用点/风险；不删证据。
5. 保留期由 MAIN 定；到期后按 ARCHIVE_RECYCLE。

### 7.3 回滚

- 恢复分支/base 或 snapshot；误标 ABANDON 重开需新证据，不复用旧 PASS。

---

## 8. SOP：ARCHIVE_RECYCLE

### 8.1 前置条件

- 无利用价值或会造成干扰；无活跃引用（branch/doc/ledger/qitem/service）。
- 删除不影响 `<REJOIN-ROUND>`/`<AFFECTED-BRANCHES>`/证据链。
- QA 签字 + 回滚路径。

### 8.2 步骤

1. 生成归档清单：path/size/hash/mtime；引用检查（`rg`/ledger/index）。
2. 归档：`tar`/`zip` + manifest/hash；存到 `reports/operations/archive/<stop-id>/` 或指定归档区。
3. 更新 ledger：`ARCHIVE_RECYCLE` + archive path/hash + 引用替换。
4. 移出工作区；只删归档后的对象，不删 active 引用。
5. rig 用 `rig archive <rigId>`（soft）；git worktree/branch 删除只在 tag/归档/QA 后。
6. 原始截图/聊天/token/logcat 不进入归档证据；按隐私规则销毁/不保留。

### 8.3 回滚

- 从归档包/manifest 恢复；跑验收/哈希；索引丢失按备份/快照恢复。

---

## 9. 证据、隐私、回滚边界

### 9.1 允许

- 命令/退出码/文本输出（不含聊天正文）。
- path/size/hash、git commit/tag、端口、锁 stat、JSON 字段。
- 问题编号/代码位置/测试结果。

### 9.2 禁止

- 原始截图、聊天正文、媒体正文、文件内容、token、`Authorization`、带 token URL、`data:`/blob、logcat/UI dump 正文。
- 共享设备可读隐私内容；只记录“已按规则销毁/不保留”。

### 9.3 回滚证据

- branch/commit/tag、snapshot path/hash、staging 只读副本、归档包 + manifest。
- 回滚命令/验证输出；不把“已停止”当回滚完成。

---

## 10. 收尾完成标准与主链回归

- [ ] stop record（原因/时间/发起人）+ 0–5min 冻结清单完成。
- [ ] workflow/qitem/queue/seat/git/docs/temp/locks/services 已盘点。
- [ ] QA 新建/保留/重启，owner 独立。
- [ ] 每项残留分类为 CLOSE_OUT/ABANDON/ARCHIVE_RECYCLE，有证据/owner/动作/回滚。
- [ ] 没有 stopped/aborted/blocked/NEED_MAIN 被写成 done/PASS。
- [ ] `<AFFECTED-BRANCHES>` 未未授权 merge/delete；`<REJOIN-ROUND>` 未跳过。
- [ ] 敏感数据未入库；只读目录未改。
- [ ] 收尾记录/证据/回滚路径落盘；主链回到 **`<REJOIN-ROUND>`**（NEED_MAIN 继续）。
- [ ] `<REJOIN-ROUND>` 的 NEED_MAIN 项完成前不进入下一产品轮。

---

## 11. 附录：QA 记录字段

```json
{
  "stop_id": "STOP-20261114-01",
  "stop_at": "<STOP-AT>",
  "stop_actor": "<STOP-ACTOR>",
  "stop_reason": "<STOP-REASON>",
  "scope": "<SCOPE>",
  "branch": "<BRANCH>",
  "head": "<HEAD>",
  "dirty_count": "<DIRTY-COUNT>",
  "workflow_instances": [],
  "qitems": [],
  "residue": [
    {
      "id": "R-001",
      "category": "branch",
      "evidence": "git rev-parse <BRANCH>",
      "classification": "ABANDON",
      "owner": "QA",
      "action": "tag abandoned; keep branch",
      "rollback": "restore branch/base",
      "status": "pending"
    }
  ],
  "qa": {"owner": "assurance.qa@...", "verdict": "NEED_MAIN", "evidence": []},
  "mainline": {"anchor": "<ANCHOR-ROUND>", "rejoin": "<REJOIN-ROUND>", "state": "<NEED_MAIN|PASS>"},
  "privacy": {"raw_screenshots": "not read/not committed", "chat_body": "not read/not committed"}
}
```

## 12. 引用

### 12.1 标准依赖（长期）

- `reports/operations/QA-CLOSEOUT-TASK.md`（标准模板）
- `reports/operations/CLOSEOUT-LEDGER-TEMPLATE.json`（台账模板）
- `docs/BRANCHING-PROTOCOL.md`（支线锚点/回归/合并规则）
- `reports/branches/SYNC-GUARD.md`、`reports/branches/SYNC-MANIFEST.json`（目录/引用一致性）
- `reports/sctg/FORMAL-RUN-STATE.json`（主链轮次状态）

### 12.2 当前实例参考（可选，不构成本手册标准依赖）

- `reports/operations/STOP-SWEEP.md` / `.json`（本次停止事件的参考实现/分析）
- `<BRANCH-DOCS>`（当前实例示例：`docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`）
- `reports/branches/BRANCH-LEDGER.json`（当前实例分支台账；换项目时按实际替换）


## 13. 变更记录

| 版本 | 日期 | 作者/角色 | 变更 |
|---|---|---|---|
| v1.0.0 | 2026-11-14 | builder / MAIN review | 建立标准版：0–5min 冻结、QA 新建/保留/重启、三类分类/判定树、三类 SOP、证据/隐私/回滚、主链回归；参数化占位符与复用步骤。 |
| v1.0.1 | `<YYYY-MM-DD>` | `<maintainer>` | `<change>` |

> 版本规则：流程/命令/分类标准变化 → minor/patch 升版并写变更记录；仅实例数据变化不改本手册。
