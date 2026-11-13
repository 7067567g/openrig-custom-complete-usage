# STOP-SWEEP · 中途停止的清扫边界与分类规则

- 日期：2026-11-14
- 类型：治理/收尾流程设计；**不改产品代码、不停止任何进程、不删除任何文件**。
- 关联：QUIET-200 / UX6-R15 / 正式 30 轮 R16（NEED_MAIN）
- 已知问题：deck issue `01`（QUIET-200 基线未冻结）
- 机器可读：`reports/operations/STOP-SWEEP.json`
- 标准件：`docs/CLOSEOUT-MANUAL.md`（v1.0.0 标准版，长期复用）、`reports/operations/QA-CLOSEOUT-TASK.md`（标准模板）；本文件是本次停止事件的分析/示例，不是手册本身。
- 后续：c2 已基于本文件产出标准手册与模板。

## 0. 一句话原则

**先冻结，后盘点，再让独立 QA 分类，最后才允许收尾/废弃/归档回收；停止不是 done。**

三个硬边界：

1. 停止/中止后 **0–5 分钟只冻结**：不删分支、不删文件、不清 qitem、不杀服务、不动 snapshot/staging/dist。
2. 所有残留必须由 **独立 QA** 分类为 `CLOSE_OUT` / `ABANDON` / `ARCHIVE_RECYCLE`，每项有证据、owner、动作、回滚。
3. 收尾完成后回到主链 **R16**（NEED_MAIN 继续），不跳过；QUIET-200/UX6-R15 未 QA/未合并前保持 active，不自动 merge/delete。

---

## 1. 停止场景

| ID | 场景 | 典型触发 | 立即状态 | 首要动作 | 禁止 |
|---|---|---|---|---|---|
| S1 | 用户主动停/中止 | 人说停、改方向、取消 | workflow `aborted` / qitem `canceled` 或 `failed` | 冻结 + 记录理由 | 把当前 packet 标 done |
| S2 | 预算/时间/内存/并发上限 | token/时间/内存/并发超限 | seat `stopped` / workflow `failed`/`aborted` | 保存现场 + 资源快照 | 继续开新轮 |
| S3 | gate FAIL / BLOCKED / NEED_MAIN | SCTG gate、人工检查点 | `blocked`/`NEED_MAIN` | 保留证据、交 QA/MAIN | 把 NEED_MAIN 写成 PASS |
| S4 | seat 卡死/watchdog/qitem 超时 | 长时间无进展、stuck sweep | qitem `blocked`/`failed`，recovery qitem | 读状态、保留 row、必要时 park | 盲删 row/杀 seat |
| S5 | 进程崩溃/断电/重启 | 服务/daemon/主机异常 | workflow `failed`/`aborted`，session detached | 恢复前先冻结，检查锁/端口 | 直接重跑覆盖现场 |
| S6 | 多轮支线中途停止 | UX6/QUIET 实现到一半 | branch active + dirty | 冻结分支/工作树，交 QA | 删除分支/清 dirty |
| S7 | 显式停止 rig/daemon | 总任务结束、维护 | rig `stopped`/`detached` | snapshot 后 down；保留可恢复 | `--delete`/`--force` 除非明确 |
| S8 | 文档/分析轮中途停止（本类） | c1/c2 未写完 | workflow active/aborted | 保留已写文件 + 半成品标记 | 把半成品当完整手册 |

**停止状态映射**：`aborted` ≠ `done`；`failed` ≠ `done`；`blocked`/`NEED_MAIN` ≠ `done`；`canceled`/`superseded`/`handed-off` 是不同语义；`stopped`/`detached`/`recoverable` 是 rig/seat 生命周期，不是工作验收。

---

## 2. 清扫边界与顺序

### 2.1 0–5 分钟冻结清单

| 时间 | 动作 | 记录 |
|---|---|---|
| 0–1 min | 停止发起新请求/新轮次；不要重启服务 | 谁停的、为什么、时间、当前 branch/HEAD |
| 1–2 min | 读 `rig status`、`rig ps --nodes -A`、`rig workflow status`、`rig queue list --all` | 状态快照（JSON/文本） |
| 2–3 min | 读 `rig parked`、`rig watchdog list`、`git status/worktree/stash/tag` | 残留清单 |
| 3–4 min | 读端口/锁/服务（只读）；不做 kill/delete | `ss`、lock stat、端口健康 |
| 4–5 min | 写 stop record；创建/保留/重启 QA 收尾任务 | QA owner、输入、截止时间 |

**冻结期间禁止**：`rig down --force`、`rig workflow abort` 前的删除、`rm`、`git branch -D`、`git worktree remove`、`git clean`、`rig archive`、`rig watchdog stop`、`systemctl stop`、`kill`、清空 queue/lock。

### 2.2 清扫顺序

```text
停止 → 冻结 → 盘点 → QA 分类 → 动作（收尾/废弃/归档回收）→ 验证 → 回 R16
```

- **盘点**只读：workflow/qitem/queue/seat/git/branch/docs/temp/locks/services。
- **QA 分类**在删除前完成；分类表是后续动作的唯一输入。
- **动作**必须逐项有 owner、证据、回滚；批量删除不允许。
- **验证**后写 closeout record，恢复主链锚点/回归点。

### 2.3 禁止动作（硬边界）

1. 把“已停止/已中止”记成 `done` 或 `PASS`。
2. 在 QA 分类前删除分支、worktree、qitem、证据、snapshot、staging、dist。
3. 未确认 owner 就清锁/杀进程/停 systemd/杀 tmux。
4. 把原始截图、聊天正文、token、logcat 正文、UI dump 写入仓库/报告/证据。
5. 直接改 staging/snapshot/dist/备份目录。
6. 在 QUIET-200/UX6-R15 未 QA/未合并前 `git merge`、`git push`、`git tag` 或删分支。
7. 把 `NEED_MAIN`/`BLOCKED`/`FAIL` 用“已经停了”掩盖。
8. 用 `--force`/`--delete` 绕过 QA 签字。

---

## 3. QA 收尾任务：新建 / 保留 / 重启

### 3.1 触发条件

| 决策 | 触发条件 | Owner | 输出 |
|---|---|---|---|
| **新建 QA 收尾任务** | 停止时没有 QA packet；或工作树/分支/证据未被独立检查；或残留跨多个目录 | 独立 QA seat（非实现者）；没有 QA seat 时由 orchestrator/Lead 指派，R16/Android 由 MAIN | QA-CLOSEOUT 任务 + 分类表 |
| **保留现有 QA 步骤** | 原 workflow 已有 QA 步骤且代码/证据在停止后未变；QA 尚未开始或可继续 | 原 QA owner | 在原 QA 上追加残留清单，不重复建 |
| **重启 QA 步骤** | 原 QA 已开始但代码/工作树/base 变了；QA seat 停止/超时；证据过期；分支 re-base | 原 QA 或新 QA（不得是原实现者） | 新 QA 输入快照 + 旧 QA 结果作废/标注 |

### 3.2 QA 任务必须包含

- 停止原因/时间/发起人；当前 branch/HEAD/dirty 状态。
- 残留清单（workflow/qitem/queue/seat/git/docs/temp/locks/services）。
- 每项分类：`CLOSE_OUT` / `ABANDON` / `ARCHIVE_RECYCLE`。
- 每项证据：命令/输出/路径/哈希（不含原始截图/聊天/token）。
- 每项动作：owner、执行者、回滚路径、验收。
- 主链回归：R16 继续；QUIET/UX6 状态；是否需要 MAIN。
- QA 结论：PASS / NEED_MAIN / BLOCKED；不得用“已停止”代替。

### 3.3 Owner 规则

- **实现者不能给自己做 QA**；本 rig 的 builder 不能同时充当独立 QA。
- QA seat 优先：`assurance.qa`/独立 QA；没有时 orchestrator/Lead 指派；R16/Android/隐私门由 MAIN 或人工 QA。
- QA 的 qitem 应标 `gate:qa`/`qa-closeout` 标签（命令草案见 §5），并在 body 中写清 stop reason。
- 如果 QA 自身停止/超时，按 S4 处理：保留 QA row，重新 park/指派，不降级成 builder 自检。

---

## 4. 三类残留判定

### 4.1 CLOSE_OUT（实际已完成，只差收尾）

**判定标准**

- 原任务的 acceptance/验收已满足；测试/证据可复核。
- write scope 内改动已提交/可提交；没有未申报越界。
- 没有未解决的 `NEED_MAIN`/`BLOCKED`/`FAIL`；或对应项已被明确接受。
- 残留只是关单/补证据/文档/merge/tag。

**证据要求**

- 验收命令/结果、测试日志、diff/commit、write scope 对照、证据路径/哈希。
- QA 独立复核结论（PASS）；不是实现者自述。

**动作**

- qitem `done`（closure reason 按语义：`no-follow-on`/`handed_off_to` 等）；workflow `done`/`completed`。
- 更新 branch doc/ledger/索引；必要时 merge/tag（按 BRANCHING-PROTOCOL）。
- 清理只清临时/可再生文件；保留证据。

**回滚**

- 合并前：丢弃分支/恢复快照；合并后：`git revert -m 1 <merge-commit>`。
- 数据 schema（IndexedDB/cache）带版本，回滚忽略/清理旧缓存。

### 4.2 ABANDON（有意废弃）

**判定标准**

- 用户/MAIN 明确停止或改方向；原目标不再需要。
- 工作未达到验收，或达到但决定不合并。
- 仍有参考价值（分析/半成品/失败证据），不能直接删。

**证据要求**

- 停止决定/理由/时间/owner；当前 branch/HEAD/scope；已产出的文件/证据清单。
- 明确“不合并/不继续”的决策记录；QA 确认没有未披露的 P0/P1。

**动作**

- workflow `aborted`（不是 done）；qitem `canceled`/`failed`（按语义），保留 row。
- 分支保留为 `abandoned` 或打 `abandoned-<date>` tag；文档记录原因与可复用点。
- 不 merge；不删证据；不删 branch 直到保留期结束（由 MAIN 定）。

**回滚**

- 恢复分支/base 或从 snapshot 恢复；若已删，按归档索引恢复。
- 若误标 ABANDON，重开 qitem/branch 需记录新证据，不复用旧 PASS。

### 4.3 ARCHIVE_RECYCLE（归档后回收）

**判定标准**

- 已无利用价值或会造成干扰：重复对象、过期临时文件、已被 supersede 的 recovery qitem、旧 staging/snapshot 的临时副本、旧 worktree、缓存/日志。
- 没有活跃引用（branch/doc/ledger/qitem/服务）；或引用已改为归档指针。
- 删除不会影响 R16/QUIET/UX6/证据链。

**证据要求**

- 归档清单（路径/大小/哈希/时间）；引用检查（`rg`/ledger/index）；QA 签字；回滚路径。
- 原始截图/聊天/token/logcat **不得**进入归档证据；只能记录“已按隐私规则销毁/不保留”。

**动作**

- 先归档（tar/zip/目录 + manifest/hash），再移出工作区；保留归档索引。
- `rig archive` 只用于 rig（soft/reversible）；不是删除。
- `git worktree remove`/`git branch -d` 只在 tag/归档/QA 后；不用 `-D` 除非明确。
- 临时文件按保留期清理；不清理未确认的锁/服务。

**回滚**

- 从归档包/manifest 恢复；恢复后跑验收/哈希。
- 若归档索引丢失，按备份/快照恢复；记录事故。

### 4.4 判定树

```text
残留是否仍被活跃引用/需要继续？
├─ 是 → 保留（不分类为回收）；若只是停止 → ABANDON 或继续
└─ 否 → 原任务验收是否已满足？
   ├─ 是 → CLOSE_OUT（关单/补证据/合并）
   └─ 否 → 是否有明确废弃决定/参考价值？
      ├─ 是 → ABANDON（保留最小引用）
      └─ 否 → ARCHIVE_RECYCLE（归档后回收）
```

---

## 5. OpenRig 命令草案与状态映射

> 以下为 QA/MAIN 执行草案；**c1 本轮不执行**。所有命令先只读确认，再按分类动作。

### 5.1 冻结/盘点（只读）

```bash
rig status
rig ps --nodes -A --json
rig workflow status --json
rig workflow list --json
rig queue list --all --json
rig queue undelivered --json
rig queue overdue --json
rig parked --json
rig watchdog list --json

git -C <BRIDGE_REPO> status --short
git -C <BRIDGE_REPO> branch --show-current
git -C <BRIDGE_REPO> rev-parse --short HEAD
git -C <BRIDGE_REPO> worktree list
git -C <BRIDGE_REPO> stash list
git -C <BRIDGE_REPO> tag --list

ss -ltnp
```

### 5.2 停止/中止（不是 done）

```bash
# 整个 workflow 中止（保留 packet/证据）
rig workflow abort <instanceId> \
  --reason "user stop / budget / gate / seat stuck" \
  --actor-session <session> --json

# 单个 packet 失败/阻塞/取消
rig queue update <qitemId> --state failed \
  --resolution "stop reason / what remains" --json
rig queue update <qitemId> --state blocked \
  --blocked-on "human:<seat>" --summary "..." --evidence-ref <path> --json
rig queue update <qitemId> --state canceled \
  --closure-reason superseded --closure-target <successor> --json

# 暂停并等条件（不是 done）
rig workflow project --instance <id> --current-packet <qitem> \
  --exit waiting --blocked-on <ref> --actor-session <session> --json

# 停止整个 rig：先确认无人工作，再快照
rig ps --nodes --rig <rig> --json
rig down <rig> --snapshot --json
```

**禁止**：`rig workflow project --exit done` 用于停止；`rig queue update --state done` 用于中止；`rig down --delete`/`--force` 绕过 QA。

### 5.3 QA 收尾任务

```bash
rig queue create \
  --destination <qa-seat> \
  --summary "QA closeout: <stop reason> @ <branch/HEAD>" \
  --body-file <qa-closeout-body.md> \
  --tags qa-closeout,stop-sweep \
  --gate qa \
  --priority urgent --json

# 或把现有 packet 交给 QA
rig queue handoff <qitemId> --to <qa-seat> \
  --summary "QA closeout after stop" --tags qa-closeout --json

# workflow 内保留/重启 QA 步骤
rig workflow project --instance <id> --current-packet <qitem> \
  --exit handoff --next-owner <qa-seat> \
  --result-note "stop; QA closeout required" --json
```

### 5.4 收尾/归档/回收

```bash
# 只有 QA PASS 后才允许
rig workflow project --instance <id> --current-packet <qitem> \
  --exit done --actor-session <qa-session> --evidence-ref <qa-report> --json
rig queue update <qitem> --state done --closure-reason no-follow-on \
  --resolution "QA PASS; evidence ..." --json

# rig 归档（soft/reversible，不是删除）
rig archive <rigId> --json

# git 侧（QA/MAIN 人工执行）
git tag <code>-done-<date>
git merge --no-ff <branch>
git revert -m 1 <merge-commit>   # 回滚
```

### 5.5 状态映射

| 真实状态 | OpenRig 表达 | 不能写成 |
|---|---|---|
| 用户中止 | workflow `aborted`；qitem `canceled`/`failed` | `done`/`completed` |
| 失败 | workflow `failed`；qitem `failed` | `done` |
| 等待人/外部 | qitem `blocked` / workflow `waiting` | `done` |
| 人工检查点未过 | formal `R16` = `NEED_MAIN`/blocked | `PASS` |
| 已交付下一阶段 | qitem `handed-off` | `done`（除非下一阶段验收） |
| 被替代 | qitem `canceled` + `superseded` + target | `done` |
| rig 停止 | `stopped`/`detached`/`recoverable` | workflow done |
| rig 归档 | `archivedAt` 非空（soft） | 删除/回收 |
| 分支完成 | `merged` + tag | active/stopped |
| 分支废弃 | `abandoned` + tag/记录 | merged |

---

## 6. 当前残留盘点（2026-11-14）

> 只读观测；本轮不清理。当前正在执行的 `stop-sweep` 是唯一 active workflow，不要在本轮中途停止它。

### 6.1 Workflow

- `rig workflow status`：共 **14**；active **1**（`stop-sweep-20261114`，c1）；waiting 0；completed 11；failed 0；aborted 2；attention 空。
- aborted 2：
  - `example-graft-complete-20261111`：opencode model route unavailable；建议 ABANDON/保留历史。
  - `fast-response-adb-round2-20261113`：用户纠正“先做真机适配，暂不执行真机测试”；ABANDON，保留引用。
- 当前 active `stop-sweep` 的 c1 packet 是本轮工作，**不是残留**；完成后 handoff c2。

### 6.2 Qitem / queue

- 当前 active qitem 1：`qitem-20261113160952-3c4ebf69`（stop-sweep c1，in-progress）。
- pending / in-progress / blocked 其他：**0**；`queue undelivered`、`queue overdue` 均为空。
- 历史 recovery qitems（`qitem-recovery-*`）已 canceled/superseded；保留审计，不重新打开。
- 近期 done/handed-off qitems 属于正常历史；不批量删。

### 6.3 Seat / rig

- `rig status`：6 rigs；daemon running/healthy；kernel **auth_blocked**（启动于 daemon-start，与 daemon healthy 不同）。
- `rig ps --nodes -A`：15 nodes；只有 **1 running**（`main-builder@monitor-lite`，assignedWork=1，即本 packet）。
- `sctg-adb-tools`：`attention_required`，`agentActivity.reason=stale_runtime_hook`；无 assigned work。
- `sctg-adb-tools-oc`、`sctg-adb-tools-dsh`、`example-graft-20261111`：detached/recoverable；`example-gov`：node detached、rig lifecycle stopped；均无 assigned work；`assurance-reviewer@example-graft` intentionallyStopped。
- `rig ps --resources`：runningSeats=1；capture 10 次/0 失败；provider/launch/wall-time 等多为 `not_enforced`（预算未强制）。
- `cmux`：unavailable。

### 6.4 Watchdog

- 10 active jobs：7 个 `parked-owner-consumer`（monitor-lite、example-gov、graft、3 个 sctg-adb、fast-response）、2 个 delivery-digest、1 个 `workflow-keepalive`（stop-sweep）。
- 旧 rig 的 parked-consumer 仍 active，但当前不 action；可在 QA 后评估停止/归档，不能盲停。
- 本 rig 的 parked-consumer 是之前延迟唤醒的来源；若 QA 确认不再需要，可 `rig watchdog stop <jobId>`，但需 MAIN/owner 同意。

### 6.5 Git / branch / docs

- 当前 branch：`feat/quiet-200`；HEAD `280de35`。
- branch heads：`remediation/20261113`=280de35、`feat/r15-ux6`=280de35、`feat/quiet-200`=280de35、`main`=54b23dc。
- 三个支线/集成分支同 commit，**无独有 commit**；工作树 **77 dirty**；无 stash、无额外 worktree、无 quiet/UX6 tag。
- 分支文档/ledger：`docs/branches/UX6-R15.md`、`QUIET-200.md`、`REFERENCE-INDEX.md`、`reports/branches/BRANCH-LEDGER.json`、`SYNC-GUARD.md`、`SYNC-MANIFEST.json`。
- 结论：QUIET-200 基线未冻结（deck issue 01）；停止时只能冻结，不能 merge/delete/清 dirty。

### 6.6 文档/证据

- `reports/issues/`：SIX-ISSUES、QUIET-200 PLAN、QUIET-200 FOLLOWUP。
- `reports/branches/`：BRANCH-LEDGER、SYNC-GUARD、SYNC-MANIFEST。
- `reports/sctg/FORMAL-RUN-STATE.json`：R16 blocked/NEED_MAIN；R15 last closed。
- `reports/monitor/MONITOR-BUILD-REPORT.md`：监控台 Round 2 证据（另一条线，不在 stop-sweep 清理范围）。
- `docs/MONITORING-DASHBOARD-PLAN.md`、`docs/DEBUG-CHANNEL.md` 等未提交文档；不是 stop-sweep 产物，不动。

### 6.7 临时文件

- 沙箱内 `/tmp` 是 tmpfs（空）；宿主 `/tmp` 因 sandbox/PID namespace 不可见。
- 宿主临时区可能含原始截图、tmux send 脚本、Chrome profile、OpenRig job 文件；**不读取、不复制、不提交**。
- QA 只按“路径类别/数量/时间”盘点；原始截图/聊天正文不进入归档证据。

### 6.8 Locks / ports / services

- Locks（只读 stat，不读内容）：
  - `<DSH_HOME>/clawbot-bridge/control/bridge.lock` 212B，mtime 2026-11-13 19:51
  - `<DSH_HOME>/clawbot-bridge/control/ctl.lock` 160B，mtime 2026-11-11 23:02
  - `<DSH_HOME>/clawbot-bridge/graft/graft.lock` 94B，mtime 2026-11-11 23:03
  - `<DSH_HOME>/clawbot-bridge/adb-remote/lock.flock` 0B，mtime 2026-11-13 23:17
  - `<DSH_HOME>/restart-3080.lock` 0B，`<DSH_HOME>/watch-flash.lock` 0B/`.pid`，`<DSH_HOME>/web.pid`
- 端口：`<IP>:7433`（OpenRig，200）、`<IP>:3080`（401）、`<IP>:3090`（401）；tailnet `<IP>:7433` 监听。
- systemd user bus 在沙箱不可用；`systemctl --user is-active` 失败，**不能据此判断服务停止**；需宿主桌面/QA 用 systemd 命令确认。
- `ps` 在 PID namespace 只看到沙箱进程，不能当宿主进程清单；用 `rig ps`/端口/锁为准。
- 禁止盲杀 3080/3090/7433 或清 lock；先确认 owner/服务/QA。

### 6.9 只读目录

- staging `governance-20261110/staging/bridge repo`：旧副本（版本号 3.2.2 但非 live），不可当源。
- snapshots `governance-20261110/snapshots/**`：只读；`SNAPSHOT-pre.sha256` 1002 文件校验 OK。
- dist `dist/v3 workspace-share-20261025`：生成物 3.0.0；live 3.2.2；允许差异。
- bridge-app：external 0.2.1；独立 Android 工作区。
- 这些目录的同步/归档规则见 `reports/branches/SYNC-GUARD.md` / `SYNC-MANIFEST.json`。

### 6.10 主链/支线关系

- 主链：`remediation/20261113`；最后已闭合 R15；R16 **NEED_MAIN**；不跳过 R16。
- 父支线 `UX6-R15` / `feat/r15-ux6`：active；I1–I6 收编；I3 外置 Android。
- 子支线 `QUIET-200` / `feat/quiet-200`：active；U2a/U2b；基线未冻结（deck issue 01）。
- 监控台 `monitor-lite`：Round 1/2 完成；不是本 stop-sweep 的清理对象。
- 本 stop-sweep 是治理轮，不是主链产品轮；完成/停止/归档都不得改变 R15/R16 结论。

---

## 7. 证据与隐私边界

**允许写入证据**：

- 命令、退出码、文本输出（不含聊天正文）。
- 文件路径/大小/哈希、git commit/tag、端口、锁 stat、JSON 字段。
- 问题编号、代码位置、测试结果。

**禁止写入证据**：

- 原始截图、聊天正文、媒体正文、文件内容、token、`Authorization`、带 token URL、`data:`/blob、logcat 正文、UI dump 正文。
- 共享设备可读的隐私内容；QA 只记录“已按隐私规则销毁/不保留”。

**回滚证据**：

- 分支/commit/tag、snapshot 路径/哈希、staging 只读副本、归档包 + manifest。
- 回滚命令与验证输出；不把“已停止”当回滚完成。

---

## 8. 与 R15/R16、QUIET-200、UX6-R15 的关系

1. **R15 是锚点，R16 是回归点**：停止/收尾完成后回到 R16；R16 的 NEED_MAIN 未完成前不进入 R17。
2. **QUIET-200/UX6 不因 stop-sweep 自动合并/删除**：未 QA/未冻结基线前保持 active；stop-sweep 只冻结、盘点、交 QA。
3. **I3 是 external Android**：不在 Web 支线里清理/合并；由独立 Android 工作区/轮次处理。
4. **监控台是另一条已完成线**：不进入 stop-sweep 的废弃/回收；只保留其证据。
5. **正式 30 轮**：R16 仍 blocked/NEED_MAIN；不得用 stop-sweep 的完成状态覆盖。

---

## 9. 收尾完成标准

- [ ] 停止原因/时间/发起人已记录；当前 branch/HEAD/dirty 已冻结。
- [ ] workflow/qitem/queue/seat/git/docs/temp/locks/services 已盘点。
- [ ] QA 任务已新建/保留/重启，owner 独立于实现者。
- [ ] 每项残留已分类为 CLOSE_OUT/ABANDON/ARCHIVE_RECYCLE，并有证据/owner/动作/回滚。
- [ ] 没有把 stopped/aborted/blocked/NEED_MAIN 记成 done/PASS。
- [ ] QUIET/UX6 未被未授权 merge/delete；R16 未跳过。
- [ ] 敏感数据未入库；只读目录未被修改。
- [ ] 收尾记录 + 证据 + 回滚路径已落盘；主链回到 R16。

## 10. 本轮不做什么

- 不停止/重启/杀任何进程或服务；不清锁/端口；不删文件/分支/worktree/qitem/snapshot/staging/dist。
- 不执行 `rig workflow abort`/`rig down`/`rig archive`/`rig watchdog stop`。
- 不替 QA 分类，不替 MAIN 决定 R16/QUIET/UX6。
- 不读/提交原始截图、聊天正文、token、logcat。
- 不写 c2 的 `CLOSEOUT-MANUAL.md`/`QA-CLOSEOUT-TASK.md`（c2 负责）。

## 11. 引用

- `discussions/stop-sweep-20261114/BRIEF.md`
- `docs/BRANCHING-PROTOCOL.md`
- `docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`
- `reports/branches/SYNC-GUARD.md`、`reports/branches/SYNC-MANIFEST.json`
- `reports/sctg/FORMAL-RUN-STATE.json`
- `reports/issues/QUIET-200-FOLLOWUP.md`
- `reports/operations/STOP-SWEEP.json`（机器可读）
