# 单独轮初始台账（STANDALONE-ROUNDS）

- 日期：2026-11-14
- 台账版本：`v1.0.9`（SOLO-09/10 登记）
- 协议：`docs/rounds/STANDALONE-ROUND-PROTOCOL.md`（单独轮 / 离散轮 / 零散轮）
- 机器可读：`reports/rounds/STANDALONE-ROUNDS.json`
- 模板：`docs/rounds/STANDALONE-ROUND-TEMPLATE.md`、`reports/rounds/STANDALONE-ROUND-TEMPLATE.json`
- 约束：只登记/索引；不改产品代码、不重开已关闭历史、不把支线/正式轮误登记为单独轮。

> 路径口径：`discussions/*` 相对 workspace root `<WORKSPACE>`；`reports/*`、`docs/*`、`test/*` 相对 repo root `.../bridge repo`。
>
> 历史条目使用 **retrospective ID**（`SOLO-<起始日期>-NN`）；`anchor/rejoin` 统一下按当前主链 R15/R16 映射，closed 历史不重开。ID 是登记标识，不代表当时已有该编号。

## 0. 汇总

| 项 | 数量 |
|---|---|
| confirmed standalone | 14 |
| candidate | 1 |
| out-of-scope | 10 |
| ACTIVE | 0 |
| needsTreatment | 0 |
| disposition | KEEP_CLOSED 14 / PROMOTE_TO_BRANCH 1 |
| stampStatus | OK 13 / MIRROR 2（SOLO-09/10） |
| staffClass | primary 9 / secondary 4 / none 0 |
| staffIndexed | 13（SOLO-09/10 meta 未入 13 条索引） |
| staffGrade | A 9 / B 4 / C 0 / D 0 |
| staffAverage | 42.0（first-pass） |

> 口径：本文件是 v1.0.9 快照（`staffIndexed 13`，`SOLO-09/10` meta 轮未入索引）；后续总参谋部索引见 [`thinking-rounds.md`](thinking-rounds.md)（15 条）。

| 分类 | 含义 |
|---|---|
| **confirmed** | 已有明确产物/验收/关闭记录，可视为单独轮 |
| **candidate** | 形态像单独轮，但多轮/验收/边界需下一轮确认 |
| **out-of-scope** | 支线、正式轮、输出物/模板、历史 run；不登记为 SOLO |

## 1. confirmed

| ID | 标题 | 来源 | Anchor/Branch/Rejoin | 策略 | 状态 | 证据 | 需收治 |
|---|---|---|---|---|---|---|---|
| `SOLO-20261026-01` | g3d overlay 使用场景/模式模拟 | `discussions/g3d-usage-sim-20261026` | R15 / discussion read-only / R16（历史关闭） | RESEARCH + ANALYZE | CLOSED | `FINAL.md`、`ACCEPTANCE.md`（PASS 6/6） | 否 |
| `SOLO-20261113-02` | 六条真机 UI 问题查收 | `discussions/issue-intake-20261113` | R15 / read-only / R16 | ANALYZE + GOVERN | CLOSED | `reports/issues/SIX-ISSUES-INTAKE-20261113.*` | 否 |
| `SOLO-20261113-03` | 监控台 Round 1/2 | `discussions/monitor-console-20261113` | R15 / remediation worktree / R16 | SMALL_FIX + GOVERN | CLOSED | `reports/monitor/MONITOR-BUILD-REPORT.md`、`docs/MONITORING-DASHBOARD-PLAN.md` | 否（git hygiene 另由 STOP-SWEEP） |
| `SOLO-20261113-04` | 本地桥功能对比与取舍 | `reports/compare-20261113` | R15 / read-only / R16 | ANALYZE + RESEARCH | CLOSED | `COMPARISON-QUICK-REFERENCE.md`、`VERIFY-COMPARISON.md` | 否 |
| `SOLO-20261114-01` | SYNC-GUARD 多文件夹一致性 | `discussions/sync-guard-20261114` | R15 / feat/quiet-200 worktree / R16 | GOVERN + ANALYZE | CLOSED | `reports/branches/SYNC-GUARD.md`、`SYNC-MANIFEST.json`、`QUIET-200-FOLLOWUP.md` | 否 |
| `SOLO-20261114-02` | STOP-SWEEP 停止边界/收尾手册 | `discussions/stop-sweep-20261114` | R15 / feat/quiet-200 worktree / R16 | GOVERN + OPS | CLOSED | `reports/operations/STOP-SWEEP.*`、`docs/CLOSEOUT-MANUAL.md` | 否 |
| `SOLO-20261114-03` | INSERT-GUARD 中途插入协议 | `discussions/insert-guard-20261114` | R15 / feat/quiet-200 worktree / R16 | GOVERN + ANALYZE | CLOSED | `docs/MIDRUN-INSERTION-PROTOCOL.md`、`reports/operations/MIDRUN-INSERTION.*` | 否 |
| `SOLO-20261114-04` | SOLO-GUARD 单独轮协议/初始台账 | `discussions/solo-guard-20261114` | R15 / feat/quiet-200 worktree / R16 | GOVERN + ANALYZE | **CLOSED**（g2 收口） | `docs/rounds/*`、`reports/rounds/*` | 否：已关闭；保持 registry/protocol |
| `SOLO-20261114-05` | 单独轮管理收治 | `discussions/solo-20261114-05` | R15 / feat/quiet-200 worktree / R16 | GOVERN + OPS | CLOSED | `reports/rounds/SOLO-20261114-05-MANAGEMENT.*` | 否：已关闭 |
| `SOLO-20261114-06` | 全库近期更改与干净状态审计 | `discussions/solo-20261114-06` | R15 / 主+fast-response worktree（均 clean） / R16 | OPS + QA | **CLOSED**（审计+next-step） | `reports/rounds/SOLO-20261114-06-REPO-AUDIT.*`、`...-NEXT-STEP.md` | 否：已收口；B2/B3/base 修正是 FAST QA 前置 |
| `SOLO-20261114-07` | OpenRig 总指挥部（轮次集散中心） | `discussions/solo-20261114-07` | R15 / feat/quiet-200 worktree / R16 | GOVERN + OPS | CLOSED | `docs/command-center/COMMAND-CENTER.md`、`reports/command-center/*`、`tools/round-command-center.mjs` | 否：已关闭 |
| `SOLO-20261114-08` | 单独轮识别标戳 | `discussions/solo-20261114-08` | R15 / feat/quiet-200 worktree / R16 | GOVERN + OPS | **CLOSED**（t2 verify） | `docs/rounds/SOLO-STAMP-PROTOCOL.md`、`tools/solo-round-stamp.mjs`、`reports/rounds/SOLO-STAMP-COLLECTION.*`、`SOLO-STAMP-VERIFY.md` | 否：13 stamps verify OK；12 mirror 待宿主复制 |
| `SOLO-20261114-09` | 总参谋部与思考类索引 | `discussions/solo-20261114-09` | R15 / feat/quiet-200 worktree / R16 | GOVERN + ANALYZE | **CLOSED** | `docs/general-staff/GENERAL-STAFF.md`、`reports/general-staff/THINKING-ROUNDS.*`、`ROUND-EVALUATIONS.*` | 否：已关闭；meta 轮未入 13 条 staff 索引 |
| `SOLO-20261114-10` | 思考维度/人才/咨询机制 | `discussions/solo-20261114-10` | R15 / feat/quiet-200 worktree / R16 | ANALYZE + GOVERN | **CLOSED** | `reports/general-staff/THINKING-DIMENSIONS.*`、`THINKING-PLAYBOOK.md`、`TALENT-LEDGER.json`、`THINKING-CONSULTATION-PROTOCOL.md`、`templates/*` | 否：已关闭；meta 轮未入 13 条 staff 索引 |

## 2. candidate

| ID | 标题 | 来源 | Anchor/Branch/Rejoin | 策略 | 状态 | 证据 | 需收治/动作 |
|---|---|---|---|---|---|---|---|
| `SOLO-20261113-01` | 视觉预规划 + Android 快速响应 | `discussions/fast-response-adb-20261113` | R15 / discussion + `tools/adb`（无独立分支） / R16 | RESEARCH + ANALYZE | CLOSED（design） | `FINAL.md`、`VISION.md`、`RUNTIME.md`、`round4/ROUND4-FINAL.md` | 否：已决议 `PROMOTE_TO_BRANCH`；先写分支计划/ledger，后续授权轮再建 `feat/fast-response` |

**candidate 判定**：有 FINAL 设计收口，但包含 4 个子轮、没有独立 QA/单轮边界，暂不直接标 confirmed；不重开历史，只做本轮收治。
**本次决议**：`PROMOTE_TO_BRANCH`，分支计划 `feat/fast-response`（**未创建**）；candidate 不再需要 SOLO 收治，后续按分支协议跟踪。

## 2.1 本次管理收治（SOLO-20261114-05）

| ID | 分类 | disposition | Owner | nextAction | lastReviewedAt |
|---|---|---|---|---|---|
| `SOLO-20261026-01` | confirmed | `KEEP_CLOSED` | Lead/QA | 归档引用；不重开 | `2026-11-14T00:31+08:00` |
| `SOLO-20261113-01` | candidate | `PROMOTE_TO_BRANCH` | Lead/MAIN + QA | 先写 `docs/branches/FAST-RESPONSE.md` + ledger；**本轮不建分支** | `2026-11-14T00:31+08:00` |
| `SOLO-20261113-02` | confirmed | `KEEP_CLOSED` | Lead | I1–I6 由 UX6/QUIET 消费；不重开 | `2026-11-14T00:31+08:00` |
| `SOLO-20261113-03` | confirmed | `KEEP_CLOSED` | Lead | 保留报告；git hygiene 归 STOP-SWEEP | `2026-11-14T00:31+08:00` |
| `SOLO-20261113-04` | confirmed | `KEEP_CLOSED` | Lead | 保留桥对比引用 | `2026-11-14T00:31+08:00` |
| `SOLO-20261114-01` | confirmed | `KEEP_CLOSED` | Lead/QA | 保留 SYNC-GUARD 标准引用 | `2026-11-14T00:31+08:00` |
| `SOLO-20261114-02` | confirmed | `KEEP_CLOSED` | Lead/QA | 保留收尾手册/STOP-SWEEP 标准 | `2026-11-14T00:31+08:00` |
| `SOLO-20261114-03` | confirmed | `KEEP_CLOSED` | Lead/QA | 保留 INSERT-GUARD 标准 | `2026-11-14T00:31+08:00` |
| `SOLO-20261114-04` | confirmed | `KEEP_CLOSED` | Lead/QA | 保留 SOLO 协议/台账；g2 已关闭 | `2026-11-14T00:31+08:00` |

## 2.2 `feat/fast-response` 分支计划（未创建）

| 字段 | 值 |
|---|---|
| 分支 codename | `feat/fast-response` |
| 状态 | `PLANNED_NOT_CREATED`（本轮不建） |
| Base | `280de35`（R15 锚点） |
| Rejoin | R16 |
| Branch doc | `docs/branches/FAST-RESPONSE.md`（待写） |
| Owner | Lead/MAIN；branch owner TBD |
| QA | 独立 QA 必须 |
| Scope | `tools/adb/**`、`tools/debug-input.mjs`、`test/adb-*`、`test/debug-*`、`docs/DEBUG-CHANNEL.md`、`sim/app.js`/`lib/local-io.mjs` 的 debug hunk |
| 不收 | 无关 dirty、`bridge-app/**`、live env/token 变更 |
| 收敛门 | 单写者锁/并发测试；R2 身份不证明即中止；目标测试 + `node --check`；安全设备证据；debug 默认 404/回滚；独立 QA；R16 回归 |
| 冻结要求 | 当前 80 dirty；先 freeze/split pathspec，再建分支；本轮不建 |
| 回滚 | `git revert -m 1 <merge>`；unset debug env + restart 恢复 404 |

**为什么不是 umbrella**：4 个子轮跨 ANALYZE/RESEARCH/SMALL_FIX，包含代码/tooling 和 live 临时测试；单策略/单 gate/单 QA 无法覆盖，容易变永久单独轮。升级支线才有 ledger/收敛门/回滚。

## 2.3 SOLO-06 审计登记

| 字段 | 值 |
|---|---|
| ID | `SOLO-20261114-06` |
| 状态 | `CLOSED`（r1 审计 + r2 next-step） |
| disposition | `KEEP_CLOSED` |
| Owner | Lead/QA |
| 结论 | 两个 worktree clean、stash 空、diff --check PASS；但 4 处 baseline/branch 文档漂移，不能宣布“全库干净一致” |
| 关键不一致 | B3 未命名；`baseline/remediation-20261114` 实际 dcd9f93；fast base 文档 f973/管理报告 280/实际 7680；ledger 缺 b2/b3 |
| nextAction | 执行 next-step：先修 B2/B3/base 元数据，再 FAST-RESPONSE 独立 QA；不改产品代码/不清工作树 |
| 证据 | `reports/rounds/SOLO-20261114-06-REPO-AUDIT.md` / `.json`、`reports/rounds/SOLO-20261114-06-NEXT-STEP.md` |

## 3. out-of-scope

| 对象 | 原因 | 处理 |
|---|---|---|
| `QUIET-200` / `feat/quiet-200` | 子支线、多轮；不是单独轮 | 按 `docs/branches/QUIET-200.md` / BRANCHING-PROTOCOL；SOLO 不重复登记 |
| `UX6-R15` / `feat/r15-ux6` | 父支线、多轮 | 按 `docs/branches/UX6-R15.md`；SOLO 只消费结果 |
| `reports/operations/*` | STOP-SWEEP/INSERT-GUARD 输出/模板 | 引用，不登记为轮 |
| `reports/branches/*` | 分支台账/同步产物 | 引用，不登记为轮 |
| `reports/issues/*` | issue/QUIET 分析输出 | 引用，不登记为轮 |
| `reports/monitor/*` | 监控台输出 | 由 `SOLO-20261113-03` 覆盖 |
| `reports/R1..R7`、`reports/sctg/*` | 正式 30 轮/历史 run | 正式轮协议，不登记 SOLO |
| `reports/rounds/*` | 本协议/模板/台账自身 | 引用，不登记 |
| `discussions/quiet-200-20261114` | QUIET-200 支线分析 | 支线协议 |
| `discussions/monitor-console-20261113` | 已由 `SOLO-20261113-03` 覆盖 | 引用 |

## 4. 下一轮收治 action

| 顺序 | Action | 目标 |
|---|---|---|
| 1 | 执行 `SOLO-06-NEXT-STEP.md`：修 B2/B3/base 元数据，再做 FAST-RESPONSE 独立 QA | 唯一推荐下一步 |
| 2 | QA PASS 后由 MAIN 授权合并到 remediation，再回 R16；不跳过 | 收敛/回归 |
| 3 | `KEEP_CLOSED` 条目只保留引用；不重开；git hygiene 只走 STOP-SWEEP | 避免历史重开 |
| 4 | QUIET/UX6 不登记 SOLO；按分支收敛门 | 避免重复治理 |
| 5 | 新 discussions/reports 出现时按模板登记；避免碎片化 | registry 持续维护 |

## 5. 收治判定

```text
有明确产物/验收/关闭记录，且不是支线/正式轮？
├─ 是 -> confirmed（补 ID/anchor/evidence）
└─ 否 -> 是多轮/支线/正式轮？
   ├─ 是 -> out-of-scope（转对应协议）
   └─ 否 -> candidate（下一轮确认边界/验收）
```

## 6. 不做什么

- 不重开已 CLOSED 历史；不把公开/历史产物改写为“当前完成”。
- 不把 QUIET/UX6 支线、正式 30 轮、输出物登记为 SOLO。
- 不删/移历史文件；台账只引用。
- 不提交原始截图/聊天正文/token。

## 7. 引用

- `docs/rounds/STANDALONE-ROUND-PROTOCOL.md`
- `docs/rounds/STANDALONE-ROUND-TEMPLATE.md`
- `reports/rounds/STANDALONE-ROUND-TEMPLATE.json`
- `docs/BRANCHING-PROTOCOL.md` §10（单独轮）
- `docs/MIDRUN-INSERTION-PROTOCOL.md`（NEXT_ROUND/SIDE_BRANCH）
- `docs/CLOSEOUT-MANUAL.md`
- `docs/branches/REFERENCE-INDEX.md`

## 8. 本轮管理报告

- `reports/rounds/SOLO-20261114-05-MANAGEMENT.md`
- `reports/rounds/SOLO-20261114-05-MANAGEMENT.json`
- `reports/rounds/SOLO-20261114-06-REPO-AUDIT.md`
- `reports/rounds/SOLO-20261114-06-REPO-AUDIT.json`
- `reports/rounds/SOLO-20261114-06-NEXT-STEP.md`
- `reports/rounds/SOLO-STAMP-COLLECTION.json`
- `reports/rounds/SOLO-STAMP-COLLECTION.md`
- `reports/rounds/SOLO-STAMP-VERIFY.md`


## 9. 总参谋部（SOLO-09）

13 条 SOLO 已全部进入总参谋部索引，THINK ID 为 `THINK-20261114-01..13`：

- 分类：9 primary + 4 secondary + 0 none。
- 标戳：13 个 `.staff-thinking.json`（1 in-place compare + 12 mirror）。
- 评估：10 维/50 分；A 9、B 4、C/D 0；平均 42.0；暂定 talentCandidate 8。
- 性质：**first-pass**；不是最终人才结论，下一轮再做维度/人才分析。
- `staffThinkingId` / `staffClass` / `staffGrade` / `staffScore` / `staffTalentCandidate` 已回写本 registry。
- 证据：`reports/general-staff/THINKING-ROUNDS.*`、`ROUND-EVALUATIONS.*`、`ROUND-EVALUATION-TEMPLATE.json`。
- 说明：SOLO-09/10 是 meta 轮，已登记但**不在 13 条 staff 索引/评估**内；stamp 为 mirror，待宿主复制。

## 10. 总参谋部引用

- `docs/general-staff/GENERAL-STAFF.md`
- `reports/general-staff/THINKING-ROUNDS.json` / `.md`
- `reports/general-staff/ROUND-EVALUATION-TEMPLATE.json`
- `reports/general-staff/ROUND-EVALUATIONS.json` / `.md`
