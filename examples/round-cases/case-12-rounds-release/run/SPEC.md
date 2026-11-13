# SPEC — OpenRig 混合编排母版（workflow-group 控制面 + OpenRig 执行面）

## 0. 分层声明

baseline: composite/two-plane-orchestration@1.0.0
contracts: strategy@1.0.0, research@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0, audit@1.0.0

> 本文件是本母版的特化规则，优先于通用 WORKFLOW/roles 中冲突的部分。
> **本母版不是一次具体项目 run，而是一套可实例化的双平面编排契约。**

## 1. 目标

把一个项目工作包从“人类意图”推进到“可验收结果”，同时保留两层事实：

- **控制面（workflow-group）**：`SPEC/PROJECT/DECISIONS/STATUS/ISSUES` 是意图、决策、验收和不可抵赖证据的权威。
- **执行面（OpenRig）**：rig、seat、queue packet、workflow instance、transcript 是实时执行状态、所有权和可恢复性的权威。

母版必须能回答四个问题：

1. 这个 run 要做成什么，谁拍板，什么算完成？（workflow-group）
2. 现在谁在做、做到哪、阻塞是什么？（OpenRig）
3. 结果证据在哪里，能否复跑？（两边共同的证据目录）
4. 出故障时从哪一层恢复，是否会重复工作？（bridge 契约 + queue/workflow trace）

## 2. 双层权威（硬规则）

| 事实                           | 唯一权威                                                  | 不允许的事                                |
| ------------------------------ | --------------------------------------------------------- | ----------------------------------------- |
| 目标、范围、验收判据           | workflow-group `PROJECT.md` / `SPEC.md`                   | 用 OpenRig queue 正文替代项目目标         |
| 重大取舍、删除、预算、权限     | workflow-group `DECISIONS.md`                             | 让 agent 在聊天里自行“拍板”               |
| 实时 seat 状态、队列归属、阻塞 | OpenRig `rig ps` / `queue` / `workflow show`              | 手工伪造 queue 状态或把 STATUS 当执行队列 |
| 收到的任务、交付回执           | OpenRig queue packet + transcript + local STATUS 证据指针 | 只写一句“已完成”而没有证据                |
| 跨重启连续性                   | OpenRig snapshot / session resume token + bridge state    | 用新的 fresh seat 冒充恢复                |

**同步原则**：workflow-group 不自动覆盖 OpenRig 的 queue/workflow；OpenRig 不会把聊天内容自动写进 local DECISIONS。两边通过 `OPENRIG-BRIDGE.json` + evidence paths 建立映射，主会话负责最终拍板。

## 3. 母版组成

```text
templates/specialized/openrig-workflow-master/
  SPEC.md                  # 本文件
  PROJECT.md               # 控制面 run 计划
  DECISIONS.md             # 决策账本
  README.md                # 实例化步骤
  ENTRYPOINTS.md           # 入口选择/调用链/KB↔项目票入口
  ARCHITECTURE.md          # 接入/管理/优化详解
  render_master.py         # 渲染每 run 的 OpenRig spec/bridge
  templates/
    rig.yaml.tpl
    workflow.yaml.tpl
    agent.yaml.tpl
    guidance-team.md
```

渲染后每个 run 得到：

```text
runs/RUN-ID/openrig/
  rig.yaml                 # 唯一 rig 名、cwd、model、seat 映射
  workflow.yaml            # 唯一 workflow id/target；v1.2 七步（分支 QA + join + 返工边）
  agents/worker/agent.yaml # 自包含 AgentSpec
  guidance/team.md         # 团队指导
  OPENRIG-BRIDGE.json      # schemaVersion=2；bundle 内路径相对、运行期字段绝对
```

v1.2 的 workflow 形状（`templates/workflow.yaml.tpl`）：

```text
plan ──┬─> implement_opencode ──> qa_opencode ──(failed)──> implement_opencode
       │                                  └─(handoff)─┐
       └─> implement_dsh      ──> qa_dsh      ──(failed)──> implement_dsh
                                          └─(handoff)─┤
                                                      v
                                                   qa_join ──> close_round
```

- `failed` 分支键只能是引擎的封闭 exit 枚举，目标是**静态 step id**；因此返工必须按分支各设一个 QA 步，不能靠「按报告内容选 TDO」（引擎无此语义）。
- 回边成环由 `loop_guards.max_hops` 授权与约束；超出即如实失败（`max_hops_exceeded`），不会无界循环。
- 不得为此新增引擎字段/API；`rig.yaml.tpl` 仅在确需新 seat 时改动（默认复用现有 `qa` seat）。

### 3.1 入口路由

进入前先读 [`ENTRYPOINTS.md`](../../../../templates/specialized/openrig-workflow-master/ENTRYPOINTS.md)。三种模式：

- **只读核对**：母版版本/测试/baseline，不启动 OpenRig；
- **local-only**：只用 workflow-group 文档面规划与静态验证，不得冒充真实 E2E；
- **hybrid**：按 `render_master.py → doctor → daemon → rig up → workflow validate/instantiate` 进入执行面。

## 4. 接入模型

### 4.1 推荐：managed isolated

- 每个 run 使用独立 `OPENRIG_HOME=/tmp/openrig-workflow-RUN-ID` 和独立 daemon 端口。
- 不碰用户现有 dsh web、OpenRig daemon、tmux server。
- 生命周期：start → up → instantiate → work → verify → down → stop → archive evidence。
- 优点：可复现、可回滚、不会把不同项目 queue/session 混在一起。
- 代价：每次一个短生命周期 daemon；适合一次性工作包/批次。

### 4.2 可选：attached

- 连接已有 OpenRig daemon/rig；bridge 用唯一 rig 名隔离。
- 仅在用户明确要求复用 live rig 时使用。
- 必须先检查 namespace 冲突；不得 kill 非本 run 的 tmux/daemon。

### 4.3 降级：local-only

- OpenRig 不可用时，仍可用 workflow-group 本地模式完成规划和静态验证；
- 不得把 local-only 的结果写成真实 E2E 通过。

## 5. 运行阶段（一个实例 = 一个工作包）

| 阶段            | 控制面                                     | 执行面                                      |
| --------------- | ------------------------------------------ | ------------------------------------------- |
| 0 preflight     | run-id、repo、scope、预算、模型/运行时策略 | 隔离 home、端口、CLI、runtime bin           |
| 1 init          | `wf.py new-run` + render master            | 生成 rig/workflow/bridge                    |
| 2 launch        | 记录 bridge/commit/dirty                   | daemon start + rig up；5 seats ready        |
| 3 plan          | PMO 写 PROJECT 计划与验收                  | workflow instantiate；entry packet 到 PMO   |
| 4 build         | TDO 只写证据指针，不改别人的 WS            | OC/DSH 两个 branch 并行/串行按预算          |
| 5 verify        | QA 对照 SPEC/证据开 ISSUE                  | queue/workflow trace + transcript           |
| 6 close         | main 拍板 DECISIONS/STATUS                 | workflow close/abort；rig down；daemon stop |
| 7 retrospective | 记录成本、失败、优化                       | 保存 sidecar/queue receipt 摘要             |

## 6. 角色映射（默认）

| 控制面角色 | OpenRig seat            | 运行时   | 职责                           |
| ---------- | ----------------------- | -------- | ------------------------------ |
| MAIN       | `control-main@RIG-NAME` | opencode | 最终拍板、收轮、异常升级       |
| PMO        | `control-pmo@RIG-NAME`  | opencode | 计划、拆分工作包、验收口径     |
| TDO-OC     | `exec-tdo-oc@RIG-NAME`  | opencode | OpenCode 分支实现与证据        |
| TDO-DSH    | `exec-tdo-dsh@RIG-NAME` | dsh      | DSH 分支实现/第二意见/批量任务 |
| QA         | `assurance-qa@RIG-NAME` | opencode | 独立核查、ISSUES、回归         |

SAFETY 是可选扩展：涉及 H 盘、不可逆删除、外部发布时，必须另加 gated safety 流程/seat；默认母版不启动。

## 7. 证据与完成定义

- 每个工作包必须有两类证据：
  1. **执行证据**：OpenRig queue packet id、workflow step id、transcript 路径、session id（脱敏）。
  2. **结果证据**：可复跑命令、退出码、日志、截图/文件 hash。
- 每条 ISSUE 必须有 owner、严重度、建议动作、证据路径。
- DoD：
  - 所有工作包有 packet receipt 或明确 SKIP 原因；
  - QA 全部检查项有 PASS/WARN/FAIL/SKIP；
  - 无 open S1/S2；
  - `OPENRIG-BRIDGE.json` 与实际 rig/workflow/home 一致；
  - teardown 前必须完成项目内 OpenRig 归档：`$OPENRIG_REPO/var/openrig-archive/machines/<machine>/runs/<run-id>/`，且 `MANIFEST.json.archiveStatus == "COMPLETE"`、`required.*` 全为 `true`；
  - 归档必须包含 run 快照、关联 DSH session、transcript capture、`OPENRIG-STATE`/bridge 证据和 live `OPENRIG_HOME` 白名单快照；缺项不得清理 live home，历史缺口只能 `--allow-incomplete` 补档并显式记录；
  - teardown 后无残留 daemon/tmux/runner；
  - pytest 全绿必须**连同环境陈述**（`rig` 与 `node` 均可解析）；缺 `rig` 为 137/2、缺 `node` 为 135/4（两者皆缺为 133/6），不得只写「全绿」；
  - 复盘记录进入 DECISIONS 或 POSTMORTEM。

## 8. 禁止

- 不把 API key/token/auth 内容写进 bridge、queue、报告、transcript 摘要。
- 不直接修改 OpenRig 的 queue/workflow 数据库。
- 不绕过 `workflow-group` 的 DECISIONS 做删除/发布/权限变更。
- 不把“rig up 成功”“seat ready”“workflow instantiate 成功”冒充业务验收。
- 不跨 run 共享 `OPENRIG_HOME`，除非显式 attached 模式并校验 namespace。
