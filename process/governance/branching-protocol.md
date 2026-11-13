# 支线协议（Branch Protocol）

> 目的：从主链拉出支线时，位置、编号、范围和回归点必须可审计，避免“支线做完了但不知道回主链哪一步”。

## 1. 锚点规则

支线必须锚定在**主链最后一个已闭合的轮次之后**，而不是锚在“部分完成但未标记完成”的轮次上。

- 锚点 = `last_closed_mainline_round`
- 回归点 = 锚点之后的第一个主链轮次
- 未闭合/NEED_MAIN 轮次不能作为锚点；支线回归时回到该轮继续，不跳过它

当前实例：

```text
主链：remediation/20261113
最后已闭合：R15
R16：NEED_MAIN（部分完成，未闭合）
支线锚点：R15 之后、R16 之前
支线回归点：R16
```

## 2. 支线元数据

每个支线必须记录：

```yaml
code: QUIET-200
branch: feat/quiet-200
parent_branch: remediation/20261113
base_commit: 280de358...
branched_at: 2026-11-13T23:52:50+08:00
mainline_anchor_round: R15
rejoin_round: R16
scope: [U2a, U2b]
write_scope: [...]
status: active | qa | merged | abandoned
```

## 3. 编号规则

- 支线轮次使用**独立命名空间**，不占用主链 R 编号。
- 顶层格式：`<CODE>-01`、`<CODE>-02`……
- 子轮格式：`<CODE>-02a`、`<CODE>-02b`……
- 一个顶层支线轮可以包含多个子轮；子轮完成后才关闭顶层轮。
- 主链 R16 在支线期间保持不变，不被支线编号覆盖。

示例：

```text
UX6-R15-01  I4 键盘+指令两行
UX6-R15-02  I6 静默预加载 + 最近200条持久化
  UX6-R15-02a  静默预加载
  UX6-R15-02b  IndexedDB 200条/离线搜索
UX6-R15-03  I2 指令来源色
UX6-R15-04  I1 日历可用日
UX6-R15-05  I5 待整理查看
UX6-R15-06  I3 原生齿轮/返回（独立 Android 支线）
```

## 4. 范围规则

- 每条支线必须有明确 write scope；跨仓库/原生 Android 任务单独开支线，不能混在 Web 支线里。
- I3 属于 `bridge-app` 原生壳，建议单独 `ANDROID-*` 支线，锚点同上，回归点同样 R16。
- I5 跨 Swift/Node/前端，必须先过隐私门和只读 DTO 设计，再动写操作。

## 5. 收口与回归

支线完成必须经过：

1. 所有支线轮 PASS；
2. 独立 QA（不是实现者自检）；
3. write scope 无越界；
4. 回归测试/真机验收通过；
5. 文档、证据、缓存/schema 版本说明齐全；
6. `git tag <code>-done-<date>`；
7. `git merge --no-ff` 回集成支线（当前为 `remediation/20261113`）；
8. 在回归点恢复主链：R16 继续，不跳过；
9. R16 自己的 NEED_MAIN 项完成后，才允许继续 R17。

## 6. 回滚

- 合并前：直接丢弃/保留支线；
- 合并后：`git revert -m 1 <merge-commit>`；
- 数据 schema（IndexedDB/cache）必须带版本，回滚时可忽略/清理，不阻塞聊天。

## 7. 当前支线状态

- 已建父支线：`UX6-R15` / `feat/r15-ux6`，锚点 `R15`，回归点 `R16`。
- 已建子支线：`QUIET-200` / `feat/quiet-200`，对应 `UX6-R15-02`。
- 详细台账：`docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`、`reports/branches/BRANCH-LEDGER.json`。


## 8. 中途停止与收尾

总任务中途停止时，按标准手册执行，不要每次现写：

- 标准收尾手册：`docs/CLOSEOUT-MANUAL.md`（v1.0.0，标准/复用）
- QA 收尾任务模板：`reports/operations/QA-CLOSEOUT-TASK.md`
- 收尾台账模板：`reports/operations/CLOSEOUT-LEDGER-TEMPLATE.json`
- 本次 STOP-SWEEP 分析：`reports/operations/STOP-SWEEP.md`

铁律：停止不是 done；先冻结、盘点，再由独立 QA 分为
`CLOSE_OUT` / `ABANDON` / `ARCHIVE_RECYCLE`；收尾后回到主链回归点 R16，不跳过。


## 9. 中途插入（INSERT-GUARD）

跑到一半收到新内容/新要求/新 bug/验收变化时，按标准插入协议，不要直接改当前轮：

- 标准协议：`docs/MIDRUN-INSERTION-PROTOCOL.md`（v1.0.0，标准/复用）
- 插入记录模板：`reports/operations/INSERTION-LEDGER-TEMPLATE.json`
- 本次分析/示例：`reports/operations/MIDRUN-INSERTION.md` / `.json`
- 引用索引：`docs/branches/REFERENCE-INDEX.md`

规则：

1. **先记录再分类**：六类 `CLARIFY` / `INLINE_EXTEND` / `NEXT_ROUND` / `SIDE_BRANCH` / `URGENT_STOP` / `GATE_CHANGE`；记录必须有 `insertId/source/receivedAt/anchor/currentRound/branch/scope/owner/status/decision/evidence`。
2. **默认 NEXT_ROUND**：不打断当前轮；新内容进插入队列，下一轮消费；当前 packet body/scope 不被静默修改。
3. **INLINE_EXTEND** 必须 owner 确认且不扩 write scope/不改 gate；验收变化转 `GATE_CHANGE`。
4. **SIDE_BRANCH** 按本协议 §1–§2 锚定最后闭合轮（当前 R15），更新 branch ledger/reference index；不混入当前 Web 分支/`bridge-app`。
5. **URGENT_STOP/GATE_CHANGE** 命中硬条件（scope/gate/安全/数据/分支基线/用户停止）时走 `docs/CLOSEOUT-MANUAL.md` + `reports/operations/STOP-SWEEP.md`；GATE_CHANGE 由 MAIN/QA 重开。
6. **R15/R16**：插入不跳过 R16；NEXT_ROUND 在 R16 后消费；SIDE_BRANCH rejoin R16；GATE_CHANGE 仍回 R16 重新验收。
7. **不能做什么**：不改当前 qitem body/scope 吸收插入；不把插入写进当前证据当原始验收；不用 `done` 腾地方；不用 `rig send` 代替持久记录；未 QA 不 merge/delete/清锁。


## 10. 单独轮（STANDALONE）

一次一议、不属于正式 30 轮、不占 R 编号的工作，走单独轮，不要混成支线或永久 dirty：

- 标准协议：`docs/rounds/STANDALONE-ROUND-PROTOCOL.md`（v1.0.0）
- 模板：`docs/rounds/STANDALONE-ROUND-TEMPLATE.md`、`reports/rounds/STANDALONE-ROUND-TEMPLATE.json`
- 台账：`reports/rounds/STANDALONE-ROUNDS.json` / `.md`
- 别名：离散轮/零散轮；ID `SOLO-YYYYMMDD-NN`

规则：

1. 单独轮必须写 `anchor`（默认最后闭合 R15）、`branch`、`rejoin`（默认 R16）、`scope`、`strategy`、`gate`、`qa`、`evidence`、`lifecycle`；不占 R 编号。
2. 多轮/持续合并/需要 branch ledger 的工作 → 升级为支线；不要用单独轮永久漂移。
3. `ANALYZE/GOVERN/OPS/QA/RESEARCH` 不写产品代码；`SMALL_FIX` 必须有小范围 write scope + 测试 + QA + 回滚；`RECOVERY` 按 CLOSEOUT-MANUAL。
4. 关闭/废弃/归档必须处理工作树/分支；不留永久 dirty。
5. 中途插入的 `NEXT_ROUND`/`SIDE_BRANCH` 可落成单独轮；`URGENT_STOP`/`GATE_CHANGE` 走 STOP-SWEEP/MAIN。
6. 不跳过 R16；不把 NEED_MAIN 写成 PASS。


### 10.1 fast-response 分支计划（未创建）

`SOLO-20261114-05` 已将 `SOLO-20261113-01` 的 candidate 处置为 `PROMOTE_TO_BRANCH`：

- 计划 codename：`feat/fast-response`
- base：`280de35`（R15 锚点）
- rejoin：R16
- 分支文档：`docs/branches/FAST-RESPONSE.md`（待写）
- 收敛门：单写者锁/并发、R2 身份不证明即中止、目标测试/`node --check`、安全设备证据、debug 默认 404/回滚、独立 QA、R16 回归
- **本轮不建分支**；先写 branch doc/ledger，并在后续授权轮处理当前 80 dirty 的 freeze/split。
- 详见 `reports/rounds/SOLO-20261114-05-MANAGEMENT.md`。


### 10.2 SOLO-06 审计后的基线备注

`SOLO-20261114-06` 审计确认主/快 worktree clean，但发现 B2/B3/base 文档漂移：

- B2 = `7680b1d`；B3（观测）= `dcd9f93`；`baseline/remediation-20261114` 实际已指向 B3。
- `feat/fast-response` 实际 merge-base 为 B2 `7680b1d`，但 `FAST-RESPONSE.md` / `BRANCH-LEDGER` 写 B1 `f973b3f`，SOLO-05 management 写 B0 `280de35`。
- 下一步：先修元数据（B2/B3/base），再 FAST-RESPONSE 独立 QA；不立即 merge、不跳过 R16。
- 证据：`reports/rounds/SOLO-20261114-06-REPO-AUDIT.md`、`reports/rounds/SOLO-20261114-06-NEXT-STEP.md`。


## 11. 总指挥部（COMMAND-CENTER）

非 SOLO 的长运行轮/主支统一登记到总指挥部，避免切轮/停轮/冲突时靠聊天记忆：

- 标准协议：`docs/command-center/COMMAND-CENTER.md`（v1.0.0）
- 机器台账：`reports/command-center/ROUND-REGISTRY.json`
- 人读视图：`reports/command-center/ROUND-REGISTRY.md`
- CLI：`node tools/round-command-center.mjs list|show|conflicts|validate`

规则：

1. 登记对象：正式 30 轮、集成线、父/子支线、外部 Android；**不登记 SOLO-***。
2. 必填：`id/kind/title/status/owner/branch/worktree/base/head/anchor/rejoin/currentRound/scope/resourceKeys/conflictKeys/lastSeenAt/links/notes`。
3. 长运行轮在开始/切轮/停止/合并时更新 registry；状态/分支/base 与 `BRANCH-LEDGER.json` / `FORMAL-RUN-STATE.json` 一致。
4. 冲突：两个 active 条目共享 `resourceKey` = 冲突候选；只读 registry，不遍历全库。当前已知 `UX6-R15` ↔ `QUIET-200` 共享 `path:sim/app.js`，属父子重叠，需按顺序协调。
5. 查询以 CLI/registry 为准；全库遍历不是常规查询方式。
6. 总指挥部不替代 STOP-SWEEP/INSERT-GUARD/CLOSEOUT；只提供轮次/资源视图。


## 12. 单独轮标戳（SOLO STAMP）

单独轮（`SOLO-*`）必须在自己的根目录写 `.solo-round.json`，作为机器识别主真值：

- 协议：`docs/rounds/SOLO-STAMP-PROTOCOL.md`（v1.0.0）
- 工具：`tools/solo-round-stamp.mjs`（`stamp` / `collect` / `verify` / `find`）
- 台账：`reports/rounds/STANDALONE-ROUNDS.json`（`stampPath` / `stampMode` / `stampStatus`）
- 规则：一个 ID 一个 stamp；不登记 out-of-scope；主文档 marker 可选；stamp 与 registry 不一致时 `verify` 失败，必须修。
- 沙箱只读 fallback：源目录不可写时写 `reports/rounds/stamps/<ID>/.solo-round.json`，`stampMode=mirror`、`stampStatus=MIRROR`；宿主有写权限后复制回 `stampTarget` 再 verify。
- 不移动/重命名单独轮来源目录；不把 stamp 写到支线/正式轮根目录。


## 13. 总参谋部（GENERAL-STAFF）

思考类单独轮进总参谋部索引/评估，不替代 command center 或分支协议：

- 标准：`docs/general-staff/GENERAL-STAFF.md`（v1.0.0）
- 索引：`reports/general-staff/THINKING-ROUNDS.json` / `.md`
- 24 维：`reports/general-staff/THINKING-DIMENSIONS.json` / `.md`
- Playbook：`reports/general-staff/THINKING-PLAYBOOK.md`
- 人才台账：`reports/general-staff/TALENT-LEDGER.json`
- 强制咨询：`docs/general-staff/THINKING-CONSULTATION-PROTOCOL.md`
- 模板：`templates/thinking-workflow.yaml`、`templates/thinking-workflow-2seat.yaml`
- 考评：`reports/general-staff/ROUND-EVALUATION-TEMPLATE.json`、`ROUND-EVALUATIONS.json` / `.md`
- 规则：13 条 SOLO 全部索引；primary 9 / secondary 4 / none 0；THINK-20261114-01..13；first-pass 评分 A9/B4，平均 42.0；24 维/playbook/咨询协议已落盘。
- `.staff-thinking.json` 是补充，不改 `.solo-round.json`；1 in-place + 12 mirror 待宿主复制。
- 不选最终人才；下一轮再做维度/人才分析。R16 仍 NEED_MAIN，不跳过。
