# OpenRig 总指挥部 · 轮次集散中心标准协议

- **协议版本**：`v1.0.0`（standard，2026-11-14）
- **状态**：`standard / reusable` —— 长期复用的轮次登记/冲突查询标准，不是一次性视图。
- **范围**：登记所有**非 SOLO** 的长运行轮/主支；提供按 ID、status、resourceKey 查询与冲突候选。
- **Owner**：Lead/MAIN；日常维护由当前轮 owner 负责，Lead 审核。
- **机器台账**：`reports/command-center/ROUND-REGISTRY.json`
- **人读视图**：`reports/command-center/ROUND-REGISTRY.md`
- **CLI**：`tools/round-command-center.mjs`
- **不登记**：`SOLO-*` 单独轮（由 `reports/rounds/STANDALONE-ROUNDS.json` + STANDALONE 协议管理）。

---

## 0. 目的

让“现在有哪些长运行轮/支线、谁在跑、跑在哪个 branch/worktree、占用什么资源、和谁冲突”在一个 registry 里可查，不需要每次遍历全库。

解决的三个问题：

1. **切轮/停轮时找不到当前状态**：统一字段 + 更新触发。
2. **两个轮同时改同一文件/分支**：resourceKey 重叠 + active 状态 = 冲突候选。
3. **主线/支线/正式轮关系散落**：registry 作为总指挥部视图，细节仍以 branch doc/ledger/formal state 为准。

---

## 1. 登记边界

### 1.1 登记

- 正式 30 轮（`FORMAL-30-*`）
- 集成线（`REMEDIATION-*`）
- 父/子支线（`UX6-R15`、`QUIET-200`、`FAST-RESPONSE`）
- 独立外部支线（`ANDROID-*`，`bridge-app`）
- 其它长运行、跨多轮、需要 branch/worktree/冲突视图的轮

### 1.2 不登记

- `SOLO-*` 单独轮：见 `docs/rounds/STANDALONE-ROUND-PROTOCOL.md`。
- 一次性分析报告/模板/输出物：不是“长运行轮”。
- 已关闭且无活跃引用的历史产物：留 branch doc/ledger 索引，不进 active registry。
- 原始截图/聊天正文/token/logcat：永不入 registry。

### 1.3 与 SOLO 的边界

| 对象 | 管理 |
|---|---|
| 单独轮 `SOLO-*` | STANDALONE registry；一次性、有 closeout |
| 长运行轮/主支 | 本 command center；持续 branch/worktree/冲突视图 |
| 从 SOLO 升级的支线（如 FAST-RESPONSE） | 进本 registry；SOLO registry 保留来源 |

---

## 2. 字段

每条 entry 必须有：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 唯一 ID；建议 `FORMAL-30-*`/`REMEDIATION-*`/`UX6-R15`/`QUIET-200`/`FAST-RESPONSE`/`ANDROID-*` |
| `kind` | enum | `formal` / `integration` / `branch` / `external` |
| `title` | string | 简短标题 |
| `status` | enum | `active` / `active-qa-ready` / `blocked` / `waiting` / `qa` / `planned` / `paused` / `done` / `merged` / `abandoned` |
| `owner` | string | 当前 owner/角色 |
| `branch` | string | 分支；external/planned 可 `TBD` |
| `worktree` | string | 工作树绝对路径或 `N/A` |
| `baseCommit` | string | 分支 base/分叉 commit |
| `headCommit` | string | 当前 head；未知写 `UNKNOWN` |
| `anchorRound` | string | 主链锚点（当前 R15） |
| `rejoinRound` | string | 回归点（当前 R16） |
| `currentRound` | string | 当前轮/step |
| `scope` | string[] | 范围（问题/模块/轮次） |
| `resourceKeys` | string[] | 占用资源；冲突判定用 |
| `conflictKeys` | string[] | 参与冲突判定的键；必须是 resourceKeys 子集 |
| `lastSeenAt` | ISO | 最后一次确认时间 |
| `updatedAt` | ISO | 记录更新时间 |
| `links` | object | 相关 doc/ledger/formal state 路径 |
| `notes` | string | 简短备注；不含敏感正文 |

### 2.1 resourceKey 命名

| 前缀 | 示例 | 用途 |
|---|---|---|
| `branch:` | `branch:feat/fast-response` | 分支占用 |
| `worktree:` | `worktree:fast-response` | 独立工作树 |
| `path:` | `path:sim/app.js` | 文件/目录写占用 |
| `scope:` | `scope:QUIET-200` | 逻辑范围 |
| `round:` | `round:R16` | 正式轮 |
| `integration:` | `integration:remediation` | 集成线 |
| `external:` | `external:bridge-app` | 外部仓 |

规则：

- 一个 key 只表达一个可冲突资源；不要用 `repo:bridge repo` 这种所有条目都共享的 key，否则冲突全是噪音。
- `conflictKeys` 可少于 `resourceKeys`（例如只把写路径放入冲突判定）。
- 父子支线共享路径（UX6/QUIET 的 `path:sim/app.js`）会显示为冲突候选；这是**已知父子重叠**，需按父子顺序协调，不是未知冲突。

---

## 3. 状态模型

```text
planned → active → active-qa-ready → qa → done/merged
             ├→ blocked/waiting/paused
             └→ abandoned
```

| 状态 | 是否 active（参与冲突） | 含义 |
|---|---|---|
| `active` | 是 | 正在执行 |
| `active-qa-ready` | 是 | 实现完成，待独立 QA |
| `blocked` | 是 | 等人/外部/gate；仍占资源 |
| `waiting` | 是 | 等条件；仍占资源 |
| `qa` | 是 | QA 进行中 |
| `planned` | 否 | 未开始，不占 active 资源 |
| `paused` | 否 | 明确暂停，不占 active 资源 |
| `done` | 否 | 已完成/关闭 |
| `merged` | 否 | 已合并 |
| `abandoned` | 否 | 明确废弃 |

`activeStatuses` 固定在 registry 中；CLI 以此判定，不靠猜。

---

## 4. 冲突查询语义

### 4.1 定义

**两个 active 条目共享同一个 `resourceKey` = 冲突候选。** `conflictKeys` 是 `resourceKeys` 的显式子集，用于声明/展示，不改变 resourceKey 判定。

- 只读 `ROUND-REGISTRY.json`；不遍历全库、不读源码、不读日志。
- 冲突是“候选”，不是自动判定谁对谁错；owner 必须确认/协调。
- `validate` 检查 schema/字段/子集；`conflicts` 输出冲突候选；`validate --strict` 把冲突当失败。

### 4.2 当前已知

- `UX6-R15` ↔ `QUIET-200`：共享 `path:sim/app.js`，已知父子重叠；先父后子/先子后父由 owner 协调。
- 其余 active 条目当前无共享 key。
- 冲突数变化时，registry 的 `updatedAt` 和 `lastSeenAt` 必须更新。

### 4.3 不做什么

- 不把“共享 repo”当冲突；不用全库 grep 代替 registry。
- 不把 `planned`/`done`/`merged` 纳入 active 冲突。
- 不在冲突查询里读取产品代码/聊天/截图。

---

## 5. CLI

```bash
node tools/round-command-center.mjs list
node tools/round-command-center.mjs list --active
node tools/round-command-center.mjs show FAST-RESPONSE
node tools/round-command-center.mjs conflicts
node tools/round-command-center.mjs validate
node tools/round-command-center.mjs validate --strict
```

- `list`：全部；`--active` 仅 active 状态；`--json` 机器输出。
- `show <id>`：单条；`--json`。
- `conflicts`：active 两两 resourceKey 交集；`--json`。
- `validate`：schema、必填、唯一 ID、active 必填、conflictKeys 子集、无 SOLO；`--strict` 冲突也失败。
- 退出码：0 成功；1 validate/show 失败；2 用法/IO 错误。
- `--registry <path>` 可指向测试 registry（不修改默认）。

---

## 6. 维护流程

### 6.1 触发

长运行轮/主支必须在以下时点更新 registry：

1. **开始**：status active，写 owner/branch/worktree/base/head/currentRound/scope/resourceKeys。
2. **切轮**：更新 currentRound、head、lastSeenAt。
3. **停止/阻塞**：status blocked/waiting/paused，notes 写 wait reason；不要只改聊天。
4. **合并/完成/废弃**：status merged/done/abandoned，links 写 evidence；从 active 冲突集移除。
5. **审计/交接**：更新 lastSeenAt，修漂移（如 base/head 与 ledger 不一致）。

### 6.2 Owner

| 动作 | Owner |
|---|---|
| 新增/更新 entry | 当前轮 owner |
| 冲突协调 | 相关轮 owner；Lead/MAIN 裁决 |
| registry schema/CLI | Lead/MAIN |
| 正式轮状态 | MAIN/QA |
| 外部 Android | Android owner |

### 6.3 与 branch ledger/formal state 一致

- `status`/`branch`/`baseCommit`/`headCommit` 必须与 `reports/branches/BRANCH-LEDGER.json` / `reports/sctg/FORMAL-RUN-STATE.json` 一致。
- 若发现不一致（如 FAST-RESPONSE base 文档漂移），registry 应记录已知差异 + `notes`，不能静默改成“看起来对”的值；由 Lead 修源文档后再统一。
- 不复制完整 branch doc；只引用 `links`。

---

## 7. 与其它协议

| 协议 | 关系 |
|---|---|
| `docs/BRANCHING-PROTOCOL.md` | branch/base/rejoin/合并规则；registry 是视图，不替代协议 |
| `docs/rounds/STANDALONE-ROUND-PROTOCOL.md` | SOLO 不进本 registry；升级支线后进 |
| `docs/MIDRUN-INSERTION-PROTOCOL.md` | 插入可产生 NEXT_ROUND/SIDE_BRANCH；进入本 registry 时登记 |
| `docs/CLOSEOUT-MANUAL.md` | 停止/收尾时更新 status；registry 不替代 closeout |
| `reports/branches/SYNC-GUARD.md` | 目录/引用一致性；registry 路径必须在索引中 |
| R15/R16 | anchor R15，rejoin R16；不跳过 R16、不把 NEED_MAIN 写 PASS |

---

## 8. 隐私/安全

- registry 只存 ID/path/status/owner/resourceKey，不存聊天正文、token、原始截图、logcat。
- `links` 只写文档/台账路径，不写敏感内容。
- CLI 只读 registry，不读产品源码/日志/图片。
- 共享设备上，registry 的 path 也不应包含用户隐私目录。

## 9. 验收

- [ ] `ROUND-REGISTRY.json` 可解析，schema/version 正确。
- [ ] 所有 entry 有必填字段；ID 唯一；无 SOLO。
- [ ] active 条目的 branch/worktree/head/currentRound/owner 非空。
- [ ] `conflictKeys` ⊆ `resourceKeys`。
- [ ] `list`/`show`/`conflicts`/`validate` 可运行；`validate` 无 error。
- [ ] 冲突只按 registry 计算，不遍历全库。
- [ ] 状态/分支/base 与 ledger/formal state 一致；已知漂移写入 notes。
- [ ] 文档/索引引用存在。

## 10. 变更记录

| 版本 | 日期 | 作者/角色 | 变更 |
|---|---|---|---|
| v1.0.0 | 2026-11-14 | builder / MAIN review | 建立总指挥部：边界、字段、状态、冲突语义、CLI、维护流程、与 SOLO/STOP/INSERT/R15-R16 关系。 |
| v1.0.1 | `<YYYY-MM-DD>` | `<maintainer>` | `<change>` |
