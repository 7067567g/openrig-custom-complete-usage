# OpenRig 混合编排母版 — 接入、管理、优化详解

## 1. 设计目标

本母版解决一个具体矛盾：

- workflow-group 擅长**目标、决策、验收、证据链**，但它没有真正的多 seat 执行面；
- OpenRig 擅长 **seat、queue、workflow、transcript、恢复**，但它不应成为项目决策账本；
- 两者直接互相复制状态会漂移，完全不用 OpenRig 又回到单会话搬运。

因此采用**双平面 + 单一映射**：

```text
workflow-group (control plane)
  SPEC / PROJECT / DECISIONS / STATUS / ISSUES / evidence/
            ▲
            │ OPENRIG-BRIDGE.json + evidence paths
            ▼
OpenRig (execution plane)
  daemon / rig / seats / queue packets / workflow instance / transcripts
```

这不是“二选一”，而是各自拥有不同事实类别。实时状态只查 OpenRig；目标/决策/验收只查 workflow-group。

---

## 2. 为什么不让一层包办

| 方案                         | 优点                            | 问题                                            |
| ---------------------------- | ------------------------------- | ----------------------------------------------- |
| 只用 workflow-group          | 轻、可审计、文档稳定            | 无真正 seat 隔离、无 queue/claim、难并发        |
| 只用 OpenRig                 | 真正的多 agent、queue、workflow | 易把临时执行状态当项目目标；证据/裁决分散在聊天 |
| 双平面全量同步               | 表面一致                        | 两套状态必然漂移，冲突时无权威                  |
| **双平面各管事实（本母版）** | 权威明确、可恢复、可审计        | 需要严格 bridge 和角色映射                      |

硬边界：

- 不直接改 OpenRig SQLite / queue 表；
- 不在 DECISIONS 里抄 queue 的实时 state；
- 不在 OpenRig queue 正文里写“最终验收已通过”作为唯一依据；
- 不用 fresh seat 冒充 resume。

---

## 3. 接入设计

### 3.1 生成物

`render_master.py` 为每个 run 生成自包含 bundle：

```text
runs/<run-id>/openrig/
  rig.yaml
  workflow.yaml
  agents/worker/agent.yaml
  guidance/team.md
  OPENRIG-BRIDGE.json
```

生成物特点：

- **唯一 rig 名**：`openrig-<run-id>`；
- **唯一 workflow id**：`openrig-workflow-<run-id>`；
- **绝对项目 cwd**：`<project-root>`；
- **自包含 AgentSpec**：`agent_ref: local:./agents/worker`；
- **唯一 seat 命名空间**：`<member>@<rig>`；
- **独立运行根**：`/tmp/openrig-workflow-<run-id>`。

### 3.2 Bridge 契约

`OPENRIG-BRIDGE.json` 是双平面唯一映射文件，至少包含：

| 字段                       | 作用                                                                                                                                                                             |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schemaVersion`            | bridge 文件形状版本，**当前生成必须为 `2`**（与 `render_master.py` 的 bridge 输出一致）；`doctor` 兼容读取 `schemaVersion=1` 的 legacy bridge 并给迁移提示，其他/缺失值报 `FAIL schemaVersion`。只有字段形状变化才升版 |
| `runId`                    | 控制面 run 标识                                                                                                                                                                  |
| `projectRoot`              | OpenRig seat 的实际 cwd                                                                                                                                                          |
| `bundleDir`                | 生成物位置                                                                                                                                                                       |
| `rigName` / `workflowId`   | 执行面唯一身份                                                                                                                                                                   |
| `rigSpec` / `workflowSpec` | 可复跑的 spec 路径                                                                                                                                                               |
| `openrigCli`               | CLI 入口（可能是 wrapper）                                                                                                                                                       |
| `openrigHome`              | 隔离 daemon/queue/snapshot 根                                                                                                                                                    |
| `daemonPort`               | 隔离 daemon 端口                                                                                                                                                                 |
| `seatMap`                  | 控制面角色 → canonical session                                                                                                                                                   |
| `runtimeEnv`               | OpenCode/DSH bin、model、profile                                                                                                                                                 |
| `policy`                   | 并发、hops、resume、safety、源码权限；其中 `policy.safetyMode` 仅允许 `on-demand`（默认，`render_master.py` 写入）/ `always`，`doctor` 对缺失或其它值报 `FAIL policy.safetyMode` |

`doctor` 对新生成 bridge 的 `schemaVersion=2` 与 `policy.safetyMode` 做校验；`schemaVersion=1` 仅按 legacy 只读兼容并输出迁移提示；未知形状或非法 safety 枚举不会被静默 PASS。

禁止把 API key、auth 文件内容写进 bridge。

### 3.3 接入模式

**managed isolated（默认推荐）**

```bash
export OPENRIG_HOME=/tmp/openrig-workflow-<run-id>
rig daemon start --no-kernel --port <port>
rig up <bundle>/rig.yaml --cwd <project-root> --non-interruptive --yes --json
rig workflow instantiate <bundle>/workflow.yaml \
  --root-objective "..." --created-by control-main@<rig> --json
```

特点：每个 run 独立 daemon/queue/tmux；结束后 `rig down` + `daemon stop`。
适合一次性工作包、批次、可复现验收。

**attached**

连接已有 daemon/rig。必须：

- 生成唯一 rig 名，禁止复用已有 rig；
- 先 `rig ps --json` / `rig workflow status` 检查 namespace；
- 不 kill 任何非本 run 的 seat/tmux；
- 在 DECISIONS 中显式记录 attached 理由。

**local-only**

OpenRig 不可用时的降级：仍可用 workflow-group 完成计划和静态验证，但真实 E2E 必须标记 SKIP/BLOCKED，不能写通过。

### 3.4 接入顺序

```text
preflight (inputs, runtime bins, budget)
  → wf.py new-run
  → render_master.py
  → rig workflow validate
  → daemon start
  → rig up --plan
  → rig up (real)
  → 5 seats ready
  → workflow instantiate
  → entry packet to PMO
```

每步都有可复跑命令和证据；任何一步失败都停在原地，不跳到模型执行。

---

## 4. 管理设计

### 4.1 身份与所有权

| 层     | 身份                               | 所有权规则                                     |
| ------ | ---------------------------------- | ---------------------------------------------- |
| 控制面 | run-id + WS + role                 | 一个 WS 一个写者；PMO/TDO/QA 不越权            |
| 执行面 | canonical session `<member>@<rig>` | 一个 seat 一个 owner；queue claim 是执行所有权 |
| 证据   | `runs/<run-id>/evidence/`          | 只追加；QA/MAIN 可读                           |

默认 seat map：

```text
main       control-main@<rig>       opencode
pmo        control-pmo@<rig>        opencode
tdo-oc     exec-tdo-oc@<rig>        opencode
tdo-dsh    exec-tdo-dsh@<rig>       dsh
qa         assurance-qa@<rig>       opencode
```

### 4.2 Queue 与 STATUS 的分工

- OpenRig queue = **工作 ledger**：谁收到、谁 claim、何时 blocked、回执在哪。
- workflow-group STATUS = **决策/证据指针**：这个 run 做到哪、为什么、下一步谁拍板。
- 建议本地 STATUS 只写：
  - packet id；
  - 证据路径；
  - 阻塞/需要拍板的点；
  - 完成状态。
  - 不复制 queue 全文。

### 4.3 状态同步

由 `tools/openrig_bridge.py` 执行只读状态/证据同步；bridge 是契约，工具不修改 queue/workflow，也不启停 daemon。

| 命令      | 读取                                                                                                                                                                                | 写出                                                                                                                                                                                      | 退出码                                                       |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `status`  | `rig ps --nodes --rig <rig> --full --json`；`rig workflow list --json`（按 `bridge.workflowId` 选 active 实例）；`rig queue list --all-rigs --limit 500 --json`（按 `@<rig>` 过滤） | `OPENRIG-STATE.json`：`schemaVersion/generatedAt/seats{total,ready,nodes}/workflow{instance,status,step,owner,frontier}/queue{total,pending,in-progress,blocked}/sources/errors/degraded` | `0` 全就绪；`2` 降级                                         |
| `capture` | `openrigHome/transcripts/<rig>/**`；目录不可读时逐 seat 回退 `rig transcript <seat> --tail 50000 --json`（沙箱 seat 看不到 daemon home 时）                                         | `capture-manifest.json` + transcript 文件（默认 `evidence/openrig-transcripts/<rig>/`，可用 `--source`/`--out` 指定）                                                                     | `0` 成功且扫描干净；`3` 命中密钥模式；`1` 无文件或来源不可用 |
| `doctor`  | bridge（含 `schemaVersion`、`policy.safetyMode`）+ `rigSpec` + `workflowSpec` + `openrigHome`                                                                                       | stdout 报告（每条不一致一行 `FAIL <field> bridge=… spec=…`）                                                                                                                              | `0` PASS；`1` FAIL                                           |

`status --json` 把同一个 state 对象打到 stdout（字段与落盘一致）；人类模式只打一行摘要。无论采集是否失败都会先落盘，失败信息进 `errors`/`sources`，因此 `rc=2` 时仍有部分证据。`degraded` 为真当且仅当：seat 未全 ready、任一采集命令非零、或 workflow 实例缺失。

`capture` 清单每个文件记录 `path` / `bytes` / `sha256`，`source` 记录来源和 `kind`（`transcripts-dir` 或 `cli-fallback`），`generatedAt` 记录时间；清单可复算：

```bash
python3 - <<'PY'
import hashlib, json, pathlib
base = pathlib.Path("<capture out dir>")
m = json.loads((base / "capture-manifest.json").read_text())
assert all(hashlib.sha256((base / f["path"]).read_bytes()).hexdigest() == f["sha256"] for f in m["files"])
print("manifest ok", m["ok"], "scan ok", m["scan"]["ok"])
PY
```

密钥扫描模式为 `sk-<token>`、`OPENAI_API_KEY=`、`Bearer <token>`；命中时只报 `file:line:kind`，不打印命中行或密钥值，退出码 `3`。

刷新时机：

- rig up / workflow instantiate 后；
- 每个 packet claim/close 后；
- QA 开始前；
- 收口/清理前。

### 4.4 连续性与恢复

优先级：

1. **resume**：使用 OpenRig snapshot + resume token + same node id；
2. **fresh-primed**：没有 runtime session 的 seat 必须显式 fresh，并记录原因；
3. **rebuild**：仅当 checkpoint 明确可用；
4. **failed**：不能伪造继续。

硬规则：

- 不用新 rig 同名 seat 冒充旧会话；
- 删除/重建前先取 snapshot；
- bridge 记录实际 `openrigHome`/rig/workflow id，恢复时不得猜测。

### 4.5 收口与清理

```text
QA pass / main decision
→ workflow close/abort (需要 reason)
→ rig down (snapshot + session kill)
→ daemon stop
→ tmux/runner 检查
→ bridge/evidence/status 收口
→ 记录 cost/latency/failure/optimization
```

清理证据必须记录：rig id、snapshot id、workflow status、residual process check。

收口阶段的命令/证据契约（QA 可原样复跑）：

| 动作            | 命令                                                            | 成功判据                                                                      | 证据                                                    |
| --------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------- |
| 收口前自检      | `python3 tools/openrig_bridge.py doctor --run-dir <run>`        | `rc=0`，且不出现 `FAIL <field> bridge=… spec=…`                               | `evidence/<ws>/dsh2-doctor.txt`                         |
| 冻结实时状态    | `python3 tools/openrig_bridge.py status --run-dir <run> --json` | `rc∈{0,2}`，`json.loads` 通过；`rc=2` 时 `OPENRIG-STATE.json` 仍含 `errors[]` | `OPENRIG-STATE.json` + `evidence/<ws>/dsh1-status.json` |
| 冻结 transcript | `python3 tools/openrig_bridge.py capture --run-dir <run>`       | `rc=0`；manifest `scan.ok=true`，每个文件 sha256 可复算                       | `capture-manifest.json`                                 |
| 关闭/清理       | `rig workflow project …` → `rig down` → `rig daemon stop`       | workflow 终态、seat/snapshot 可追溯、无残留进程                               | 清理日志 + snapshot id                                  |

`rc≠0` 不等于没证据：`status` 的降级结果仍会写 `OPENRIG-STATE.json`；`capture` 命中密钥（`rc=3`）或来源不可用（`rc=1`）仍会写 `capture-manifest.json`，只是 `ok=false`。收口报告必须引用实际 `rc`，不得把 `rc=2/3` 写成 PASS。

### 4.6 安全

- runtime 认证由 OpenCode/DSH 自己管理，不进 bridge；
- transcript/queue 摘要中不写 key；
- 高风险动作（删除、发布、H 盘、权限变更）必须走 gated safety，不能由普通 TDO 包办；
- 所有 external publish/push 必须由主会话单独决策。

---

## 5. 优化设计

### 5.1 模型与 runtime 选择

默认建议：

| 角色     | runtime      | 模型/策略     | 理由                            |
| -------- | ------------ | ------------- | ------------------------------- |
| MAIN/PMO | opencode     | flash 级      | 计划/协调，成本敏感             |
| TDO-OC   | opencode     | 中/强模型     | 主实现分支                      |
| TDO-DSH  | dsh headless | DeepSeek 路由 | 第二意见、批量/低成本任务       |
| QA       | opencode     | flash/中模型  | 独立核查，避免与 TDO 同模型偏见 |

优化原则：

- 先用便宜模型做计划/分类，再升级到强模型做关键实现；
- QA 不复用 TDO 的会话；
- 同一工作包不让两个 TDO 同时改同一个文件；分支边界写进 packet。

### 5.2 并发和资源

本机 4 vCPU / 5.8GB，默认：

```text
maxActiveAgents = 2
```

- PMO 计划与一个 TDO 可以并行；
- OC/DSH 两个 branch 在预算允许时并行，否则串行；
- 不让 5 seats 同时跑长报告/大测试；
- UI/浏览器/大编译任务一次只放一个。

### 5.3 上下文与任务包

- 启动 prose 只进 `AGENTS.md`，不要自动触发模型；
- 任务包必须包含：目标、范围、允许改的文件、验收命令、证据路径、退出条件；
- 不要每个 packet 都附带全项目背景；使用共享 `AGENTS.md` + 局部文件清单；
- skill 使用项目级 `.agents/skills/`；
- 大输出写 evidence 文件，聊天只留摘要。

### 5.4 队列/工作流调优

一个 workflow instance 只承载一个 bounded round；长期项目用多个 instance/轮次。以下规则对本 run 和后续母版实例生效：

| 契约                       | 规则                                                                                                                                                                                                                                                                                                      | 落点 / 命令                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| packet 粒度上限            | 1 个 packet **≤1 个文件面**且 **≤3 个任务**；超限必须拆包。跨文件但无独立验收面的，用 `depends_on` 串行，不合并成一个包                                                                                                                                                                                   | `rig queue create --body-file <path>`；`workflow.yaml workflow.steps[].depends_on` |
| `tier`                     | workflow 自动投影的 packet 沿用引擎默认 tier（不在母版层改写）；手工/独立 packet 用 `fast`（只读或 ≤1 文件核对）、`routine`（默认，≤1 文件 + ≤3 任务）、`deep`（跨文件分析，执行前拆包）、`critical`（仅人工门控）                                                                                        | `rig queue create --tier <fast                                                     | routine | deep                                                                                                                 | critical>`；`rig queue handoff --tier`（改级时新建）；`rig queue show <qitemId> --json`的`.tier` |
| `priority`                 | 默认 `routine`；`urgent` 仅当该 packet 阻塞当前 round 的 join/收口，并在 body 写明被阻塞的 packet/step；`critical` 仅 S1 或人工门控，TDO 不得自批                                                                                                                                                         | `rig queue create --priority routine                                               | urgent  | critical`；`rig queue handoff --priority`（不原地改库）；`rig queue list --state pending,in-progress,blocked --json` |
| `max_hops` vs `depends_on` | `depends_on` 表达真实前置关系并决定 frontier；`max_hops` 只防循环（默认 10），不是调度工具，不得为绕过大包而调高                                                                                                                                                                                          | `workflow.yaml workflow.steps[].depends_on`、`workflow.loop_guards.max_hops`       |
| fan-out 判据               | 仅当分支文件面互斥且可独立验收时 fan-out；否则串行。join step 在 `depends_on` 列全部分支 step id                                                                                                                                                                                                          | `workflow.yaml workflow.steps[].depends_on`                                        |
| stale claim                | 先用 `rig queue list --state in-progress --json` + `rig queue show <qitemId> --json` 看 claim/age/blocker；stale 由 queue watchdog（`queue-stuck-sweep`、`parked-owner-consumer`）升级，不人工改归属。需要释放时用 `rig queue unclaim <qitemId> --reason stale`，再重新 claim 或 `rig queue handoff --to` | `rig queue list`、`rig queue show`、`rig queue unclaim`、`rig queue handoff`       |
| 写入面                     | 所有 packet 状态变化只走 `rig queue create/claim/update/handoff/unclaim` + `rig workflow project`；**禁止**直接写 sqlite/queue 表、手改 `OPENRIG-BRIDGE.json` 伪造状态、或绕过 daemon 改 tmux/session                                                                                                     | `rig queue ...`、`rig workflow project ...`；禁止 `sqlite3` / `UPDATE`             |

每个 packet 还必须含 owner、acceptance、evidence（`rig queue create --destination` + `--body-file` 的 evidence 段）。历史已超限的 packet 不追溯拆包，新 packet 按本表收口。

### 5.5 成本与延迟观测

每次收口记录：

```text
packet 数、模型调用数、token/cost（可得的）、wall time、
失败/重试/恢复次数、人工介入次数、QA 发现数
```

优化闭环：

```text
测量 → 找出最贵/最慢 packet → 缩小范围/换模型/改并行度 → 下一轮复测
```

### 5.6 可靠性优化

- 启动后先检查 5/5 ready，再 instantiate workflow；
- 不允许 workflow entry packet 发给未 ready 的 seat；
- 每次 down 前取 snapshot；
- resume 失败时如实落 fresh，不静默；
- 所有 spec/render 结果进 run 目录，避免“本机某处有个版本”。

---

## 5.1 v1.2 的双平面契约变化（bridge v2 与返工边）

**bridge v2：把「bundle 身份」与「运行期环境」拆开。**

- bundle 内路径（`bundleDir` / `rigSpec` / `workflowSpec`）一律相对，且不得逃逸 bundle 根——这是「整目录可搬迁」的定义；
- 运行期字段（`projectRoot` / `openrigHome` / `openrigCli`）保持绝对语义，因为它们描述**这台机器这次运行**，而不是产物身份；
- 判据不是「文件里没有绝对路径」，而是「同一 run 同参数渲染到两个不同 output-dir，5 个产物逐字节一致」——绝对路径若混进产物身份，此判据必然失败；
- `doctor` 对 `schemaVersion=1` 的旧 bridge 保持**只读兼容**并给迁移提示：旧 run 的证据必须仍可复跑，静默改写旧 bridge 会销毁证据。

**返工边：静态图能表达什么，不能表达什么。**

- 引擎的 `next_hop.on` 键是**封闭 exit 枚举**（`handoff`/`waiting`/`done`/`failed`），值是**静态 step id**；没有「按 QA 报告内容选目标」的语义。
- 因此「单 QA + 由 PMO 读报告后定向回某个 TDO」无法在图上表达，只能退化为聊天/resume——那正是 v1.2 要消灭的形态。
- 正确形状是**分支专属 QA**：每个分支一个 QA 步，各自的 `failed` 回到本分支 TDO；两分支通过后 `qa_join` 汇合。这样「失败回到正确 TDO」是**图的性质**，不依赖人的自觉。
- 环由 `loop_guards.max_hops` 授权；超出即 `max_hops_exceeded` 如实失败，不会无界循环。hop 预算要写清（基础走查 + 每次返工的增量 × 允许次数）。
- **验收必须是有失败投影的实测**：`failed` exit 被真实投影后，`nextStepId` 回到本分支 TDO、`hopCount` 递增、随后能再次进入该分支 QA。只有静态边没有投影，不算完成。
- 一个诚实的分工事实：**若某轮 run 自身跑在改前图上，它就无法演示自己的返工边**。这类 run 的返工证据只能来自独立实例的隔离 probe；不得因此把「图上有边」写成「返工已可用」。

## 6. 故障分类与处理

| 故障                   | 判定                       | 处理                                          |
| ---------------------- | -------------------------- | --------------------------------------------- |
| daemon 不可达          | `rig status`/端口失败      | 停止；不重复 instantiate；检查 home/port      |
| rig 部分 seat ready    | `rig ps --nodes`           | 不启动 workflow；修复该 seat 或重新 up        |
| workflow validate fail | 命令返回非 0               | 修 spec；不 instantiate                       |
| entry owner 错         | workflow show              | 修 roles/preferred_targets；不手工改 DB       |
| queue stalled          | `workflow status`/watchdog | 查 owner/claim/blocker；必要时 route/重新投递 |
| runtime auth 失败      | transcript/sidecar         | 修 provider；不伪装成功                       |
| context overflow       | usage/transcript           | 拆包/压缩/换模型                              |
| resume 失败            | restore 结果               | 记录 fresh-primed；需主会话决策才丢历史       |
| 测试失败               | 日志/CI                    | 开 ISSUE；不把失败写成 PASS                   |

---

## 7. 母版扩展点

- **SAFETY**：高风险项目另加快照/审批/gated action seat，作为独立 pod 或 queue gate。v1.2 仍只定义契约；**执行器未实现，已转 v1.3 候选**。执行器落地前，属于 SAFETY 类别的动作只能由具名人类在 OpenRig 之外执行并留证，agent 不得代跑。`doctor` 只强制校验 bridge 载体（新生成 `schemaVersion=2`；legacy v1 只读兼容）与 `policy.safetyMode ∈ {on-demand, always}`，不执行任何 gate。

  | 契约项                      | 取值/要求                                                                                                                                                                                         |
  | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | 动作类别 `action_class`     | `read-only` / `write-reversible` / `delete-irreversible` / `external-publish` / `permission-change` / `hdisk-write`                                                                               |
  | gate 结果 `gate_result`     | `PASS`（可执行）/ `FAIL`（拒绝，需改写动作）/ `NEEDS-HUMAN`（材料不足）/ `EXPIRED`（批准过期）                                                                                                    |
  | 人工批准前置                | `delete-irreversible`、`external-publish`、`permission-change`、`hdisk-write` 必须取得具名 human 的 `approve`，记录 `action_id`、目标、`expires_at`；agent 不得自批、不得把多个动作合并成一次批准 |
  | 账本路径                    | `runs/<run-id>/safety/gate-ledger.jsonl`，只追加；每条含 `action_id/action_class/target/gate_result/approver/approved_at/expires_at/executed_at/evidence`                                         |
  | bridge 载体 `schemaVersion` | 新生成必须为 `2`（与 `render_master.py` 一致）；`schemaVersion=1` 只读兼容并提示迁移；未知/缺失 → `doctor` `FAIL schemaVersion`；只有字段形状变化才升版 |
  | bridge `policy.safetyMode`  | `on-demand`（默认，`render_master.py` 写入）/ `always`；缺失或其它值 → `doctor` `FAIL policy.safetyMode`；本轮不改变默认值                                                                        |
  | 失败处理                    | 首个非 `PASS` 立即停止；`FAIL` 的动作不得改参数复用同一 `action_id`，只能新建动作重新走 gate                                                                                                      |
  | 审计                        | 账本与 evidence 路径进入收口报告；批准过期后动作不得执行                                                                                                                                          |

- **多 TDO**：同一 pod 增加更多 TDO；每个 packet 的文件范围必须互斥；
- **长任务**：一个 run 多轮，每轮实例化新 workflow instance；
- **多项目**：每个 run 一套 bridge/rig/workflow，不复用 `OPENRIG_HOME`；
- **替换 runtime**：保持 seatMap 和 workflow step id 不变，只改 rig runtime/model。

---

## 8. 验收清单

- [ ] `render_master.py` 已生成唯一 rig/workflow/bridge/agent/guidance；
- [ ] `rig workflow validate` PASS；
- [ ] `rig up --plan` PASS；
- [ ] 真实 rig 5/5 seats ready；
- [ ] workflow instantiate entry packet 到 PMO；
- [ ] queue/transcript/session id 有证据；
- [ ] resume 或 fresh-primed 有明确记录；
- [ ] QA 无 open S1/S2；
- [ ] rig down/daemon stop 后无残留；
- [ ] 复盘至少记录一条可执行优化。
