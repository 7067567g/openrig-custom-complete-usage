# 长任务工作流竞品分析：我们这套「监护器 + 每轮独立 headless」处在什么位置

- 日期：2026-10-25（所有事实以该日抓取到的页面/仓库为准）
- 读者：要决定「继续用 / 改 / 换 / 开源」的人
- 基准对象：`workflow/` 那层外壳（`loop_supervisor.py` + `plan.json` + `ROUND-SPEC.md`），不是 dsh 本身
- 置信标记：**✅** 直接抓官方文档/仓库核对过机制；**◐** 官方页面/仓库存在，机制按公开资料描述但未逐条核对；**○** 未验证，只能当线索
- 抓取限制：`developers.openai.com` 在本环境返回 403，Codex 的沙箱机制改以仓库内 `codex-rs/linux-sandbox/README.md` 为准；部分商业产品（Devin / Manus / Factory / Amp / Cursor）只核对到公开页面存在，具体版本与计费标 ○

---

## 1. 一页结论

**定位一句话：** 我们是「**单机、文件即状态、进程即隔离、轮即编排单元、人在轮边界拍板**」的长任务外壳——功能上夹在「持久化工作流引擎」（Temporal/DBOS/Restate）和「本机多座位 agent 管理器」（OpenRig/Claude Squad/Conductor）之间，但两边最贵的东西都没买：没有事件日志，用 git + 文件；没有容器，用进程 + 契约。

**三个最强优势（都是竞品"做得到但很贵"或"架构上不会做"的）：**

1. **上下文新鲜度是结构性的，不是提示词技巧。** 每轮新起 `dsh --profile headless` 进程，上一轮的上下文一个字都不继承，只继承 `runs/<id>/reports/` 与 `VERDICT.md`。Claude Code 的 subagent 虽然也是新上下文，但它活在同一 session/runtime 里，结果要回流主上下文；Devin/Cursor 的办法是把整台 VM 搬走。**只有我们是"新进程 + 旧产物"，成本最低且不依赖任何会话存活。**
2. **零基础设施，单机成本。** systemd user unit + 几个 JSON/MD 文件 + 本机 API key。Temporal 自托管要 server + 数据库 + worker 三件套；Inngest/Trigger.dev 要账号；DBOS 要一个 Postgres；Prefect/Dagster 要 server + work pool。**在"一台工作站、一个人、跑几十轮"这个规模上，我们的运维成本是 0，它们是 0.5~2 人天。**
3. **验收规则是可执行的，不是口头约定。** 「缺 `DONE` 或 `VERDICT.md` 即未完成」+ 独立 verify 轮 + 每轮 diff 落 `reports/`，让"做完了"这件事有机器可判、人可读、git 可 diff 的证据。durable engine 的审计是事件历史（机器格式，人读不了）；coding agent 的审计是 transcript（非结构化）；我们的审计是**契约文件**。最接近的是 OpenRig 的 proof + 指定 reviewer 签收（✅），但那是交互式座位模型。

**三个最大短板：**

1. **并行度 = 1，且是硬编码的。** 单个 supervisor、单份 `loop-state.json`、同一 `workflow/` 目录只允许一个监护器（README 明说，代码里也确实没有 flock）。Claude Code dynamic workflows 默认 16 并发、单 run 上限 1000 agents（✅）；OpenRig 多 seat 并行（✅）；Temporal 的并发只受 worker 数限制。
2. **状态是文件 + pid，没有事件日志，所以"恢复"只能是"整轮重跑"。** 没有 `step` 级检查点，崩溃后无法从第 3 步续；重跑还会叠加已改了一半的代码。Temporal 靠事件历史 + 确定性重放（✅）；Restate 靠 journal，崩溃后跳过已完成步骤（✅）；DBOS 把 workflow/step 状态 checkpoint 进 Postgres 系统库（✅）。
3. **隔离是进程级，且 worker 以 `danger-full-access` 起。** 同机同用户、共享工作区，靠 `ROUND-SPEC.md` 的"不 push / 不发布 / 不碰用户服务"约束。Codex CLI 在 Linux 上用 bubblewrap + seccomp + user/PID/net namespace，`/` 默认只读、`.git` 与 `.codex` 单独保护（✅）；container-use 一 agent 一容器一分支（✅）；Cursor/Devin 是云 VM。**要跑不可信代码，我们直接出局。**

**一句话选型：** 单机、自己仓库、无人值守、以"小时级切片"为粒度 → 继续用并补状态机；一旦需要并行、多机、强隔离、step 级恢复中的任意两项 → 换，别改造。

---

## 2. 我们的机制摘要（对齐基准）

### 2.1 结构

```
systemd user unit (openrig-loop.service, Restart=on-failure)
  └─ loop_supervisor.py --watch --interval 120
       ├─ 读 plan.json：loops[].rounds[]（run_id / type / goal / inputs / budget_sec）
       ├─ tick：找到当前轮 → ensure_run() 从 templates 生成 PROJECT.md / SPEC.md / reports/
       ├─ spawn: python loop_supervisor.py --worker <run_id>
       │     └─ 起 dsh --profile headless --json -（prompt 走 stdin，cwd=目标仓库）
       │           ├─ ROUND-PLAN.md（≤3 目标 / 文件边界 / 测试命令 / NOT-DOING）
       │           ├─ 改代码 + 写测试 + 跑测试 + reports/
       │           ├─ VERDICT.md（CONTINUE | ADJUST | STOP）
       │           └─ DONE
       └─ 下一 tick：DONE + VERDICT 齐 → completed；否则按心跳/pid 判定
```

### 2.2 不变量（这套东西真正的设计）

| 不变量 | 实现 | 换来的东西 | 代价 |
| --- | --- | --- | --- |
| 每轮一个新进程 | `dsh --profile headless --json -`，prompt 走 stdin，`--json` 只进日志不被解析 | 上下文不膨胀；绕开交互信道 ~90 分钟截断；进程死活与产出解耦 | 没有跨轮记忆，全靠文件交接；启动成本每轮一次 |
| 只认文件，不认进程输出 | supervisor 不解析 NDJSON，只看 `DONE`/`VERDICT.md`/`worker.json` | 执行器可替换（今天 dsh，明天 claude -p 也行） | 无法从输出流里拿结构化进度；卡住时只能靠心跳 |
| 心跳 60s / 超时 180s | worker 写 `runs/<id>/.pipeline/worker.json`（pid/started/heartbeat） | 僵尸进程可判、可杀（>180s SIGTERM，>2× 阈值 SIGKILL） | 心跳只证明"进程活着"，不证明"在干活" |
| 缺 DONE/VERDICT 就 nudge，≤6 次后 BLOCKED | `MAX_NUDGES=6`；`--nudge` 会提示"先核对 ROUND-PLAN/STATUS，不要重复完成的波次" | 语义失败（跑偏/没交付）有上限，不会拖死整条线 | 重试粒度=整轮；nudge 是"再跑一遍"，不是"从断点续" |
| 独立验证轮 | `plan.json` 里单列 `type: verify`（示例：`loop2-r2-verify`），复跑测试、核版本口径 | 不接受实现者自述；实现与验收分离 | 验证者同样只能看到文件，看不到实现者的推理 |
| git 基线 | `BASE-COMMIT` 文件 + 每轮 `git diff $(cat BASE-COMMIT) --stat` 进 reports | 可 diff、可 bisect、可回滚 | 基线是"单一基线"而非"每轮一提交"；自动提交没实现 |

### 2.3 三个必须说清的实现边界（别把设计当现状）

1. **`budget_sec` 不是硬约束。** `plan.json` 每轮写了 `budget_sec: 7200`，但它只进 prompt 文本（`loop_supervisor.py:207`「预算按本轮 budget_sec」）；真正的硬超时是全局 `OPENRIG_LOOP_ROUND_LIMIT`（默认 7200s，`communicate(timeout=ROUND_LIMIT)`）。**每轮不同预算目前不生效**，改 plan 不会改杀进程的时间。
2. **没有并发保护。** 状态就是 `workflow/loop-state.json`（README 自己写"同一时间只跑一个监护器，否则抢同一份 loop-state.json"），代码里没有 `flock`。两个人/两个 systemd 实例同时起 = 状态互相覆盖。
3. **"每轮一个 git 基线提交"是更严格的用法，分享版没自动化。** supervisor 不 `git commit`；它只提供 `BASE-COMMIT` 和 diff 统计模板。要真做到"每轮一提交"，得在 `ROUND-SPEC.md` 里要求 MAIN 提交，或 supervisor 在轮结束时代提交——目前都没做。

---

## 3. 竞品全景表

> 编排单元 = 这套东西"一次调度决策"作用在什么上；持久化 = 崩溃/重启后靠什么活下来；隔离 = 最外层边界；验证 = 谁判定"做完了"；部署 = 跑在哪；适合谁 = 一句话。

### 3.1 类别一：Agent 编排框架/库

| 代表 | 编排单元 | 持久化 | 隔离 | 验证 | 部署 | 适合谁 |
| --- | --- | --- | --- | --- | --- | --- |
| LangGraph ✅ | 图节点 / super-step；函数式 API 里是 task | checkpointer 按 `thread_id` 存图状态快照 + pending writes；`interrupt()` 后 `Command(resume=...)`；store 存跨线程长期记忆 | 同进程（子图共享 runtime），要隔离得自己拆进程 | 无内建；靠 eval/测试节点 | 库；生产用 Agent Server/LangSmith 托管 | 要"人在任意点介入 + 时间旅行"的 agent 应用 |
| CrewAI ◐ | Crew（角色 agent，顺序或层级 manager）+ Flow（`@start/@listen/@router` 事件驱动） | Flow 有 checkpointing/persistence（v1.15.x 文档专章） | 同进程 | 无内建；靠 task 的 output/guardrail | 库 + 云 | 快速搭"角色分工"团队，流程偏线性 |
| AutoGen / AG2 ◐ | AutoGen v0.4 起是 actor 模型：异步消息 + 事件驱动 runtime（AgentChat/Core/Extensions）；AG2 为社区分支，延续 GroupChat 对话编排 | 无强持久化；靠消息历史/外部存储 | 同进程（分布式 runtime 可跨进程，需配置） | 无内建 | 库 | 研究型多 agent 对话、可容忍重启重跑 |
| OpenAI Agents SDK ✅◐ | Agent + handoffs + guardrails + sessions + tracing | 进程内 sessions；**本身不做 durable execution**，官方路径是接 Temporal/DBOS（两家都有集成文档 ✅） | 同进程 | guardrails（输入/输出校验），不是交付验收 | 库；跑在你自己的服务里 | 想要"薄 SDK + 自己接持久化"的团队 |
| Google ADK ◐ | LlmAgent + 工作流 agent（Sequential / Parallel / Loop） | Session/State/Artifacts 服务（可换后端） | 同进程；部署到 Agent Engine 时是托管运行时 | 无内建 | 库 + Vertex AI Agent Engine | GCP 体系内做多 agent，要 A2A 互通 |

**这一类共同的盲区：** 它们都假设"编排逻辑写在代码里、跑在一个长期存活的进程/服务里"。**没有一家把"执行单元是一个会被杀掉、下次换个新进程重来的 CLI agent"当一等公民。** 我们要的语义（轮=可被外部杀死的黑盒进程 + 文件契约）在这一层是缺位的，所以硬套会别扭：LangGraph 的 checkpointer 存的是图状态，不是"某个 CLI 进程改到一半的仓库"。

### 3.2 类别二：持久化工作流引擎（durable execution）

| 代表 | 编排单元 | 持久化 | 隔离 | 验证 | 部署 | 适合谁 |
| --- | --- | --- | --- | --- | --- | --- |
| Temporal ✅ | Workflow Execution（代码）+ Activity（副作用） | **事件溯源：事件历史 + 确定性重放**（workflow 代码从头重跑，按历史对齐；worker 轮询 task queue 领任务；Activity 结果记录后不重跑；timer/signal/child workflow/schedule 都是一等公民） | 不提供；worker 是你的进程/容器 | 无内建 | Server 集群 + 数据库 + worker（或 Temporal Cloud） | 要"跑几年的业务流程 + 精确恢复"的组织 |
| Inngest ✅ | function run + step | **step 结果 memoize 在服务端**；`step.sleep` 不占算力（最长一年，免费档 7 天）；`waitForEvent`/`waitForSignal` 挂起 | 你的 serverless/容器 | 无内建 | 云（可自托管） | 事件驱动的后端任务、AI 长流程，团队小 |
| Restate ✅ | invocation（handler）+ journal 条目 | **journal 记录每步操作与结果**，崩溃后重放跳过已完成；Virtual Object 单写者 K/V；FaaS 上可 suspend，等待不付费 | 你的服务（Rust 单二进制 Server 前置代理） | 无内建 | 自托管单节点/HA 集群、Cloud、BYOC | 要"低延迟 + exactly-once + 状态"的服务编排 |
| DBOS ✅ | workflow + step（库，不是服务） | **checkpoint 进 Postgres 的 system database**；队列/定时/恢复由库 + DB 完成；Conductor 是可选控制面 | 你的进程 | 无内建 | 库 + 一个 Postgres（Cloud 可选） | 已经有 Postgres、不想再养一套 server 的团队 |
| Prefect ◐ | flow run / task run | 状态机（Scheduled/Running/Retrying/Failed/Completed）+ result persistence；work pool 里 worker 拉取 | worker 进程/容器 | 无内建 | Server + worker（Cloud 或自托管） | 数据管道的"Python 原生"编排 |
| Dagster ◐ | asset materialization（资产为中心） | 运行记录 + 事件日志存 DB；partition/sensor/schedule | run launcher 决定（进程/K8s） | 有 asset checks（数据质量断言） | 自托管或 Dagster+ hybrid（agent 在你侧） | 数据平台，要"资产血缘 + 分区回填" |
| Trigger.dev ◐ | task run（代码跑在你的 worker） | 云端存 run 状态；waitpoint token 实现长时间挂起等人批准；v4 引入 checkpoint/resume（○ 细节未核） | 你的容器/机器 | 无内建 | 云为主 | 想要"Zapier 体验 + 真代码"的后端长任务 |
| Windmill ◐ | script / flow step | Postgres 队列 + 运行历史 | **nsjail 沙箱** + Rust worker | 无内建 | 自托管单二进制 / 云 | 内部工具、低代码 + 脚本混合 |

**这一类共同的盲区：** 恢复的粒度是 **step/activity**，前提是"step 是幂等或可重放的函数"。我们的"step"是一次 LLM 自由发挥 2 小时——**不可重放、不幂等、副作用是"改了仓库"**。所以 durable engine 的恢复语义在这里会退化：重放一个 activity 等于重跑一次 agent，钱照花，副作用可能叠加。它们能解决的是"调度与重试"，解决不了"agent 语义失败"。

### 3.3 类别三：编码 Agent 的多任务/多代理产品

| 代表 | 编排单元 | 持久化 | 隔离 | 验证 | 部署 | 适合谁 |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code（subagents / hooks / background / workflows）✅ | 四层：subagent（同 session 内）、agent team（lead + 同伴）、**dynamic workflow（JS 脚本，`agent()/pipeline()/parallel()`）**、background session | session JSONL + workflow run 结果存 `~/.claude/projects/`，可 resume/重放已完成 agent | 进程内 subagent；`isolation: worktree` 给子 agent 独立 worktree；cloud session 是云 VM | 无强制验收；有 `/code-review`、ultrareview 等评审能力，但"做完"仍靠模型自述 + 人看 | 本机 CLI / 桌面 / 云 / SDK | 已经在 Claude Code 里工作、想少写编排代码的人 |
| OpenAI Codex CLI ✅ | 一次 turn / 一个 session（`codex exec` 非交互） | session rollout 文件 + `codex resume` | **Linux：bubblewrap + seccomp + user/PID/net namespace，`/` 默认只读、写根白名单、`.git`/`.codex` 额外保护**（macOS 另有 Seatbelt 后端，本次未核对） | 自跑测试；人审 diff | 本机 CLI | 要"本机、有真沙箱、能脚本化"的个人/CI |
| OpenHands ◐ | 一次 session（agent controller + 事件流） | 事件流持久化 + 运行时可重建 | **Docker 沙箱 runtime**（代码执行在容器里） | 自跑测试 | 自托管 / 云 | 想自建"开源 Devin"的团队 |
| Devin ○ | 一个 session（云 VM） | VM + snapshot；并行多 session | 云 VM（独立文件系统/进程/网络） | 自跑测试 + 出 PR，人审 | 托管 | 把"整件事"外包出去、按结果付费 |
| Cursor cloud agents ○ | 一次 agent run（云 VM） | VM + git 分支 + PR | 云 VM | 自跑测试 + 录屏/demo + PR | 托管 | 已经在 Cursor 里的团队 |
| GitHub Copilot Workspace ◐ | task → plan → code（已被吸收/退役，见 §3.5） | 无 | 云 | 人审 | — | 历史参考：证明"计划即产物"这条路走通过也被并掉了 |
| Factory ○ | Droid（spec 驱动的执行体） | 会话 + 分支 | 云 / 本机 | 自跑测试 + PR | 托管 + CLI | 想要"规格 → 执行"流水线的团队 |
| Amp ○ | thread（终端/编辑器 agent） | 会话 | 本机 | 人审 | 本机 CLI / 扩展 | 单人、重交互、不要求无人值守 |
| Aider ◐ | 一次编辑会话；**每个 change 一个 git commit**（可关） | **git 历史就是持久化** | 无（本机工作树） | `/test` + lint/test 钩子 + 自动提交 | 本机 CLI | 要"每一步都可回滚"的结对编程 |

**这一类共同的盲区：** 它们把"长跑"解决成"**会话别断**"（background/cloud session、tmux）或"**沙箱别炸**"（VM/bubblewrap），很少有产品把"**轮**"当成一等单元——除了 Claude Code 的 workflow（脚本级，✅）和 OpenRig 的 workflow（任务级，✅）。而这两家的"轮"都活在**一个仍在运行的宿主**里；宿主一停，轮就停。我们是反过来的：宿主只是个看文件的轮询器，轮自己是一个会死的进程。

### 3.4 类别四：本机/开源的 agent 编排与座位管理

| 代表 | 编排单元 | 持久化 | 隔离 | 验证 | 部署 | 适合谁 |
| --- | --- | --- | --- | --- | --- | --- |
| **OpenRig** ✅（0.7.0） | seat（tmux 里的真实 CLI 会话）+ queue task + workflow step | 工作树是**磁盘上的文件夹**（mission/spec/progress/proof），加 LEARNED.md、快照、`rig restore` 重启恢复 | tmux 会话；同机共享工作区（无 per-task 容器） | **proof + 指定 reviewer 签收**（"agent 说做完了"不算） | 本机 daemon（systemd/launchd）+ TUI + Slack + 多机 fleet | 要"一支常驻 agent 团队"而不是一条流水线的人 |
| Claude Squad ✅ | instance（tmux + worktree） | git 分支 + tmux 会话 | tmux + **每任务一个 git worktree** | 人看 diff，满意再 checkout/push | 本机 TUI | 想同时开 5 个 Claude/Codex/Aider 的人 |
| container-use ✅ | agent 会话 + 容器环境 | **每 agent 一个容器 + 一个 git 分支** | 容器（Dagger 驱动） | 人看完整命令历史/日志，可进容器接管 | 本机（MCP server，接 Claude Code/Cursor） | 要"真隔离 + 可丢弃"的并行实验 |
| cmux ✅ | workspace / pane（终端） | 版本化快照 + agent 原生 resume（hooks 存 session id） | 终端 pane / SSH / 云 VM | 人 | macOS app（Ghostty 内核） | 只想"看得过来"，不想被编排器绑住的人 |
| Conductor ◐ | task（worktree）+ Claude Code 会话 | git worktree + 分支 | worktree | 人 review/merge | macOS app | 设计/前端这类"多方案并行比较" |
| worktree 系（Crystal / Sculptor / vibe-kanban / Uzi）○ | 每任务 worktree + 多会话面板 | git + 本地状态 | worktree | 人 | 本机 app/CLI | 同上，选顺手的 |
| agent-farm ○ | 声称是"多 agent swarm / MCP 工具集" | 不明 | 不明 | 不明 | 本机 | **不建议参考**：公开仓库至少有两个同名不同项目，定位互相矛盾 |

**这一类共同的盲区：** 它们的编排对象是"**座位**"（一个长期活着的交互 agent），所以优化目标是"让人同时看住 N 个座位"；我们的编排对象是"**轮**"（一个跑完就死的批处理作业），优化目标是"人不用看"。**这是两种产品直觉，不是同一件事的两种实现。** 唯一在这条线上和我们撞车的是 OpenRig 的 workflow + proof：它也要求"步骤=任务、失败升级、签收才算完"，但它的执行体仍是 tmux 里的交互会话（✅ 官方 features 页），不是 headless 进程。

### 3.5 类别五：托管型自主 Agent

| 代表 | 编排单元 | 持久化 | 隔离 | 验证 | 部署 | 适合谁 |
| --- | --- | --- | --- | --- | --- | --- |
| Manus ○ | 一个 task/session（云 VM + 多 agent 规划/执行） | VM + 会话产物（文件/网页） | 云 VM | 自检 + 用户验收 | 托管（订阅 + credits） | 非工程类交付（报告/网页/数据整理） |
| ChatGPT agent mode ○ | 一次 agent 运行（虚拟计算机：浏览器 + 终端） | 会话 | 托管虚拟计算机 | 关键动作前向你申请确认 | 托管 | 跨网站操作、调研类任务 |
| Google Jules / Antigravity / Deep Research ○ | 一次异步任务（Jules：云 VM，接 GitHub） | 云 | 云 VM | 自跑测试 + PR / 引用核对 | 托管 | 已在 Google 生态里的个人与小团队 |
| GitHub Copilot Workspace ◐ | task → plan → code | — | 云 | 人审 | **2025-05 退役技术预览**（二手来源；官方 GitHub Next 页面仍作为项目展示） | 历史参考：它的"计划先成文再执行"被 Copilot coding agent / Agent HQ 吸收 |

**这一类共同的盲区：** 交付物是"结果"（PR/报告/网页），过程对你不可见也不可改；计费和限流是黑盒；**你的仓库要么上传，要么给 token**。对"改自己工作站上的私有仓库、不能上云"的场景，整类不适用。

---

## 4. 六维定位图（文字版坐标）

每条轴从左到右，`▲` 标我们的位置；`[n]` 是格位编号，正文用它指代。

### 4.1 编排单元

```
[1] 整场会话            Amp、cmux、Devin
[2] 单 agent 回合       Codex CLI、Aider
[3] 轮 / 任务           ▲ 我们、OpenRig task、Claude Squad instance、CC workflow 的 agent() 调用
[4] 图节点 / step       LangGraph node、CrewAI Flow step、ADK 工作流 agent
[5] workflow + activity Temporal、Inngest step、Restate handler、DBOS step
```

**我们在 `[3]`，但和 OpenRig/Claude Squad 的"任务"不是一种东西：** 它们的任务活在一个常驻会话里，我们的"轮"是一个会被 supervisor 杀掉、下次换新进程重来的黑盒。**最近似：** Claude Code dynamic workflow 的"一个 agent 调用"（也是黑盒、也返回结果）；**最不同：** LangGraph（编排单元是图节点，节点间共享状态对象）。

### 4.2 持久化方式

```
[1] 无（内存/会话）      AutoGen/AG2、CrewAI、Claude Squad、cmux
[2] 文件 + git           ▲ 我们、OpenRig 工作树、Aider
[3] DB 快照(checkpoint)  LangGraph checkpointer、Prefect
[4] 事件日志 / 重放      Temporal、Restate、Inngest(step memo)
[5] 关系库事务           DBOS（Postgres system database）
```

**我们在 `[2]`，且是其中最"裸"的：** 没有 schema、没有版本迁移、没有并发控制，状态正确性靠"只有一个 supervisor"这个约定。**最近似：** OpenRig（工作树就是文件夹）与 Aider（git 即历史）；**最不同：** Temporal（事件历史是唯一真相，且要求确定性重放）。

### 4.3 隔离级别

```
[1] 同进程               LangGraph、CrewAI、ADK、OpenAI Agents SDK
[2] 进程                 ▲ 我们、OpenRig(tmux seat)、Codex CLI*
[3] worktree             Claude Squad、Conductor、cmux(可选)
[4] 容器                 container-use(Dagger)、OpenHands(Docker)、Windmill(nsjail)
[5] 微 VM / 云 VM        Devin、Cursor cloud agents、Manus、Jules
```

\* Codex 是"进程 + 内核沙箱"（bubblewrap + seccomp + user/PID/net namespace），严格说在 `[2]` 和 `[4]` 之间：比我们多**内核强制**，比容器少**环境独立性**（仍是同一个根文件系统视图，只是挂载视图被改过）。

**我们在 `[2]` 最左端：** 同用户、同工作区、`danger-full-access`，边界是文档不是内核。**最近似：** OpenRig（tmux 会话，同机共享）；**最不同：** container-use / Cursor / Devin（一个 agent 一个容器/VM）。

### 4.4 验证方式

```
[1] 自述                 Amp、CrewAI、AutoGen
[2] 同轮自检             Devin、Cursor、Codex CLI、Aider
[3] 独立轮 / 独立进程    ▲ 我们
[4] 独立系统 + 签收      OpenRig proof + 指定 reviewer
```

（Claude Code dynamic workflow 的"对抗评审"落在 `[3]` 之前：同一 run 内的独立 agent，但同一 runtime、同一 session，不跨进程。）

**我们在 `[3]`，这是相对位置最高的一维。** 关键差别不是"有没有 review"，而是**验证者是不是一个刚启动、没看过实现过程的新进程**——只有我们是。**最近似：** OpenRig（签收人机制，但签收人多半是人或另一个常驻 seat）；**最不同：** Devin/Cursor（自检 + 人审 PR）。

### 4.5 部署形态

```
[1] 单机零依赖           ▲ 我们、Aider、Codex CLI（supervisor 连常驻都不需要）
[2] 单机守护进程         OpenRig(daemon)、Claude Squad(tmux)、cmux
[3] 自托管 server + DB   Temporal、Restate、DBOS(+PG)、Prefect、Dagster
[4] SaaS                 Inngest、Trigger.dev、Devin、Cursor、Manus、Jules
```

**我们在 `[1]`，且是唯一"连 daemon 都不需要常驻"的（supervisor 本身可以 cron/nohup 起）。** 代价是：没有集中状态 → 没有多机 → 没有团队视图。

### 4.6 谁来拍板

```
[1] 轮内全自主 + 轮边界人   ▲ 我们（轮内无提示；ADJUST/STOP 由人在轮边界最终决定）
[2] 任意点人介入            LangGraph interrupt、OpenRig decision task、ChatGPT agent 接管
[3] 代码里 signal / 审批     Temporal signal/update、Inngest waitForSignal、Restate awakeable
[4] 交付后人才看到           Devin/Cursor/Manus 的 PR 或产物验收
```

**我们落在 `[1]`：轮内没有权限提示（`danger-full-access`）、没有审批队列、没有人机对话**，只有 `DECISIONS.md` 的待决项；人的判断只在轮边界（改 `plan.json`、删 `PAUSED`、看 `VERDICT=ADJUST`）。**最近似：** Devin（异步交付，人在 PR 处出现，但轮内仍会为关键动作申请确认）；**最不同：** LangGraph（设计哲学就是"任意点可中断"）。

### 4.7 汇总

| 维度 | 我们 | 最近似 | 最不同 | 一句话 |
| --- | --- | --- | --- | --- |
| 编排单元 | 轮（外部可杀的进程） | Claude Code workflow 的 agent 调用 / OpenRig task | LangGraph 节点 | 我们的单元"会死"，它们的不会 |
| 持久化 | 文件 + git | OpenRig 工作树 / Aider git | Temporal 事件历史 | 可读性最好，可恢复性最差 |
| 隔离 | 进程（无内核边界） | OpenRig tmux | container-use / 云 VM | 我们信任自己的代码 |
| 验证 | 独立轮、独立进程 | OpenRig proof+reviewer | Devin/Cursor 自检 | 我们唯一"换进程再验" |
| 部署 | 单机零依赖 | Aider / Codex CLI | Temporal / SaaS | 我们的运维成本是 0 |
| 拍板 | 轮边界人 | Devin 异步交付 | LangGraph interrupt | 我们把"打扰"压到最低频 |

---

## 5. 优势（逐条对竞品缺口）

### A1. 新进程 = 真新鲜上下文，且不依赖会话存活

- **机制：** 每轮 `subprocess.Popen([dsh, --profile headless])`，prompt 从 stdin 灌入，stdout 只进日志；supervisor 从不解析模型输出。
- **竞品缺口：**
  - Claude Code subagent 是"新上下文"，但**同一 session**：它的报告要回流主上下文，且 session 一断，subagent 的 run 就没了（background session 能续，但要开着 app / 云端，✅ 文档明确 background 会话与 cloud session 的区别）。
  - OpenRig / Claude Squad / Conductor 的隔离单位是**座位/会话**，agent 一旦"跑飞"，你得人肉 `/clear` 或 handover（OpenRig 有 `rig handover`，✅，但那是人工触发的）。
  - Devin / Cursor 用**整台 VM**换来干净环境，代价是启动慢、按 VM 计费、仓库要上云。
- **为什么竞品做起来贵：** 它们的商业模型建立在"会话/座位"上（订阅席位、并发 session 数），"每轮新进程"会打散会话连续性和计费口径。对我们这只是 `Popen`。
- **买来的限制：** 跨轮没有隐式记忆；所有交接必须显式写文件，写漏了就丢。

### A2. 零基础设施 + 单机成本

- **机制：** 一个 Python 文件 + systemd unit + `plan.json`；没有 DB、没有消息队列、没有容器运行时、没有云账号。
- **竞品缺口：**
  - Temporal 自托管 = Server + 持久化库 + worker（✅ 官方架构：Server 前置、worker 轮询 task queue）；Temporal Cloud 要账号与按 action 计费。
  - Inngest / Trigger.dev 要接云（自托管是"可以"，不是"默认"）。
  - DBOS 最轻，但仍要一个 Postgres（✅ "checkpoint 进 Postgres 的 system database"）。
  - Prefect / Dagster 要 server + work pool + worker。
  - OpenRig 是本机 daemon（✅ 要 Node 22/24 + tmux + 已登录的 Claude/Codex），比我们重一档，但已属"轻"。
- **量化对比（同规模：1 台工作站、几十轮/周）：** 我们 0 运维；OpenRig ~0.5 人天安装 + 偶发 daemon 故障；DBOS ~0.5 人天（建库/迁移）；Temporal ~2 人天（集群/库/升级）。

### A3. 契约即审计，且验收规则机器可判

- **机制：** `ROUND-PLAN.md`（开工前声明 ≤3 目标/文件边界/测试命令/NOT-DOING）→ `VERDICT.md`（三值决策 + 理由 + 未完成项）→ `DONE`；缺一即未完成，supervisor 直接 nudge。
- **竞品缺口：**
  - durable engine 的审计是**事件历史**（Temporal）或 **run 日志/仪表盘**（Prefect/Trigger.dev）：完整、机器可读，但**人读不了**，也无法回答"这一轮他原本打算做什么、什么没做"。
  - coding agent 的审计是 **transcript**：全、但非结构化，且随会话消失（Claude Code 有 cleanupPeriodDays 默认 30 天，✅）。
  - OpenRig 的 proof + reviewer 签收（✅）是**唯一机制上等价**的，但 proof 由 agent 自己 `rig proof add`，签收人多半是人——比我们多一层人工，少一层"独立验证进程"。
- **为什么竞品做起来贵：** 要把"计划成文 → 执行 → 自评 → 验收"做成硬门禁，就得改执行器协议（Claude Code 的 hooks 可以，但要写一堆 hook 脚本；✅ hooks 是生命周期钩子，能做确定性拦截）。我们把它写进了 prompt 契约 + supervisor 的文件检查，成本几乎为零。
- **买来的限制：** 契约靠模型自觉遵守，**没有内核强制**；一个不听话的 round 可以写完 DONE 却什么都没做（除了 verify 轮能抓一部分）。

### A4. 实现轮 / 验证轮分离，且验证者没有"作者偏见"

- **机制：** `plan.json` 里 `type: implement` 与 `type: verify` 是两轮；verify 轮自己复跑测试、核版本口径、审 diff，输入只有上一轮的 `VERDICT.md` + `reports/`。
- **竞品缺口：**
  - Devin / Cursor / Codex / Aider 的验证都是**同一上下文里的自检**（"我改了，我跑测试，我报告绿了"）。
  - Claude Code 的 dynamic workflow 能在一个 run 内做"对抗评审"（✅ 文档明确写到 agent 互相 adversarial review、`/deep-research` 对每条 claim 投票），但那是**同一 run、同一 runtime、同一 session**，不是新进程。
  - 真正"独立验证"的只有 CI（人写的断言）和人的 code review。
- **买来的限制：** 验证轮也是 LLM，也会漏；它只能验证"可复跑的东西"（测试、版本号、diff 大小），验证不了"设计对不对"。

### A5. 失败半径被三重限制住

- **机制：** 单轮 ≤3 目标 + 硬超时 7200s + nudge ≤6 → `BLOCKED`；`PAUSED`/`STOP`/`LOOPS-DONE`/`LOOPS-STOPPED` 四个标记文件让人随时刹车。
- **竞品缺口：**
  - Temporal 的 retry policy 针对**异常**（activity 抛错/超时），不针对"agent 跑偏但没报错"。
  - Claude Code workflow 有 stall 检测（6 次尝试后失败，✅ 文档），也是"没输出"而非"输出错了"。
  - Devin/Cursor 的失败表现为"PR 不对"，成本已经花完。
- **为什么竞品做起来贵：** "语义失败"需要外部判据（契约文件 + 目标上限），而它们的执行器不产出这种判据。

### A6. 执行器可替换（今天 dsh，明天 claude -p / codex exec）

- **机制：** 唯一耦合是命令行（`DSH_BIN`）+ stdin prompt + 文件契约；supervisor 不解析模型输出。
- **竞品缺口：** LangGraph/CrewAI/ADK 把编排写进 SDK（换执行器=改代码）；OpenRig 绑 tmux + Claude/Codex 的会话协议（✅ 混合 harness 是卖点，但仍在 tmux 层）；Claude Code workflow 绑 Claude Code 的 agent() 运行时。
- **买来的限制：** 也意味着我们**不能**利用执行器的结构化能力（tool 事件、token 计数、权限回调），只能看文件。

---

## 6. 短板（逐条给竞品解法）

### S1. 并行度 = 1

- **现象：** 单 supervisor、单 `loop-state.json`、无 flock；同一 `workflow/` 只能跑一条线。
- **后果：** 一轮 2 小时，10 轮就是 20 小时；机器闲着，人在等。
- **竞品怎么解：** Claude Code dynamic workflow 默认 16 并发（上限可调到 256）、单 run 1000 agents（✅）；OpenRig 多 seat + `rig grow` 动态加人（✅）；Temporal 并发只受 worker 数限制；Claude Squad 起 N 个 tmux 实例。
- **最小补法：** `plan.json` 加 `loop.parallel: n`；run 目录级 `flock`；状态从"单文件"改成"每 run 一个 state 文件 + 一个只读汇总"。**不要**在没有文件锁之前开并发——现在的代码会互相覆盖。

### S2. 状态 = 文件 + pid，没有事件日志，恢复粒度是"整轮"

- **现象：** 崩溃/被杀后，supervisor 只看 `DONE`/`VERDICT.md` 判定；不全就 nudge（整轮重跑）。`budget_sec` 不进执行路径；`loop-state.json` 可删（"safe to delete when idle"）。
- **后果：** 一轮跑了 100 分钟被杀，100 分钟白烧；重跑还会叠加已改一半的代码（nudge prompt 只说"不要重复完成的波次"，靠模型自觉）。
- **竞品怎么解：** Temporal 事件历史 + 确定性重放（✅）；Restate journal 跳过已完成步骤（✅）；DBOS 把 step checkpoint 进 Postgres（✅）；LangGraph checkpoint + pending writes（✅）；Inngest 每个 step 结果 memoize（✅）。
- **最小补法：** append-only `runs/<id>/events.jsonl`（`round_started` / `heartbeat` / `nudge` / `verdict` / `round_finished`）；supervisor 启动时重放事件恢复，而不是信 `loop-state.json`；再加一个"轮内切片"约定（`STATUS-Round-1.md` 已有一行一切片的雏形，✅ ROUND-SPEC 要求）让重跑能从最后一个切片开始。

### S3. 可观测性 = 日志文件 + `--status`

- **现象：** 三个日志文件 + `--list/--status` 文本；没有 trace、没有指标、没有 UI、没有告警（只有 `BLOCKED` 文件）。
- **后果：** "现在跑到哪、花了多少、为什么慢"要 `tail` 三个文件；出了问题只能翻 `workflow/logs/`。
- **竞品怎么解：** Temporal Web UI（事件历史可视化）；LangSmith/LangGraph Studio（trace + 时间旅行）；Trigger.dev/Prefect/Dagster 仪表盘；OpenRig TUI（`rig ps`/`rig capture`/`rig usage top`，✅）。
- **最小补法：** `--status --json` 输出机读状态；每轮结束生成一段固定格式的 `summary`（耗时/nudge 次数/diffstat/token 估算/VERDICT）；一个静态 HTML 或 Markdown 汇总页（不用前端框架）。**不要**做实时大屏——单人工作站不需要，做了也没人看。

### S4. 隔离强度不足（进程级、无容器/VM）

- **现象：** 同机同用户、共享工作区、`DSH_PERMISSION_MODE=danger-full-access`（README 明确）；边界靠 `ROUND-SPEC.md` 的"不 push / 不发布 / 不碰用户服务"。
- **后果：** 不可信代码、第三方 PR、多租户直接出局；一次 `rm -rf` 或 `git push --force` 就可能越界（契约是建议，不是内核）。
- **竞品怎么解：** Codex CLI 的 bubblewrap + seccomp + namespace（✅ 仓库文档：`/` 只读、写根白名单、`.git` 保护、禁 `io_uring`）；container-use 一 agent 一容器一分支（✅）；OpenHands Docker runtime（◐）；Cursor/Devin 云 VM（○）；Windmill nsjail（◐）。
- **最小补法：** 不要自己写沙箱。两个低成本选项：(a) 把 worker 的 cwd 换成 `git worktree`（隔离工作树，仍是同机）；(b) 需要真隔离时把 worker 命令换成 `container-use`/`codex exec --sandbox workspace-write`，supervisor 只改一行 `DSH_BIN` 式的配置。

### S5. 成本核算缺失

- **现象：** `budget_sec` 是时间预算，不是钱；token/美元只散落在每轮 `dsh` 的 NDJSON 日志里，supervisor 不解析（明确设计如此）。
- **后果：** 一个 loop 跑完才知道花了多少；没有熔断，"跑飞"的轮会一直烧到 2 小时硬超时。
- **竞品怎么解：** OpenRig `rig usage top --window 2d` 按 token/小时排名 + 显示 Claude 限额（✅）；Claude Code `/cost` 与 usage limit 自动暂停（✅ workflow 在限额处暂停并等重置）；Temporal 本身不管钱，但 activity 可自带计量。
- **最小补法：** 解析 `--json` 输出里的 usage 字段（只读不依赖），写 `runs/<id>/cost.json`；加 `max_tokens_per_round`，超限先写 `VERDICT.md` 再退出（优雅降级，不是硬杀）。

### S6. 计划编写的人工成本全在人身上

- **现象：** `plan.json` 的 loop/round 拆分、`goal`、`inputs`、`ROUND-SPEC.md` 的硬边界，全靠人写；写错一轮，后面全歪。
- **后果：** 新人上手门槛高；"想到什么写什么"会导致轮与轮之间输入不闭合（`inputs` 指错路径，下一轮从空开始）。
- **竞品怎么解：** Claude Code 让 Claude 自己写 workflow 脚本（✅ `ultracode` 关键字/`/effort ultracode`，脚本可保存为 `/命令` 复用）；OpenRig 让 orchestrator agent 拆任务（✅ workflow spec + 每步一个 task）；Devin 自己 plan（○）。
- **最小补法：** 提供一个 `--plan-from <brief.md>` 的**辅助**命令：把 brief 交给一个 headless 会话产出 `plan.json` 草稿 + 校验（inputs 路径存在、round 数 ≤N、每轮有 verify 或测试命令），**人只做 review**。注意：这是"生成草稿"，不是"替你决定目标"。

### S7. 重试语义粗糙：nudge ≠ 续跑

- **现象：** nudge 是"再起一个新 worker，prompt 里说别重复已完成的部分"；没有断点，没有"只重做失败的那一步"。
- **后果：** 同一个坑踩 6 次才 BLOCKED；每次都可能叠加改动，最后仓库处于半改状态，只能人工 `git checkout`。
- **竞品怎么解：** Temporal activity 级 retry + 幂等键；Inngest step 级 retry（失败 step 单独重试，✅ 文档明确"不重跑已成功的 step"）；DBOS step checkpoint；LangGraph 从最后一个 checkpoint 恢复。
- **最小补法：** 轮内引入"切片"（slice）作为最小重试单位：`STATUS-Round-1.md` 每行一个 slice + 一个 `slice-done` 标记；nudge 时 prompt 带上"已完成的 slice 列表 + 未完成列表"，并要求先 `git status` 自检再动手。这是契约层的改动，不需要新引擎。

### S8. 单机单人，没有协作面

- **现象：** 没有用户、没有权限、没有共享状态；`plan.json` 在本地磁盘。
- **后果：** 两个人不能同时用；远程看进度只能 SSH；给同事演示要打包整个 `workflow/`。
- **竞品怎么解：** OpenRig 多机 fleet + Slack 决策 + `rig bundle`（一个文件带走整支团队，✅）；Temporal namespaces + 多租户；Devin 团队席位。
- **最小补法：** 明确"这是单人工具"，用 `git` 共享 `workflow/` + `runs/`（把 runs 也提交，或至少提交 `VERDICT.md`/`reports/`）。**不要**自己做账号体系——那是另一个产品。

---

## 7. 选型决策表

| 场景 | 推荐 | 理由 | 明确不推荐 |
| --- | --- | --- | --- |
| **单机长跑**（自己仓库、无人值守、小时级切片） | **本方案** | 零 infra、轮边界拍板、失败半径小、契约可审计 | Temporal（为 3 个文件引入集群）；Devin（仓库要上云） |
| **需要并行 3~10 个任务**（同一台机器） | OpenRig / Claude Squad / Conductor；或本方案 + 槽位（S1） | 它们已经把"多座位 + worktree + 人看 diff"做完了 | 硬改本方案做并发（先补 flock 与状态分片） |
| **多机 / 团队 / 集中看板** | Temporal（编排）+ OpenRig（座位）；或 Claude Code agent teams + cloud sessions | 需要集中状态、并发、权限、跨机 | 本方案（文件契约在 NFS 上会打架） |
| **需要强隔离跑不可信代码** | container-use / Codex CLI（workspace-write）/ Cursor cloud agents / E2B 类沙箱 | 容器/内核沙箱/VM 级边界；我们只有进程边界 | 本方案 + "ROUND-SPEC 说不许"（那是建议） |
| **需要精确恢复**（不重跑副作用、从第 N 步续） | Temporal / Restate / DBOS / Inngest | 事件历史/journal/checkpoint 是它们的核心能力 | 本方案（只能整轮重跑） |
| **需要实时观测 / trace / 告警** | Temporal UI / LangSmith / Trigger.dev / OpenRig TUI | 现成的时间线、失败原因、重试记录 | 本方案（`tail` 日志） |
| **需要审计合规**（谁在何时改了什么、可回放） | Temporal（事件历史 + 归档）或 Git 平台审计日志；小规模可用本方案 + 签名/保留策略 | 合规要的是不可篡改的完整记录，不是 Markdown | 本方案裸用（`reports/` 可被 agent 改写） |
| **需要几十~几百 agent 扇出**（审计/迁移/研究） | Claude Code dynamic workflows（16 并发、1000 agents/run、可 resume） | 脚本化 fan-out + 现成 runtime | 本方案（串行，一轮一个） |
| **需要频繁人机来回**（每步批准/改方向） | LangGraph interrupt / OpenRig decision tasks / ChatGPT agent 接管 | 它们的 UI 与协议就是为"随时打断"设计的 | 本方案（轮内不打扰是设计，不是缺陷） |
| **交付物是 PR 而不是本机文件** | Devin / Cursor / Copilot coding agent / Factory | 云端 branch + PR + 审阅流 | 本方案（本机 git，不 push 是硬边界） |

**什么时候该换（触发条件，命中两条就动手）：**

1. 单轮经常撞 2 小时硬超时 → 先拆轮；拆不动说明"轮"这个粒度不适用，换 step 级引擎。
2. 需要第二台机器参与 → 文件契约失效，换集中状态（Temporal/DBOS）。
3. 要把 agent 权限交出去（不可信代码/第三方） → 换容器或 VM，不要试图用文档约束。
4. 需要 exactly-once 副作用或 step 级重试 → 换 Temporal/Restate/DBOS。
5. 需要别人（同事/客户）用、要看板 → 换有 UI/多租户的。
6. **nudge 率 > 30%** → 这不是引擎问题，是契约/prompt 问题：先修 `ROUND-SPEC.md` 与 `goal` 写法，别换工具。

---

## 8. 产品化建议

> 前提判断：这套东西的价值不在"又一个编排引擎"，而在"**用最低基础设施成本，给长跑 agent 一个可审计的轮边界**"。产品化要放大这一点，不要把它扩成 Temporal。

### 8.1 最小三件事（按投入产出排序）

**① 轮级状态机 + 事件日志 + `--resume`（1~2 天）**

- 做什么：`runs/<id>/events.jsonl`（append-only）；supervisor 启动时重放事件而非信 `loop-state.json`；`--resume` 只跑未完成轮；`budget_sec` 真正进入执行路径（每轮独立超时）。
- 为什么排第一：它同时修掉 S2（恢复粒度）、S5 的一半（可按轮计量）、S7 的一半（重试有据可依），且不引入任何外部依赖。
- 完成判据：`kill -9` supervisor 后重启，**不重跑任何 DONE 轮**；当前轮能从 `worker-result.json` 或最后一个 slice 续；`plan.json` 里 7200 vs 3600 的两轮真的按各自预算被杀。

**② 并发槽位 + 目录所有权（2~3 天）**

- 做什么：`plan.json` 的 `loop.parallel: n`；每个 run 目录一把 `flock`；状态按 run 分片，supervisor 只维护"下一轮该起谁"的只读视图；日志按 run 分流。
- 为什么排第二：这是从"一条流水线"到"小规模流水线"的门槛，也是唯一能让单机利用率上去的改动。
- 完成判据：3 个 loop 并行 6 小时，无状态交叉写、无重复启动、`--status` 能看到每个槽位。

**③ 观测与成本最小面（2~3 天）**

- 做什么：`--status --json`；每轮 `summary.json`（耗时 / nudge 次数 / diffstat / token 与估算成本 / VERDICT）；`max_tokens_per_round` 熔断（超限先写 VERDICT 再退出）；一个静态 `report.md` 汇总所有轮。
- 为什么排第三：没有它，"这套东西靠不靠谱"永远只能靠感觉；有了它，才谈得上给别人用。
- 完成判据：一条命令回答"这 10 轮花了多少、哪轮最贵、为什么停、改了多少行"。

### 8.2 不做什么（避免重复造轮子）

| 不做 | 理由 | 需要时怎么办 |
| --- | --- | --- |
| 通用 DAG / 事件溯源引擎 | Temporal/Restate/DBOS 已经把重放、版本兼容、集群做到极致；我们的语义单位是"轮"，不是"节点" | 需要精确恢复时，把"轮"实现成 Temporal 的一个 activity（一次 agent 调用），别自己写引擎 |
| 容器 / VM 编排 | container-use、Codex sandbox、Cursor、E2B 已经覆盖；自建等于做基础设施公司 | 把 worker 命令换成它们的 CLI，supervisor 只认文件 |
| UI 大屏 / 多租户 / RBAC | 单人工作站不需要；做了就要养账号、权限、审计，产品重心跑偏 | 需要团队视图时接 OpenRig 或 Temporal UI |
| LLM 网关 / 路由 / 计费 | dsh 已经管模型与 key；自建会绑死模型、放大维护面 | 用环境变量 + 执行器自身的 provider 配置 |
| Agent 框架（工具层、子 agent、上下文压缩） | 这是 dsh / Claude Code / Codex 的战场，迭代速度我们跟不上 | 通过 prompt 契约与 CLI 参数使用它们的能力 |
| "自动写计划"（让 agent 决定 loop/round） | 目标拆分是人最有价值的判断；让 agent 写计划会掩盖"目标本来就不清楚" | 提供 `--plan-from brief` 生成**草稿**，人 review 后才跑 |

### 8.3 如果决定开源，90 天节奏

- 第 1~2 周：三件事做完；补 3 个真实项目的 30 轮跑测数据（nudge 率、单轮成本、VERDICT=ADJUST 比例、BLOCKED 率）。
- 第 3~6 周：把 `workflow/` 抽成可 `pip install` 的包（`loop-supervisor`），模板与 `ROUND-SPEC.md` 做成可覆盖的默认值；写一份 5 分钟 quickstart（含"一轮必须是可独立验证的切片"这条最重要的告诫）。
- 第 7~12 周：拿数据决定定位——如果 nudge 率 < 15% 且单轮成本可控，就开源为"长跑 agent 的轮边界"；如果 nudge 率居高不下，先别开源，问题在契约设计而不是工具。

---

## 9. 来源清单

> 抓取日期均为 **2026-10-25**。核对方式：**抓全文** = 本次实际读取页面/仓库内容；**页面存在** = 搜索结果或链接可达但未逐条读全文；**未验证** = 无一手来源，仅作线索。

| # | 来源 | URL | 核对方式 | 支撑结论 |
| --- | --- | --- | --- | --- |
| 1 | 本项目 `workflow/README-WORKFLOW.md` | `dist/openrig-local-0.1.4-share-20261025/workflow/README-WORKFLOW.md` | 抓全文（本地） | 机制摘要、6 次 nudge、180s 心跳、控制文件 |
| 2 | 本项目 `workflow/ROUND-SPEC.md` | 同上目录 | 抓全文（本地） | 契约内容、≤3 目标、硬边界 |
| 3 | 本项目 `workflow/loop_supervisor.py` | 同上目录 | 抓全文（本地） | `MAX_NUDGES=6`、`ROUND_LIMIT=7200`、无 flock、budget_sec 未进执行路径 |
| 4 | 本项目 `workflow/plan.json` | 同上目录 | 抓全文（本地） | loop/round 结构、verify 轮示例 |
| 5 | Temporal — Workflows（事件历史/重放） | https://docs.temporal.io/workflows | 抓全文 | 事件历史、确定性重放、Activity 结果复用 |
| 6 | Temporal — Tasks | https://docs.temporal.io/tasks | 页面存在 | worker 轮询 task queue |
| 7 | LangGraph — Persistence | https://docs.langchain.com/oss/python/langgraph/persistence.md | 抓全文 | checkpointer/store 分工、thread 级快照 |
| 8 | LangGraph — Checkpointers / Interrupts / Time travel | https://docs.langchain.com/oss/python/langgraph/checkpointers.md · https://docs.langchain.com/oss/python/langgraph/interrupts | 页面存在 | interrupt/resume、时间旅行 |
| 9 | Inngest — Steps | https://www.inngest.com/docs-markdown/learn/inngest-steps | 抓全文 | step memoize、sleep 不占算力、waitForEvent/waitForSignal |
| 10 | Inngest — Durable workflows | https://www.inngest.com/docs-markdown/durable-execution/durable-workflows | 页面存在 | 执行模型 |
| 11 | Restate — Key Concepts | https://docs.restate.dev/foundations/key-concepts.md | 抓全文 | journal、重放跳过已完成、Virtual Object 单写者、FaaS suspend、flow control |
| 12 | Restate — 文档索引 | https://docs.restate.dev/llms.txt | 抓全文 | 服务类型/部署形态/AI patterns |
| 13 | DBOS — 文档索引 | https://docs.dbos.dev/llms.txt | 抓全文 | Postgres system database checkpoint、队列、恢复、Conductor、DBOSify |
| 14 | DBOS — 架构 | https://docs.dbos.dev/architecture.md | 页面存在 | "durable workflows built on top of Postgres" |
| 15 | DBOS — 与 Temporal 对比 | https://docs.dbos.dev/explanations/comparing-temporal.md | 页面存在 | 定位差异 |
| 16 | Prefect — 文档 | https://docs.prefect.io | 页面存在 | flow/task、state、work pool |
| 17 | Dagster — 文档 | https://docs.dagster.io | 页面存在 | asset/partition/sensor |
| 18 | Trigger.dev — Human-in-the-loop | https://trigger.dev/human-in-the-loop-ai-agents | 页面存在 | waitpoint / 人工批准 |
| 19 | Trigger.dev — 文档 | https://trigger.dev/docs | 页面存在 | task run、queue、realtime |
| 20 | Windmill — 文档 | https://www.windmill.dev/docs | 页面存在 | Postgres 队列、worker、nsjail |
| 21 | CrewAI — Checkpointing | https://docs.crewai.com/v1.15.28/en/concepts/checkpointing | 页面存在 | Flow 持久化 |
| 22 | CrewAI — Flows | https://docs.crewai.com/v1.15.12/ko/concepts/flows | 页面存在 | `@start/@listen/@router` |
| 23 | OpenAI Agents SDK — 文档 | https://platform.openai.com/docs/guides/agents-sdk | 页面存在（站点 403，仅链接） | agents/handoffs/guardrails/sessions/tracing |
| 24 | DBOS — OpenAI Agents SDK 集成 | https://docs.dbos.dev/integrations/openai-agents.md | 页面存在 | SDK 本身不做持久化 |
| 25 | Google ADK — 文档 | https://adk.dev/ | 页面存在（经 DBOS 集成页引用） | 工作流 agent、Session/State |
| 26 | ADK + DBOS | https://docs.dbos.dev/integrations/google-adk.md | 页面存在 | ADK 需要外部 durable execution |
| 27 | AutoGen / AG2 | https://github.com/microsoft/autogen · https://github.com/ag2ai/ag2 | 页面存在 | actor 模型、社区分支 |
| 28 | Microsoft Agent Framework | https://learn.microsoft.com/agent-framework/ | 页面存在（学习模块） | AutoGen + Semantic Kernel 合并方向 |
| 29 | Claude Code — Subagents | https://code.claude.com/docs/en/sub-agents.md | 抓全文 | 独立上下文、工具白名单、20 并发、3 层嵌套、worktree 隔离、SendMessage/resume |
| 30 | Claude Code — Dynamic workflows | https://code.claude.com/docs/en/workflows.md | 抓全文 | JS 脚本编排、16 并发、1000 agents/run、可 resume、16 并发/4096 items、无 mid-run 输入、stall 6 次 |
| 31 | Claude Code — Hooks | https://code.claude.com/docs/en/hooks | 页面存在 | 生命周期确定性拦截 |
| 32 | Claude Code — Features overview | https://code.claude.com/docs/en/features-overview | 抓全文（截断） | background agents / agent teams / cloud 的产品面 |
| 33 | Codex CLI — README | https://raw.githubusercontent.com/openai/codex/main/README.md | 抓全文 | 本机 CLI、`codex exec`/app/cloud 区分 |
| 34 | Codex — Linux sandbox | https://raw.githubusercontent.com/openai/codex/main/codex-rs/linux-sandbox/README.md | 抓全文 | bubblewrap + seccomp + namespace、`/` 只读、写根白名单、`.git` 保护 |
| 35 | Codex — Sandbox & approvals | https://developers.openai.com/codex/security | **403 未抓取** | 审批模式细节（○） |
| 36 | OpenHands | https://github.com/OpenHands/OpenHands | 页面存在 | 事件流 + Docker runtime |
| 37 | Devin — 用量/计费 | https://docs.devin.ai/admin/billing/usage | 页面存在 | session/ACU 计费模型（细节 ○） |
| 38 | Cursor — Cloud Agents（二手说明） | https://stevekinney.com/courses/ai-development/cursor-background-agents | 页面存在 | 云 VM、分支、PR |
| 39 | Cursor — Cloud Agents（官方） | https://cursor.com/docs/cloud-agents | 页面存在 | 同上 |
| 40 | GitHub Copilot Workspace | https://githubnext.com/projects/copilot-workspace/ | 页面存在 | 项目仍在展示 |
| 41 | Copilot Workspace 退役（二手） | https://aiwiki.ai/wiki/copilot_workspace | 页面存在 | 2025-05 退役技术预览（○ 未核官方公告） |
| 42 | Copilot `@workspace` 讨论 | https://github.com/orgs/community/discussions/195273 | 页面存在 | 社区侧证据 |
| 43 | OpenRig — Features（0.7.0） | https://openrig.dev/features | 抓全文 | seat/queue/workflow/proof/decision/restore/fleet/usage |
| 44 | OpenRig — GitHub | https://github.com/mvschwarz/openrig | 页面存在 | Apache 2.0、自托管 |
| 45 | Claude Squad — README | https://raw.githubusercontent.com/smtg-ai/claude-squad/main/README.md | 抓全文 | tmux + worktree、auto-yes、diff 审阅 |
| 46 | container-use — README | https://raw.githubusercontent.com/dagger/container-use/main/README.md | 抓全文 | 一 agent 一容器一分支、MCP server、Dagger |
| 47 | Dagger — container-use 博客 | https://dagger.io/blog/agent-container-use/ | 页面存在 | 设计动机 |
| 48 | cmux — README | https://raw.githubusercontent.com/manaflow-ai/cmux/main/README.md | 抓全文 | workspace/pane、通知环、socket API、agent resume、Claude Code teams |
| 49 | Conductor — 并行会话 | https://www.conductor.build/docs/guides/parallel-agents/run-multiple-claude-code-sessions | 页面存在 | 多 Claude Code 会话并行 |
| 50 | Conductor — worktree | https://www.conductor.build/docs/guides/git-worktrees/run-claude-code-with-git-worktrees | 页面存在 | 每任务 worktree |
| 51 | Aider — 文档 | https://aider.chat/docs/ | 页面存在 | 自动 git commit、/test、watch |
| 52 | Manus — 官方 | https://manus.im | 页面存在 | 云 VM + 多 agent（细节 ○） |
| 53 | Manus 概览（二手） | https://createaiagent.net/tools/manus/ | 页面存在 | 定位（○） |
| 54 | ChatGPT agent（OpenAI） | https://openai.com/index/introducing-chatgpt-agent/ | 页面存在 | 虚拟计算机、确认机制（○ 版本） |
| 55 | Google Jules | https://jules.google | 页面存在 | 异步编码 agent、云 VM（○ 版本） |
| 56 | Google Antigravity | https://antigravity.google | 页面存在 | agent-first IDE（○ 版本） |
| 57 | agent-farm（两个同名项目） | https://github.com/agentic-dev-io/agent-farm · https://github.com/BossX429/agent-farm | 页面存在 | 定位互相矛盾，低信号（○） |

---

## 10. 不确定性（别拿这份文档做合同级决策）

1. **商业产品的版本/定价/上限**（Devin ACU、Manus credits、Cursor 并发数、Factory/Amp 的能力边界）只核对到"页面存在"，标 ○。采购前必须重新查官方定价页。
2. **Copilot Workspace 的退役**只有二手来源（aiwiki + 社区讨论），未拿到 GitHub 官方公告原文；标 ◐。这不影响结论——它即使活着，也是"云 + PR"形态，不在我们的选择集里。
3. **Codex 的审批模式细节**（`untrusted/on-request/never` 的确切语义与默认值）因 `developers.openai.com` 403 未核对，正文只写了能从仓库确认的沙箱部分。
4. **OpenHands 当前架构**（v0/v1、事件流与 runtime 的具体实现）未逐条核对，按公开资料描述，标 ◐。
5. **本文对"我们"的描述**以 `dist/openrig-local-0.1.4-share-20261025/workflow/` 的分享版为准；如果生产环境另有 `wf.py` 之类脚手架，`budget_sec`、git 提交、并发这三处的结论需要按实际代码复核。
