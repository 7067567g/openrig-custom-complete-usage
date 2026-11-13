# OpenRig 医护中心方案（v1.0.0）

> 状态：**方案文档，未实施**  
> 范围：只定义医护中心的架构、标戳、分诊、手册、异常档案和根因分析；本轮不改代码、不建 workflow、不创建 stamp、不执行任何收治动作。  
> 已废弃：**机动快速部队 / 定时 SHA 巡检 / 变更自动拉起**。工作区日志与变更管理优先使用成熟的 git + OpenRig registry + 收尾手册，不另造常驻巡检器。

---

## 0. 一句话

医护中心是 OpenRig 的**鲁棒性/坏数据清理/伤员收治中心**：

```text
发现问题 → 分诊 → 隔离现场 → 诊断 → 标戳 → 生成“不实施的改进建议补丁”
         → QA/MAIN 决策 → 治疗或归档 → 根因复盘
```

它不是监控器，不是自动修复器，也不是新的命令中心。它只在出现“伤员/坏数据/异常残骸”时介入，把不可控的残留变成**可检索、可审计、可决策**的档案。

---

## 1. 为什么不建机动快速部队

已评估的定时/触发式 SHA 巡检方案：

- 定时常驻后台轮询工作区；
- 检查文件 SHA 变更；
- 变更后自动拉起处理流程。

结论：**废弃**。原因：

1. git 自带 status/log/reflog/worktree/stash/tag；
2. OpenRig 已有 command center registry、queue/workflow 状态、solo/staff stamps；
3. 自建常驻轮询会引入新的后台进程、权限和误报成本；
4. 大多数“工作区变更”不是伤员，不需要自动收治；
5. 真正常见的坏数据是**局部异常**，更适合按需分诊，而不是持续扫描全库。

保留原则：

- 用 `git status` / `git log` / `git reflog` / `git worktree` 做变更审计；
- 用 `ROUND-REGISTRY.json` 查长运行任务；
- 用 `.solo-round.json` / `.staff-thinking.json` 检索单独轮和思考轮；
- 用 `CLOSEOUT-MANUAL` 处理停止收尾；
- 医护中心只处理“已经受伤/异常/无法自愈”的对象。

---

## 2. 医护中心定位

| 对象 | 职责 |
|---|---|
| **Command Center** | 登记长运行轮/主支、查冲突、看运行中任务 |
| **General Staff** | 思考类轮次索引、评估、维度/人才/咨询 |
| **Medical Center** | 坏数据/伤员/异常残骸的分诊、隔离、诊断、标戳、建议补丁、归档、根因分析 |
| **STOP-SWEEP / CLOSEOUT** | 正常停止/中途停止的冻结、盘点、三类分类 |
| **QA** | 独立验证治疗/补丁/恢复结果 |

边界：

- 医护中心不替代 QA，也不自动应用补丁；
- 医护中心不删除用户数据；
- 医护中心不接管正式轮/分支的验收结论；
- 医护中心不监听文件 SHA，不做常驻后台轮询。

---

## 3. 伤员定义

“伤员”是任何**已偏离健康状态、需要判断是否需要干预**的对象：

- 坏数据：损坏的 JSON/schema、重复/孤立缓存、失效的索引、错误的时间戳；
- 代码/分支伤员：无法合并、基线不明、dirty worktree、孤儿 worktree、冲突残留；
- 流程伤员：半完成 workflow、孤儿 qitem、卡死 seat、未关闭的 watchdog、未归档证据；
- 文档伤员：断链、过期版本、互相矛盾的 ledger/doc/report；
- 产物伤员：失败的测试、不可复现的构建、错误的 patch、无效的 snapshot；
- 认知伤员：错误结论、未经验证的“已完成”、被误标 PASS 的轮次；
- 环境伤员：端口/锁/权限/依赖/磁盘/服务异常；
- 不可救治：数据已不可恢复、模型能力不足、外部依赖永久缺失、成本不可接受。

---

## 4. 医护标戳系统

### 4.1 医护轮 ID

```text
MED-YYYYMMDD-NN
```

- 每次分诊/收治一个批次分配一个医护轮 ID；
- 一个医护轮可包含多个伤员（patient）；
- 伤员 ID：

```text
PAT-YYYYMMDD-NN
```

- 医护轮独立于 SOLO/THINK/正式 R 轮，不占用主链编号。

### 4.2 医护轮标戳文件

每个医护轮目录放：

```text
reports/medical-center/rounds/<MED-ID>/
  .medic-round.json
  INTAKE.md
  TRIAGE.json
  DIAGNOSIS.md
  PROPOSED-PATCH.diff
  TREATMENT.md
  OUTCOME.json
  RCA.md
```

`.medic-round.json` 草案字段：

```json
{
  "schema": "example-medic-round/v1",
  "medicId": "MED-YYYYMMDD-NN",
  "status": "INTAKE|TRIAGE|DIAGNOSIS|PATCH_PROPOSED|TREATED|ARCHIVED|UNRESOLVED|CLOSED",
  "owner": "<Lead/QA/MAIN>",
  "anchor": "R15",
  "rejoin": "R16",
  "patients": ["PAT-YYYYMMDD-01"],
  "triageSummary": {"green": 0, "yellow": 0, "red": 0, "black": 0},
  "patchPolicy": "PROPOSE_ONLY_NOT_APPLIED",
  "relatedRounds": [],
  "relatedBranches": [],
  "createdAt": "...",
  "updatedAt": "..."
}
```

### 4.3 伤员标戳

每个伤员有独立档案：

```text
reports/medical-center/patients/<PAT-ID>/
  .patient.json
  EVIDENCE.md
  SYMPTOMS.md
  TRIAGE.json
  PATCH-PROPOSAL.md
  RCA.md
  OUTCOME.md
```

`.patient.json` 字段：

- `patientId`
- `kind`：data/code/branch/process/doc/artifact/cognition/env/unrecoverable
- `severity`：green/yellow/red/black
- `symptoms`
- `evidenceRefs`
- `contagious`：是否可能污染其它轮/分支
- `reproducible`
- `rootCauseClass`：model/spec/tool/env/data/transient/unknown
- `proposedPatch`
- `patchApplied`：固定 `false`（v1）
- `outcome`：treated/archived/unresolved/closed
- `owner`
- `nextReviewAt`

### 4.4 医护检索

- 所有医护轮：`.medic-round.json`
- 所有伤员：`.patient.json`
- 统一 ID 前缀：`MED-` / `PAT-`
- 只读检索，不做全库自动扫描；由分诊输入指定范围。

---

## 5. 分诊等级

| 等级 | 含义 | 默认动作 |
|---|---|---|
| **GREEN** | 已知、可安全自愈/小修 | 记录症状 + 标准动作 + 复验 |
| **YELLOW** | 有局部损伤，需要诊断/建议补丁 | 隔离现场 + 提案 + QA 决策 |
| **RED** | 可能污染其它轮/分支/数据 | 立即隔离 + 禁止合并 + 根因分析 |
| **BLACK** | 不可救治/成本过高/外部永久缺失 | 归档 + 事故档案 + 明确不再重试 |

分诊不是最终诊断；24 小时内可升级/降级，必须写理由。

---

## 6. 标准动作（医护手册骨架）

未来标准手册分两本：

1. **赤脚手册**：一线快速处理，少术语、可复制命令；
2. **医护手册**：完整诊断/治疗/根因/归档规范。

### 6.1 一线动作

1. **STOP**：停止继续写入，保留现场；
2. **ISOLATE**：隔离分支/worktree/数据目录/端口；
3. **SNAPSHOT**：只读快照/哈希，不删除；
4. **TRIAGE**：green/yellow/red/black；
5. **DIAGNOSE**：最小复现、证据、影响面；
6. **TAG**：写 `.medic-round.json` / `.patient.json`；
7. **PROPOSE**：生成 `PROPOSED-PATCH.diff`，**不应用**；
8. **QA**：独立复核；
9. **TREAT / ARCHIVE / UNRESOLVED**：按决策执行；
10. **RCA**：写根因与预防。

### 6.2 禁止动作

- 不自动 `git reset --hard` / `clean -fd` / 删除分支 / 删除 worktree；
- 不自动应用补丁；
- 不读/提交原始截图、聊天正文、token、logcat 正文；
- 不把“已归档”写成“已修复”；
- 不把 RED/BLACK 伤员混入正常轮次；
- 不在没有快照/回滚路径时执行破坏性动作。

---

## 7. 不实施的改进建议补丁

医护中心 v1 只生成补丁建议，不应用。

补丁包：

```text
reports/medical-center/patients/<PAT-ID>/
  PROPOSED-PATCH.diff
  PATCH-META.json
  PATCH-REVIEW.md
```

`PATCH-META.json`：

- `patientId`
- `baseCommit`
- `patchKind`：code/data/config/doc/test
- `risk`
- `applyPolicy`: `PROPOSE_ONLY`
- `applyCommand`（仅建议，不执行）
- `rollback`
- `verification`
- `owner`
- `status`: `PROPOSED|APPROVED|REJECTED|SUPERSEDED`

应用补丁必须另开正式轮/修复分支，经过 QA 和 MAIN 批准，医护轮本身不直接改产品代码。

---

## 8. 异常档案与根因分析

### 8.1 异常档案

无法救治、反复出现、原因不明或影响较大的伤员，进入：

```text
reports/medical-center/incidents/<INCIDENT-ID>/
  INCIDENT.md
  TIMELINE.json
  EVIDENCE.md
  RCA.md
  OUTCOME.md
```

`OUTCOME` 只能是：

- `FIXED`
- `MITIGATED`
- `ARCHIVED`
- `UNRESOLVED`
- `WONTFIX`

### 8.2 根因分类

| 类 | 判断 |
|---|---|
| `model` | 模型能力/幻觉/推理失败；可复现且与输入相关 |
| `spec` | 需求/验收/契约模糊或矛盾 |
| `tool` | 工具/脚本/命令缺陷 |
| `env` | 环境、权限、网络、systemd、设备、资源 |
| `data` | 坏数据、schema、迁移、缓存、索引 |
| `concurrency` | 锁、竞态、重复、并发写 |
| `transient` | 偶发、不可复现、无系统模式 |
| `unknown` | 证据不足，必须标注 |

### 8.3 模型不行 vs 偶发

必须回答：

1. 是否可复现？同输入/同 seed/同环境；
2. 是否只发生一次？有无时间/资源/并发相关性；
3. 是否跨模型/跨 session 复现；
4. 是否由 prompt/上下文/工具结果触发；
5. 是否有明确反例和修复验证；
6. 是能力边界，还是流程没有给出足够约束。

结论只能是：

- `MODEL_LIMITATION`
- `PROCESS_GAP`
- `ENVIRONMENT_TRANSIENT`
- `DATA_CORRUPTION`
- `UNKNOWN`

并写适用边界，不把一次偶发上升为模型结论。

---

## 9. 医护轮 OpenRig 工作流形态

医护轮也是**单独轮**的一种，但使用自己的 stamp：

```text
MED-YYYYMMDD-NN
```

建议 workflow 步骤：

1. `intake`：收伤员、建 patient 清单、冻结现场；
2. `triage`：分诊 green/yellow/red/black；
3. `diagnose`：证据/复现/影响面；
4. `propose_patch`：生成不实施补丁；
5. `qa_review`：独立 QA；
6. `outcome`：治疗/归档/未解决；
7. `rca`：根因与预防；
8. `close`：更新医护台账，回 R16。

强制边界：

- 医护 workflow 不得直接修改产品代码；
- 只能写 `reports/medical-center/**` 和必要的只读证据；
- 补丁只能 `PROPOSE_ONLY`；
- QA 必须独立于提出补丁的人/seat；
- 回归点仍是 R16，不跳过。

---

## 10. 与现有体系的关系

| 体系 | 关系 |
|---|---|
| Command Center | 医护轮开始/结束时登记？不，医护轮属于单独轮；但若伤员涉及长运行轮，需更新 command center 状态/冲突键 |
| General Staff | 医护轮的思考过程可入 THINK 索引；但医护轮有自己的 MED 标戳 |
| SOLO registry | 医护轮可登记为 `staffClass=secondary` 或 `primary`，但必须带 medicId |
| 正式 30 轮 | 医护中心不改变 R16 结论；治疗补丁需另开正式修复轮 |
| STOP-SWEEP | 正常停止走 CLOSEOUT；医护中心处理停止后发现的伤员/坏数据 |
| SYNC-GUARD | 多文件夹漂移先由 SYNC-GUARD 分类；需要治疗的进入医护中心 |
| MIDRUN-INSERTION | 新需求不是伤员；插入走 INSERT-GUARD，医护不走插入队列 |

---

## 11. 分阶段落地（未来）

| 阶段 | 内容 | 验收 |
|---|---|---|
| M0 | 本方案文档 | 方案评审通过 |
| M1 | 医护轮/伤员标戳 schema | `.medic-round.json` / `.patient.json` 可解析、可检索 |
| M2 | 赤脚手册/医护手册 | 标准动作可复制执行 |
| M3 | 分诊/诊断/补丁提案模板 | 不实施补丁可读、可 QA |
| M4 | 异常档案/RCA 模板 | 模型 vs 偶发判定有证据 |
| M5 | 一次真实/演练伤员收治 | 全流程闭环，未改产品代码 |

---

## 12. 明确不做

- 不做机动快速部队/定时 SHA 巡检/自动拉起；
- 不做常驻后台医护 daemon；
- 不自动应用补丁；
- 不自动删除坏数据/分支/worktree；
- 不替代 QA、正式轮、Command Center、General Staff；
- 不把医护轮变成万能修复轮；
- 不提交原始截图/聊天正文/token/logcat 正文。

---

## 13. 结论

- 机动快速部队方案**废弃**；成熟 git/OpenRig registry/CLOSEOUT 足以做日常变更审计。
- 医护中心值得建立，但定位是**按需分诊 + 标戳 + 不实施补丁 + 异常档案 + RCA**，不是自动修复器。
- 医护轮使用独立 `MED-` 标戳，伤员使用 `PAT-` 标戳；不移动原目录、不占用主链 R 编号。
- 本文件只定义方案，未实施任何医护 workflow、stamp 或代码。
