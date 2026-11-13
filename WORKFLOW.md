# WORKFLOW — 工作流组规范（canonical）

> 版本：v1.2 ｜ 更新：2026-11-11
> 定位：一个**以文档为唯一交互源**的多智能体工作流。主会话只做委派、收账、拍板，以及流程编排/统一提交/关停；完整职责见 `roles/MAIN.md`。
> 执行体：opencode 会话中的 DeepSeek-V4.1-Flash 智能体（PMO / TDO / QA；安全关键特化 run 可另设 SAFETY）。
> 实例目录：`runs/<run-id>/`；模板：`templates/`；角色手册：`roles/`；工具：`scripts/wf.py`、`scripts/issues.py`。

## 0. 规范层级与冲突裁决

> 权威链（从高到低）：用户当轮指令 > `WORKFLOW.md`（canonical） > `roles/*.md` > `templates/**` > `SPEC.md`（只能加严，不得放宽 §1 四条硬约束） > `DESIGN.md` / `EVOLUTION.md` / `WORKFLOW-TAGS.md` / `EXAMPLE.md`（非规范）。

- 任一文档与更高层规则冲突时，以更高层为准。
- `SPEC.md` 只能增加更严格的门禁、证据或路径限制，不得减损上层规则；尤其不得覆盖 §4.1 明列的不可覆盖约束（文档即接口、单一写者、锁协议、分歧不落地）。
- `DESIGN.md` / `EVOLUTION.md` / `WORKFLOW-TAGS.md` / `EXAMPLE.md` 只提供理由、索引或示例，不产生新规则；与上层冲突时上层优先。
- 同层冲突且无法按适用范围判定时，停止执行并升级主会话裁决。

---

## 1. 总原则

1. **文档即接口**：智能体之间、智能体与主会话之间，只通过 run 目录四件套交接；会话里不传正文、不复述文档。
2. **单一写者**：每个文档同一时刻只有一个角色可写（见 §4 契约表）。写别人文档 = 事故。
3. **主会话盲读**：主会话不看 TDO 的 STATUS、不看 QA 的 ISSUES 正文；只读 PMO 维护的 `PROJECT.md` §6 上报区，然后写 `DECISIONS.md`。
4. **分歧不落地**：任何执行体遇到需要取舍的分歧，不得自行选择后"顺手做掉"，必须写进文档升级，由主会话在 `DECISIONS.md` 拍板。
5. **进度逐条提交**：STATUS 写入期间加锁，一次追加一条，一条一提交；保证多智能体并发下进度可审计、可回滚。
6. **证据可复现**：每条进度必须带可复现证据（命令、文件路径、摘要数字、hash 之一）。

## 2. 编制与角色

| 角色           | 数量               | 一句话职责                                                              | 只读                                                 | 只写                                                          |
| -------------- | ------------------ | ----------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------- |
| 主会话（MAIN） | 1 人               | 立项/定编制/发委派/收回执/拍板/状态编排/统一提交/关停                   | 流程读 `PROJECT §6 + DECISIONS`                      | `DECISIONS.md`；S0 bootstrap 窗口可写 PROJECT §0 元信息与 §1 G1 目标/终止判据；经 `wf.py state/new-round` 动状态字段 |
| PMO            | 1                  | 计划、分任务、收轮汇总、向主会话上报                                    | PROJECT、DECISIONS、STATUS、ISSUES                   | `PROJECT.md`（S0 bootstrap 后唯一写者）                       |
| TDO            | N（1–5，主会话定） | 按工作流分片执行、写进度                                                | PROJECT §4、当轮 STATUS、DECISIONS                   | 产出物、当轮 `STATUS-Round-n.md`                              |
| QA             | 1                  | 独立核查 STATUS 与产出物，登记问题/风险/变更                            | 当轮 STATUS、PROJECT §1/§3/§4、产出物、上一轮 ISSUES | `ISSUES.xlsx`（当轮新增行）                                   |
| SAFETY         | 0 或 1             | **仅安全关键特化 run**：逐条审核门控 FAIL 的 action，不做执行/计划/核查 | 门控 action/gate/证据、PROJECT §1/§2/§4、DECISIONS   | `safety/reviews/ACT-*.json`（只能经 `hdrive_gate.py review`） |

编制默认：`PMO×1 + TDO×N + QA×1`。N 由主会话决定并记录在 `DECISIONS.md`。启用安全门控的 run 另加 `SAFETY×1`。

> **不设游离角色**：本工作流不设常设领域角色或独立办公室式结构（术语口径见 §11 术语与用字）；游离项一律按 §3.1 阶段 S4、§6、§7 的**收口规则**处理，不新建常设角色或游离台账。
> **安全关键 run 的唯一例外**：若特化 `SPEC.md` 明示启用门控执行器（如 `scripts/hdrive_gate.py`），主会话须用**独立会话**单独委派 `SAFETY×1`。该角色是任务级独立复核/双人控制位，只对 FAIL action 逐条签字，不是常设领域角色，不写四件套，也不得与 TDO/QA/人工批准人同身份。

### 2.1 TDO 数量决策表（主会话用）

| 情况                                    | N                    | 理由                                 |
| --------------------------------------- | -------------------- | ------------------------------------ |
| 任务无法切成互不触碰文件的独立片        | 1                    | 共享文件并发写会互相覆盖；串行更便宜 |
| 2–4 条独立工作流（不同产出物/不同目录） | = 工作流数           | 各自产出物互斥，可并行               |
| 工作流 ≥5 条但产出物有交叠              | ≤4，合并交叠项       | 锁与合并成本随 N 上升                |
| 上一轮严重度 S1 阻塞多、返工多          | 上轮 N − 1（最低 1） | 先降并发、稳住质量                   |
| 探索型/信息不全                         | 2                    | 一路探路、一路验证，避免全押一个假设 |

> 每轮结束主会话**重新拍一次 N**，写进 `DECISIONS.md` 的编制变更时间线。

## 3. 一轮的完整流程（状态机）

> 术语约定：S0–S5 表示流程阶段；S1–S4 表示 ISSUES 严重度，凡指严重度必须写“严重度 Sx”，单写“Sx”默认指阶段。

```text
S0 主会话开局
   │  wf.py new-run（复制四件套）→ MAIN 仅 bootstrap 填 PROJECT §0 元信息与 §1 G1 目标/终止判据；DECISIONS D-001 编制
   ▼
S1 PMO 计划        [PROJECT: pmo-plan → plan-ready]
   │  写 PROJECT §1–§5（目标判据/范围/指标/分任务/编制建议）
   │  ✗ 不写 STATUS、不写 ISSUES、不执行任务
   ▼  回执（≤8 行）→ 主会话不读 PROJECT 正文
S2 TDO 执行        [STATUS: tdo-pending → tdo-in-progress → qa-pending]
   │  主会话按 N 发 TDO-BRIEF；wf.py new-round 已备好当轮 STATUS
   │  每个 TDO：lock → 追加 1 条进度 → commit → unlock（可循环直到分片完成）
   │  ✗ 不改 PROJECT、不改 ISSUES、不替主会话拍板
   │  ┌─ 安全关键 run 的“阶段 S2”内门控子流程（不新增 state）
   │  │  TDO propose action → hdrive_gate.py gate
   │  │  ├─ PASS → 进入执行队列
   │  │  └─ FAIL → SAFETY 逐条 review
   │  │       ├─ reject → 退出队列（新 action 才可重提）
   │  │       └─ approve → red 再加 human-approve → run（一次一个）
   │  └─ 未审 FAIL = 0 且 red 未批 = 0，TDO 才能收尾
   ▼  主会话收齐 N 个回执 → wf.py state <run> STATUS qa-pending --by main
S3 QA 核查         [STATUS: qa-pending → qa-done]
   │  QA 读 STATUS + PROJECT 验收判据 + 产出物；逐条核对
   │  问题/风险/变更写入 ISSUES.xlsx（含严重度、是否需主会话决策）
   │  ✗ 不修产出物（只报不改）、不写 STATUS 进度条目
   ▼
S4 PMO 收轮        [PROJECT: plan-ready → waiting-main]
   │  PMO 读 STATUS + ISSUES，更新 PROJECT §3 指标/§4 分任务状态/§5 轮次结论
   │  待办去向核对：遍历 PROJECT §6 待办与 ISSUES 残余项，逐条给 owner/去向或升级；
   │  无主/无去向项不得进入 waiting-main
   │  写 §6 上报区：结论、待拍板选项（A/B + 建议）、下轮编制建议、风险
   ▼
S5 主会话拍板      [PROJECT: waiting-main → 下一轮 pmo-plan 或 closed]
   │  主会话读 PROJECT §6 → 写 DECISIONS（本轮决策 + 裁决 + 新编制 N'）
   │  ├─ 继续：wf.py new-round <run> → 回到阶段 S1
   │  └─ 终止：DECISIONS 记终止条目 → PROJECT: closed → 留档
   ▼
（循环，直到达成成功判据或确认终止）
```

### 3.1 各段完成定义（DoD）

| 阶段 | 完成定义                                                                                                                                 | 谁来确认                                |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| 阶段 S1 | PROJECT §1–§5 无占位符，§6 有"计划就绪"摘要，state=plan-ready                                                                            | PMO 自检 + `wf.py doctor`               |
| 阶段 S2 | 当轮 STATUS 每条分片都有"完成/阻塞"结论；阻塞项有 ID；state=qa-pending；若启用安全门控，则 `safety_pending=0` 且无未批 red 执行          | TDO 自检 + SAFETY 账本 + 主会话收齐回执 |
| 阶段 S3 | 每个未通过项都有 ISSUES 行；严重度 S1 行标记"需主会话=是"                                                                                       | QA 自检 + `doctor`                      |
| 阶段 S4 | §3"当前"列已更新；§4 状态已更新；待办去向核对完成（`PROJECT §6` 无未标注 owner/去向的待办）；§6 非空且给出选项与建议；state=waiting-main | PMO 自检 + `doctor`                     |
| 阶段 S5 | 每条待拍板都有 D-xxx；编制变更时间线已更新                                                                                               | 主会话                                  |

### 3.2 回执规范（唯一会话交互）

每个被委派智能体完成后，**只回执以下 8 行以内结构**，不贴正文、不贴 diff、不贴日志：

```text
[role] PMO|TDO|QA|SAFETY
[run]  <run-id>
[round] N
[state] 我去写的文档 → 新 state（如 PROJECT → plan-ready）
[summary] 一句话结论
[evidence] 关键证据路径/命令 1–2 条
[blockers] 有/无（有则给 ISSUES 或 STATUS 行的 ID）
[ask] 需要主会话拍板：有/无
```

## 4. 文档契约（唯一交互源）

### 4.0 状态迁移权（唯一执行者）

> 状态字段是流程推进操作，不算“写别人文档”；非本表执行者不得迁移状态。内容写权与状态迁移权分离。

| 迁移                                   | 唯一执行者        | 触发                        | 命令/动作                          |
| -------------------------------------- | ----------------- | --------------------------- | ---------------------------------- |
| （新建）→ `PROJECT:pmo-plan`           | 主会话            | 立项                        | `wf.py new-run`                    |
| `PROJECT:pmo-plan → plan-ready`        | PMO               | §1–§5 完成、doctor 无 ERROR | `wf.py state <run> PROJECT plan-ready --by pmo` |
| `STATUS:tdo-pending → tdo-in-progress` | TDO（首条持锁者） | 第一条进度                  | `wf.py append-status`              |
| `STATUS:tdo-in-progress → qa-pending`  | 主会话            | 收齐当轮 TDO 回执           | `wf.py state <run> STATUS qa-pending --by main` |
| `STATUS:qa-pending → qa-done`          | QA                | 核查完成、ISSUES 已登记     | `wf.py state <run> STATUS qa-done --by qa` |
| `PROJECT:plan-ready → waiting-main`    | PMO               | 阶段 S4 收轮、含待办去向核对 | `wf.py state <run> PROJECT waiting-main --by pmo` |
| `PROJECT:waiting-main → pmo-plan`      | 主会话            | 开下一轮                    | `wf.py new-round`                  |
| `PROJECT:waiting-main → closed`        | 主会话            | 达成/终止且关闭收口核对通过 | `wf.py state <run> PROJECT closed --by main` |
| `DECISIONS:open → closed`              | 主会话            | run 关闭时（可选）          | `wf.py state <run> DECISIONS closed --by main` |
| `STATUS:qa-done → closed`              | 主会话            | run 关闭时（可选）          | `wf.py state <run> STATUS closed --by main` |

| 文档                | 写者（唯一）                                                                                                                             | 其他角色         | 状态值                                                       | 关键结构                                            |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------ | --------------------------------------------------- |
| `PROJECT.md`        | PMO（S0 bootstrap 例外见下）                                                                                                            | 全员只读；MAIN 仅可在 bootstrap 窗口写 §0/§1-G1 | `pmo-plan` / `plan-ready` / `waiting-main` / `closed`        | §1 目标判据、§3 指标、§4 分任务、§5 轮次、§6 上报区 |
| `DECISIONS.md`      | 主会话                                                                                                                                   | 全员只读         | `open` / `closed`                                            | §1 决策账本（D-xxx）、§2 编制变更时间线             |
| `STATUS-Round-n.md` | TDO（持锁者）                                                                                                                            | 主会话按 §3 不读 | `tdo-pending` / `tdo-in-progress` / `qa-pending` / `qa-done` / `closed` | 进度条目表、阻塞表、交接给 QA 区                    |
| `ISSUES.xlsx`       | QA 新增行；仅当 `DECISIONS.md` 明确授权时，PMO 可更新既有行的「状态」「关联决策ID」（不改其他列、不删行；关闭/挂起必须有可追溯证据落点） | PMO/QA/SAFETY/TDO 只读；MAIN 仅读 `doctor` 摘要，禁读正文 | 行级：新建/处理中/待主会话/已决议/已关闭/挂起                | `账本` / `汇总` / `说明` 三个 sheet                 |

- **PROJECT S0 bootstrap 例外（单点授权）**：`wf.py new-run` 后至 PMO 首次接手阶段 S1 前，MAIN 只可填写 `PROJECT.md §0` 元信息与 `§1` 的 G1 目标/终止判据；PMO 接管后（最迟 `plan-ready`）窗口立即关闭，MAIN 不得再写 `PROJECT.md`。除此之外，`PROJECT.md` 写者仍只有 PMO。
- 每份 md 头部是 `<!-- wf-doc ... -->` 元信息块，字段：`run` / `round` / `doc` / `owner` / `state` / `updated`。
- 状态迁移只用 `python3 scripts/wf.py state <run> <doc> <state> --by <角色>`，不要手改状态行。
- 四件套只增不删：作废用状态列/取代关系表达，不删历史行。
- **安全门控账本不是第五份四件套**：`safety/actions|gates|reviews|human-approvals|executions/` 由门控/执行器写入；SAFETY 只通过 `hdrive_gate.py review` 新增 `reviews/ACT-*.json`，不得手改其他账本。安全关键 run 的 SPEC 可规定主会话读取 `hdrive_gate.py status` 摘要，作为“主会话盲读”的显式例外。

## 4.1 run 特化（SPEC.md 与 `--template`）

- 每次烧 token 的 run 建议按"目录范围"特化：一个写权限目录/文件边界一份 SPEC，实例化时用
  `python3 scripts/wf.py new-run <run-id> --template templates/specialized/<name> ...`
- 特化模板目录至少含 `SPEC.md`（分区表 + 全内容覆盖要求 + 证据格式 + 禁止项 + DoD）；`PROJECT.md` 推荐但可选，缺省时回退通用模板；
  `DECISIONS.md` 可预置待决清单；缺的 `STATUS-Round-n.md` / `ISSUES.xlsx` 自动回退通用模板。
- 委派消息会自动带上"先读 `runs/<id>/SPEC.md`（特化规则优先于通用手册）"；SPEC 只能按 §0 权威链加严，**不得放宽 §1 四条硬约束**，尤其不覆盖：文档即接口、单一写者、锁协议、分歧不落地。
- 模板写法与分区原则见 `templates/specialized/README.md`。

## 4.2 原子轮型契约（冻结层）

> 原子轮型是标准工作流的**单轮最小接口**：输入、必产、强制门、预算、完成定义、交接。它们不是 run 模板，不能直接 `--template`。

- 冻结位置：`templates/contracts/`；当前版本`atomic-contract-set@1.0.0`，基础母版`workflow-group-base@1.2.0`。
- 七个原子轮型：`strategy / research / diff / architecture / optimize / verify / audit`。
- 共同计划门：`templates/contracts/_shared/PLAN-GATE.md` 7/7；收轮判词：`templates/contracts/_shared/VERDICT.md`。
- 领域 `SPEC.md` §0 必须显式引用：
  ```text
  contracts: research@1.0.0, verify@1.0.0
  ```
- `ROUND-PLAN.md` 必须声明本轮唯一 `contract: <type>@<version>`；`produces/gate/budget/NOT-DOING` 四行齐全。
- 冻结文件只增不改：任何变更必须升 `templates/contracts/VERSION`、更新 `LOCK.json`，并跑
  `python3 scripts/contract_lock.py check` rc=0。协议见 `templates/contracts/BASE-MASTER.md`。

## 4.3 基准模板（baseline，复合类型重点参考）

> **类定义**：基准模板是复合类型的稳定参考模板，不是可直接实例化的 run 模板。它把多个原子轮型组合成默认管线，并规定主攻方向、特点、强制证据、领域参考和成熟度。
> **使用方式**：新建/复用领域特化前先查 `templates/baseline/REGISTRY.md`；匹配时在 `SPEC.md` §0 写
> `baseline: composite/<name>@1.0.0` 与对应 `contracts:`。真正 `wf.py new-run --template` 仍使用 `templates/specialized/<name>`。

| 基准模板                     | M   | 主攻方向                                  | 关键特点                                                           |
| ---------------------------- | --- | ----------------------------------------- | ------------------------------------------------------------------ |
| `fix-wave`                   | M3  | 票源/缺陷清单 → 验证→修订→复跑→门禁化     | 每票先红后绿；一 WS 一域；票源去向闭合                             |
| `refactor-decompose`         | M2  | 先 100% 归属/冻结基线，再分区行为不变重整 | 唯一归属、old→new 映射、回滚、语义不变                             |
| `ops-hardening`              | M3  | 分发/同步/调度/入口可靠性加固             | 恢复性演练、篡改/缺失反例、多仓留 diff                             |
| `safe-cleanup`               | M3  | 真实文件系统 move-only 整理               | action digest、逐条 SAFETY、人工批准、失败即停、POSIX/Windows 后端 |
| `knowledge-pipeline`         | M3  | 来源入库→检索消费→方法实战回写            | 全内容处置、检索指标、真实查询日志、门禁反例                       |
| `two-plane-orchestration`    | M3  | workflow-group 控制面 + OpenRig 执行面    | 双权威、隔离 home/port、分支 QA+join+有界回边、先归档再 teardown   |
| `postmortem-meta-governance` | M2  | 复盘/角色/规则/模板的元治理回写           | 数据表、失败模式、≥3 处回写、红队/影子验证                         |
| `product-redesign-live`      | M2  | 反目标→多 seat 设计→staging→live/回滚     | 反目标先行、独立 QA、finalize 快照/回滚/通知                       |
| `hypothesis-analysis`        | M3  | 未知项假设矩阵 + 置信度 + 可证伪实验      | 事实/推断分离、分支 QA+join、源数据只读                            |

- 每个基准模板的主攻方向、特点、默认管线、证据和领域参考见 `templates/baseline/<name>/BASELINE.md`；
  注册表见 `templates/baseline/REGISTRY.md` / `REGISTRY.json`。
- 2026-10-23：原 `issue-sync` 复合类型已降级为 `templates/specialized/issue-sync/` adapter（canonical 零引用）；baseline 由 10 项收敛为 9 项，adapter 自身按 atomic 组合（research/verify/audit）实例化。
- 现有 26 个领域特化的 baseline/contracts 映射见 `templates/specialized/BASELINE-MAP.md`；新增模板必须补行，旧 run 的 SPEC 不追溯改写。
- `wf.py new-run --template` 会拒绝直接使用 `templates/contracts/*` 与 `templates/baseline/*`，避免把“冻结接口/参考模板”误当“run 模板”。
- 基准模板自身变更必须升级 `templates/baseline/VERSION` 并同步注册表；领域 run 引用的是固定版本，不随目录最新内容漂移。

## 5. 锁与提交协议（STATUS 专用）

- 锁对象：`runs/<run-id>/.locks/status.lock`（目录形式的原子锁）。
- 获取：`python3 scripts/wf.py lock <run-id> --agent <name>`；释放：`... unlock <run-id>`。
- 一条进度 = 一次锁周期：`lock → 追加 1 条 → （--commit）git add/commit → unlock`。
- 推荐直接用一条命令完成整个周期：
  `python3 scripts/wf.py append-status <run-id> --agent tdo-a1 --ws WS-2 --action "..." --evidence "..." [--state 阻塞 --blocker "..."] [--also 产出物路径]`
- **`--also` 只能指向 git 会跟踪的路径**：若指向被 `.gitignore` 忽略的文件（如 `*.log`、`burner/` 运行态、`logs/**`），`git add --` 一步就会失败，连带**整条进度提交失败**（进度行已落盘但未入库，易被误判为"已提交"）。变通：产物日志只留盘 + 在报告内联关键行，或改扩展名/调 `.gitignore`。（出处：`runs/signaldeck-runtime-20261014/STATUS-Round-1.md` WS-2 薄弱点 3）
- **`--also` 用途边界**：TDO 的 `append-status --also` 只用于本轮 `STATUS-Round-n.md` 与**本 run 产物**（`runs/<run-id>/**`）；**核心规范/角色/模板文件**（`WORKFLOW.md`、`DESIGN.md`、`roles/**`、`templates/**`、入口 `AGENTS.md`/`README.md`）**不得**进入 TDO `--also`，一律由主会话 S5 按明确 pathspec 统一提交（避免 TDO 阶段提交母版文件）。（出处：`runs/master-adoption-20261015` P-001）
- 超时接管：锁超过 TTL（默认 900 秒）视为过期，`lock --steal` 可接管，且必须在 STATUS 追加一条 `steal` 说明、在 ISSUES 登记一条严重度 S3 风险。
- 提交信息约定：`wf(<run-id>): r<N> <WS> <动作摘要>`。
- 冲突处理：拿不到锁就退避重试（默认 3 次，指数退避）；仍失败就写回执报告"锁竞争"，不要硬改文件。

## 6. 分歧、风险与升级

- **必须升级主会话**（写进 PROJECT §6 待拍板，并同步一条 ISSUES 行）：
  - 影响目标/范围/终止判据的解释；
  - 两个智能体结论相反且证据都成立；
  - 需要改产出物形态、成本或时间的取舍；
  - 严重度 S1 问题；任何"要不要继续/改编制"的判断；
  - 安全事件：绕过门控执行、批量/自审/代签、action 摘要被改、未审批 red 被执行、范围越界。
- **不需要升级**（按手册自行处置，但要留痕）：任务内实现细节、命名、局部方案；留痕方式 = STATUS 进度条目或 ISSUES 的严重度 S3/S4 行。
- **承接规则**：任何跨轮/跨 run 承接项必须写 owner + 去向 + 最晚复核轮；未立项的“下一 run”不算有效去向；无去向项按本节升级主会话。
- 升级格式：`选项 A` / `选项 B` / `PMO 建议` / `最晚决策时点`；主会话只在这四栏上拍。
- 拍板结果写 `DECISIONS.md`；PMO 在下一轮阶段 S1 把决策映射回 PROJECT §2/§4。

## 7. 轮次与退出

- 轮次从 1 开始，`STATUS-Round-n.md` 一轮一个文件；`DECISIONS.md` 按轮次记账。
- **达成**：PROJECT §1 全部成功判据满足，且 ISSUES 无 open 的严重度 S1/S2，且已知游离项全部有 owner/去向或主会话在 `DECISIONS.md` 显式接受。安全关键 run 还必须 `hdrive_gate.py status --json` 的 `safety_pending=0`、无未批 red 执行、无绕过门控事件，且审计报告/隔离区清单/保留期齐全。
- **终止**（满足任一，由主会话在 DECISIONS 记录后关闭）：
  - 连续 2 轮无可验证进展；或
  - PMO 上报 ROI 不足 / 目标已无价值；或
  - 主会话或用户主动叫停。
- **关闭收口规则**：run `closed` 前，所有已知游离项必须有 owner + 去向，或由主会话在 `DECISIONS.md` 显式接受；否则 PMO 不得置 `waiting-main`，主会话不得置 `closed`。
- 关闭动作：主会话记 D-xxx（达成/终止 + 资产去向）→ 关闭收口核对通过 → 运行 `python3 scripts/wf_close_lint.py --run <run-id>`（ERROR 必须为 0）→ 仅主会话执行 `wf.py state <run> PROJECT closed --by main` → 保留 run 目录作为过程证据。
- 历史 run 的关闭语义违规由 `reports/close-lint-20261111.txt` 登记为历史缺口，不追溯改写；新 run 一律走上面的关闭门。

## 8. 常用命令

```bash
cd workflow-group

# 开局（复制四件套 + 填目标 + 建锁目录）
python3 scripts/wf.py new-run kb-search-eval --goal "..." --tdo 2

# 主会话生成委派消息（填空即用，直接贴给 opencode）
python3 scripts/wf.py brief --role pmo --run kb-search-eval
python3 scripts/wf.py brief --role tdo --run kb-search-eval --agent tdo-a1
python3 scripts/wf.py brief --role qa  --run kb-search-eval

# TDO 追加一条进度（自动加锁/提交/解锁）
python3 scripts/wf.py append-status kb-search-eval \
  --agent tdo-a1 --ws WS-1 --action "完成检索脚本骨架" \
  --evidence "workflow-group/runs/kb-search-eval/out/search.mjs (sha256:...)" --also out/search.mjs

# 状态迁移 / 新轮 / 体检
python3 scripts/wf.py state kb-search-eval STATUS qa-pending --by main
python3 scripts/wf.py new-round kb-search-eval
python3 scripts/wf.py doctor kb-search-eval

# ISSUES 表格读写
python3 scripts/issues.py add  runs/kb-search-eval/ISSUES.xlsx --round 1 --type 风险 \
  --title "..." --severity S2 --owner PMO --source "STATUS-Round-1" --action "..." --need-decision yes
python3 scripts/issues.py list runs/kb-search-eval/ISSUES.xlsx --open-only
python3 scripts/issues.py close runs/kb-search-eval/ISSUES.xlsx R-002 --decision D-004
```

## 9. opencode 直连（可选自动化，仅 opencode 1.x）

> 本节的 `serve` / `delegate` 是"主会话纯委派"的可选自动化实现；不用它时，`brief` + 人工粘贴同样成立。
> 实测（2026-10-12）：PMO 157.8s / $0.00025，TDO 168.5s / $0.0006，QA 114.5s / $0.00049（模型 `opencode-go/deepseek-v4.1-flash`，第二次起 cache.read 命中 5 万级）。

```bash
python3 scripts/wf.py serve start        # 起无头服务（默认 cwd=workflow-group，仅绑 127.0.0.1）
python3 scripts/wf.py serve status
python3 scripts/wf.py delegate <run> --role pmo --timeout 900            # 自动发 BRIEF + 收回执 + 记账
python3 scripts/wf.py delegate <run> --role tdo --name tdo-a1
python3 scripts/wf.py delegate <run> --role qa
python3 scripts/wf.py delegate <run> --role pmo --dry-run                # 只看将发送的 BRIEF
python3 scripts/wf.py serve stop
```

规则：

1. **通道与版本守卫**：仅 opencode **1.x** 支持本节的 v1 同步 API（`POST /session` + `POST /session/{id}/message`，阻塞到答完）。**本机实测 opencode v2.0.32：v1 端点已移除，`POST /session` 返回 405**；`serve_start` 在拼 `serve --pure` 之前先探测 `opencode --version`，检测到 2.x 或无法识别版本时立即 **rc=1** 并给出一行可执行提示（改用 `opencode run` headless，或用 `OPENCODE_BIN=/path/to/opencode-1.x` 指定兼容二进制），不会启动悬挂进程。`delegate`/`squad` 默认自动拉起服务，因此同样在此失败；显式 `--server` 指向已运行的 v1 服务时保留原 v1 路径。本仓 `scripts/` **没有内置 v2 CLI adapter**：v2 下自动委派需外部 adapter（插件线 `opencode_delegate.py`）或直接 `opencode run`。`--dry-run` 不经过 HTTP，仍可离线预览 BRIEF。v2 的 `POST /api/session/{id}/prompt` 在无头服务下只受理不执行（`wait` 返回 503），同样不要用。
2. **状态守卫**：`delegate` 会核对状态机——PMO 需 PROJECT=`pmo-plan|plan-ready`；TDO 需 PROJECT=`plan-ready` 且 STATUS=`tdo-pending|tdo-in-progress`；QA 需 STATUS=`qa-pending`；不匹配直接拒绝（`--force` 可绕过，不推荐）。
3. **模型与 agent**：默认 `opencode-go/deepseek-v4.1-flash` + opencode 内置 agent `minimal`（无编排注入）。换模型用 `--model providerID/modelID`，换 agent 用 `--oc-agent`。
4. **记账**：每次委派追加 `runs/<id>/DELEGATIONS.md`（时间/轮次/角色/session/cost/tokens），原始回执存 `runs/<id>/delegations/*.md`；轮末汇总进 DECISIONS。
5. **服务作用域**：session 属于 server 启动目录所在项目；默认 cwd=`workflow-group`，所以相对路径 `runs/<id>/...` 直接可用。不要用 `--dir` 指到别的项目而不改 BRIEF。
6. **安全**：默认无密码、仅 127.0.0.1。要设密码就 `export OPENCODE_SERVER_PASSWORD=...`，脚本会自动带 Basic Auth。
7. **权限坑**：opencode 配置里 `git push = ask`，无人值守会卡住。把 push/发布类动作留给主会话；或在建 session 时传 `permission` 白名单（当前 `delegate` 未暴露，需要时再扩展）。
8. **会话留存**：`delegate` 不自动删 session（审计用）；确认无用后 `opencode session delete <sid>`。

### 9.1 真实项目 run（写权限与提交）

- `PROJECT.md` §0 必须填「项目根」「写权限白名单」；TDO 只改白名单内路径，越界按事故记 ISSUES。
- 项目仓**只改不提交、不 push**；每轮结束由主会话统一提交（只 add 明确路径，绝不 `git add -A`，因为项目仓常混有他人未提交改动）：

```bash
python3 scripts/wf.py commit --repo /path/to/project-repo \
  --run <run-id> --round 2 --message "修复 R1 扫描问题" \
  -- 10-signaldeck/src/frontend/src 10-signaldeck/tests
```

- 高并行扇出（每片一个 WS，互不重叠）：

```bash
python3 scripts/wf.py squad <run-id> \
  --agents 'tdo-a1:WS-1,tdo-a2:WS-2,tdo-a3:WS-3,tdo-a4:WS-4' \
  --timeout 3600 --jobs 4
```

- 烧额度记账：`python3 scripts/wf.py ledger <run-id>`（按角色统计次数/cost/tokens/耗时）。

### 9.2 烧额度调度器（burner）的三条硬约定（2026-10-14）

> 依据 `burner/burner.log` 与各 run 记录；实现见 `burner/run_queue.py`，完整映射见 `runs/burn-postmortem-20261014/reports/ws2-changes.md`。

1. **幂等**：启动一个 pack 前先查 `runs/<id>/DONE` 或 `BLOCKED`，存在即 `SKIP`；要重跑必须先删该文件。（反例：kb-debt-20261013 已 closed 仍被重跑，花 63664 tokens 仅写 DONE。）
2. **可见性**：单条 send 期间按 `heartbeat_sec`（默认 300s）记 `HEARTBEAT`；`send_timeout_sec` 默认收敛到 7200s。（反例：单条 send 跑 98 分钟零日志，无法区分在跑/卡死。）
3. **记账口径**：预算/复盘以「官方余额差」为准，不能只看 session `cost`；逐 pack 记 `余额 ¥a → ¥b（Δ¥c）`。（反例：P1–P4 cost 合计≈$0.0034，余额却降 ¥4.89。）

## 10. 反模式清单（见到就停）

1. 主会话读了 STATUS / ISSUES 正文 → 越权，破坏"文档即接口"的职责分离。
2. TDO 没领锁就写 STATUS → 并发覆盖，进度丢失。
3. 智能体"顺手把分歧做掉" → 事后返工且无法追责。
4. 把会话结论当交付 → 必须落文档，否则视为未完成。
5. 一次提交一大坨进度 → 逐条提交失败，回滚粒度丢失。
6. 在 `templates/` 上直接改 → 模板污染，应复制到 `runs/<id>/` 再改。
7. 把 run 目录当正式 KB 正文 → 本目录不参与 KB 校验与正式检索，不要混。
8. 并行 TDO 抢同一片 WS → PMO 拆片必须按文件/目录边界；squad 强制每个执行体绑定唯一 WS。
9. 在项目仓 `git add -A` 或 push → 会裹进他人改动；提交只用 `wf.py commit` 的明确 pathspec。
10. 重跑已完成的 run（已有 `DONE` / PROJECT `closed` 还拉起）→ 白烧额度；先查 `DONE`，没有把握就别重跑。
11. `append-status --also` 给被 `.gitignore` 忽略的文件（`*.log`/`logs/**`/`burner/`）→ 整条进度提交失败，进度行落盘却没入库。
12. 无主/无去向的待办只写“下一 run/人工”就关闭 run → 关掉了，但没有承接目标，问题丢失。
13. 把严重度 S1/S2 问题转入任何游离台账绕过 ISSUES → 规避严重度门禁，问题不可追溯。

---

## 11. 术语与用字

> 本表是工作流规范用字的唯一来源；新增/修改的规范、角色、模板文字一律以本表为准。
> 注：S0–S5 表示流程阶段；S1–S4 表示 ISSUES 严重度，凡指严重度必须写“严重度 Sx”。
> `SO`、`Specialist Office`、`Specialist Officer`、`执行专员`、`领域专员`、`L1/L2/L3` 作为规范术语**已退役**，仅在历史材料中保留原文；退役术语不得出现在新增/修改的规范文字里。

| 规范用法                     | 含义                                                                                       | 退役/避免                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| **主会话（MAIN）**           | 唯一决策、编排、统一提交与关停者                                                           | 单独写 MAIN；主 Agent                                        |
| **角色**                     | PMO / TDO / QA；安全关键特化 run 可加任务级 SAFETY；主会话不算执行角色                     | 智能体堆叠                                                   |
| **游离项**                   | 收轮/关闭时无 WS 归属、无 owner、或无去向的已知事项                                        | 无主问题（可用作口语，不写规范）                             |
| **收口**                     | 为游离项确定 owner 与去向的动作                                                            | 收杂、兜底                                                   |
| **去向**                     | owner + 承接目标（WS / 后续 run / ISSUES / DECISIONS / 主会话接受 / 挂起）+ 最晚复核轮     | 只写“后续/人工”                                              |
| **承接**                     | 跨轮/跨 run 移交；必须带 owner、去向、最晚复核轮                                           | 遗留（须补去向）                                             |
| **状态迁移**                 | state 变化；唯一执行者见 §4.0                                                              | 状态推进、改状态                                             |
| **严重度**                   | S1 / S2 / S3 / S4                                                                          | 等级、L1–L3                                                  |
| **SAFETY**（独立安全审核员） | 仅在特化 SPEC 明示启用门控时存在的任务级独立复核位；逐条审 FAIL action，不执行、不写四件套 | 把 SAFETY 当常设 SO/领域专员；SAFETY 兼执行/计划             |
| **SO**（已退役）             | 仅历史材料；现行规范不设此角色/结构                                                        | Specialist Office / Specialist Officer / 执行专员 / 领域专员 |

> **退役术语 grep 边界（2026-10-15）**：退役术语字面（`SO`、`Specialist Office`、`Specialist Officer`、`执行专员`、`领域专员`、`L1/L2/L3`）**只在“退役/不设/历史”上下文允许出现**——即本表“退役/避免”列、历史 run 与旧报告、退役横幅，以及显式写明“已退役/不设/历史”的句子。上述字面仅作为**现行用法**出现（未带退役标注）才算违规；校验不做裸字面全局禁用。（出处：`runs/master-adoption-20261015` R-002）
