[English](OPENRIG-WORKFLOW-GUIDE.md) | **简体中文**

# OpenRig + workflow — 完整指引

这是 OpenRig 与 workflow-group / SCTG 控制面配合使用的统一入口。写它的原因很
简单：同一批词在不同层含义不同，而 LLM 很容易把它们混在一起。

## 0. 先记住五个硬区分

| 不要这样说 | 应该说 |
|---|---|
| “OpenRig 就是 SCTG” | SCTG 是协议/kit；OpenRig 是执行面；workflow-group 是控制面。 |
| “workflow run 会把活干完” | `rig workflow run` 只负责实例化和跟随；具体工作由 seat 完成并关闭 packet。 |
| “rig send 就是自动流程” | `rig send` 是人工/调试路径；单线自动流程是 `rig workflow run`。 |
| “step 就是 round” | **step** 是 OpenRig 引擎单位；**round** 是 PMO -> TDO -> QA -> MAIN 的一轮。 |
| “validate/plan 通过就是 E2E 通过” | `workflow validate` 和 `rig up --plan` 只验证 spec，不证明模型执行成功。 |

只记一句话：**round 属于 workflow-group；step 和 queue packet 属于 OpenRig。**

> 常见用户误读和“什么时候该问”的清单见 [`LLM-MISREAD-QUICKREF.zh-CN.md`](LLM-MISREAD-QUICKREF.zh-CN.md)。

## 0.1 怎么用一句话要求

用带意图的短句。只说“使用 OpenRig”太容易歧义——它可能被理解成“建个 rig”、
“开个 seat”或“跑 workflow”。

| 你想表达 | 简短说法 | 应理解成 |
|---|---|---|
| 用 OpenRig 一条命令自动跑完 | **“用 OpenRig 跑工作流。”** | render -> validate -> `rig workflow run` |
| 完整 SCTG 控制面 + OpenRig 执行面 | **“用 OpenRig 执行 SCTG 工作流，单线跑。”** | workflow-group 管目标/决策；OpenRig 管 seat/queue/workflow |
| 只跑 SCTG 多轮，不启动 OpenRig | **“跑 SCTG 多轮。”** | `wf.py new-run` / `new-round` |
| 手动开 seat 调试 | **“OpenRig 手动调试。”** | `rig up` + `rig send` + queue 检查 |
| 只检查 spec / 启动计划 | **“OpenRig 预检。”** | `workflow validate` / `rig up --plan` |

默认建议：**“用 OpenRig 跑工作流。”**  
最精确：**“用 OpenRig 执行 SCTG 工作流，单线跑。”**

### 澄清门：只在开始前问一次，开始后不再发问

针对完整的多轮自动流程，提问只允许发生在 run 开始之前。开始前做一次合并澄清，
覆盖：层级（SCTG/workflow-group/OpenRig）、计数单位（round vs step）、
输出/验收、不可逆动作、预算/超时。优先给 1–3 个具体 A/B/C 问题。

自动流程开始后：

- 不再向用户提问；
- 低风险歧义用文档默认值，把假设记进 `DECISIONS.md` / `STATUS`；
- 真被阻塞时写 `BLOCKED` / `NEED_MAIN`，继续能做的工作；
- 下一步是未授权的不可逆动作时，停下来写 blocker。

提问预算：**开始前一次合并澄清，开始后 0 个问题。**

## 1. 一页决策表

| 你想做什么 | 用什么 | 入口 |
|---|---|---|
| 只做规划/审阅/写文档 | local-only | `python3 scripts/wf.py new-run ...` |
| 跑 10+ 轮控制面循环 | workflow-group | `wf.py new-run` -> `append-status` -> `state` -> `new-round` |
| 一条命令跑完一个声明式 OpenRig workflow | hybrid one-line | `rig workflow run <spec> --rig <rig> ...` |
| 调试卡住的 workflow | hybrid debug | `rig workflow show/trace`、`rig queue list` |
| 给 seat 发一条人工消息 | 仅调试 | `rig send <seat> "..."` |
| 复用已停止的 team | attached | `rig up <rig> --existing` |

## 2. 三层模型

```text
SCTG 协议 / kit
  card -> submission -> gate -> decision -> ledger
  包：sctg-kit/

workflow-group 控制面
  PROJECT / SPEC / DECISIONS / STATUS / ISSUES
  roles: MAIN, PMO, TDO, QA, SAFETY
  一轮 = PMO 计划 -> TDO 执行 -> QA 复核 -> MAIN 拍板

OpenRig 执行面
  rig / seats / queue qitems / workflow instance / steps / transcripts
  一个 step = 一个由 actor 角色处理的 workflow packet
```

`OPENRIG-BRIDGE.json` 是控制面和执行面之间唯一的映射，包含 run id、rig、
workflow id、seat map、OpenRig home、daemon port。

## 3. LLM 最容易混淆的术语

| 术语 | 含义 |
|---|---|
| **Rig** | 一个 live team 拓扑：pods、seats、edges。 |
| **Seat** | rig 里的一个 agent 身份（`main-analyst@my-rig`）。 |
| **Qitem / packet** | 投递给 seat 的一条队列项。 |
| **Workflow instance** | 一次 workflow spec 运行；有 frontier 和 step trail。 |
| **Step** | workflow spec 里声明的单元（`audit`、`plan`、`qa`）。 |
| **Round** | workflow-group 的一轮，写 STATUS/DECISIONS。 |
| **Closure** | seat 报告 packet 结果（`done`、`failed`、`handoff` 等）。 |
| **Bridge** | `OPENRIG-BRIDGE.json`，控制面事实到执行状态的映射。 |

### Step 与 round

```text
12 steps:  一个 workflow instance 里声明 12 个 step
12 rounds: workflow-group 里 12 个 PMO -> TDO -> QA -> MAIN 循环
```

两者可以组合，但计数含义不同，不能混着说。

## 4. 路径 A — 12 轮控制面

```bash
python3 scripts/wf.py new-run case-001 \
  --template templates/specialized/openrig-workflow-master \
  --goal "Harden a small service" \
  --project-root "$PWD" \
  --scope 'runs/case-001/**' \
  --tdo 1

# 第 1 轮
python3 scripts/wf.py append-status case-001 --agent tdo-a1 --ws WS-1 \
  --action "R1: implement" --evidence "evidence/r1.log" --no-commit
python3 scripts/wf.py state case-001 STATUS qa-pending --by main
python3 scripts/wf.py state case-001 STATUS qa-done --by qa
python3 scripts/wf.py new-round case-001

# ... 重复 12 次 ...
```

三个完整 12 轮导出见 `examples/round-cases/`。

## 5. 路径 B — 单线 OpenRig workflow

### 5.1 准备带目标 seat 的 rig

```yaml
# /tmp/one-line.rig.yaml
version: "0.2"
name: "one-line-audit"
pods:
  - id: main
    label: Main
    members:
      - id: analyst
        agent_ref: "path:<OPENRIG_REPO>/packages/daemon/specs/agents/research/analyst"
        profile: default
        runtime: opencode
        cwd: "<project-root>"
        model: "deepseek/deepseek-flash"
    edges: []
edges: []
```

```bash
rig up /tmp/one-line.rig.yaml \
  --cwd "<project-root>" --non-interruptive --yes --json
```

### 5.2 声明单步 workflow

```yaml
# /tmp/one-line.workflow.yaml
workflow:
  id: one-line-audit
  version: 1
  objective: Audit the repository and write one report.
  target:
    rig: one-line-audit
  entry:
    role: analyst
  exception_routing:
    orchestrator_role: analyst
  roles:
    analyst:
      preferred_targets: [main-analyst@one-line-audit]
  steps:
    - id: audit
      actor_role: analyst
      objective: >
        Read README.md and docs/INDEX.md. Write exactly one file
        reports/one-line-report.md with a verdict and five findings.
        Do not modify other files. Close the packet when done.
      allowed_exits: [done, failed]
  invariants:
    allowed_exits: [done, failed]
  loop_guards:
    max_hops: 3
```

### 5.3 验证并运行

```bash
rig workflow validate /tmp/one-line.workflow.yaml --json

rig workflow run /tmp/one-line.workflow.yaml \
  --root-objective "Audit the repository" \
  --created-by main-analyst@one-line-audit \
  --rig one-line-audit --json
```

退出码：

```text
0  workflow completed
3  workflow failed or aborted
1/2 transport/API error
```

### 5.4 查看 trail

```bash
rig workflow show <instance-id> --json
rig workflow trace <instance-id> --json
rig ps --nodes --rig one-line-audit --json
```

## 6. 路径 C — 人工调试

只在需要检查 seat/packet 时使用。

```bash
rig send main-analyst@one-line-audit "Read reports/one-line-report.md and reply with a 5-line summary." --verify
rig queue list --all-rigs --limit 50
rig queue show <qitem-id>
rig workflow show <instance-id>
rig workflow trace <instance-id>
```

手动关闭 packet：

```bash
rig queue update <qitem-id> --state done --closure-reason no-follow-on
```

合法 closure reason 包括 `handed_off_to`、`blocked_on`、`denied`、`canceled`、
`no-follow-on`、`escalation`。关闭 packet 不等于接受工作结果。

## 7. Queue / packet 生命周期

```text
pending -> in-progress -> done
                     \-> blocked / handed off / canceled
```

典型流程：

1. `rig workflow run` 创建 entry packet；
2. seat 领取 packet（`pending -> in-progress`）；
3. seat 写证据并报告 exit（`done`、`failed`、`handoff`）；
4. 引擎投影下一步 packet，或结束实例。

如果 workflow 看起来 idle 但没完成，检查：

```bash
rig queue list --all-rigs --limit 50
rig workflow show <instance-id>
rig ps --nodes --rig <rig>
```

## 8. Preflight、bridge、teardown

```bash
python3 scripts/openrig_preflight.py --json --no-monitor
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-001 --project-root /tmp/demo-project \
  --output-dir runs/demo-001/openrig
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor --run-dir runs/demo-001
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py status --run-dir runs/demo-001
```

硬规则：

- rig 名 / workflow id 唯一；
- 独立 `OPENRIG_HOME` 和 daemon 端口；
- 不直接改 SQLite/queue；
- 先归档再 `rig down` / `rig daemon stop`；
- 不得把 local-only 通过写成 hybrid E2E 通过。

### Seat 启动副作用

OpenRig seat 启动可能向 `AGENTS.md` 注入 managed block，并创建
`.agents/skills/`。公开仓库要删除或明确记录：

```bash
git checkout -- AGENTS.md
rm -rf .agents
echo '.agents/' >> .gitignore
```

## 9. 内存与并发安全

Agent seat 的真实内存可能远超可见 RSS，因为 systemd scope 会把大文件读取的
page cache 也算进去。`ulimit -v` 不够。

```text
MemoryHigh=5G  （软阈值，位于 MemoryMax 内）
MemoryMax=6G   （硬 RAM 上限）
MemorySwapMax=1G（独立 swap）
=> 约 6G RAM + 1G swap，不是 12G
```

推荐配置：

```text
first seat:  heavy  5G high / 6G max / 1G swap
second seat: light  3.5G high / 4.5G max / 0.5G swap
global:             8G high / 9G max / 2G swap
```

使用 `examples/memory-limits/` 和用户 slice（`dsh.slice`）限制并行 seat 总和。
不要让 seat 跑 broad `find /`、扫 `$HOME`、或无界捕获输出。

## 10. 故障排查矩阵

| 现象 | 可能原因 | 检查/修复 |
|---|---|---|
| Agent 一直调 shell、不写报告 | prompt 太宽、无停止条件 | 用单步 workflow，明确一个输出文件和工具调用上限 |
| `workflow run` 一直 active，但 seat idle | packet 等待 claim/closure | `rig queue list`、`rig workflow show` |
| `no_activity_signal` | activity hook/relay 未配置 | 只是 advisory；用 `rig capture` 和 queue 状态核实 |
| `workflow validate` 绿了但没执行 | validate 只验 spec | 用 `rig workflow run` 或 `instantiate` |
| workflow completed 但没有报告 | seat 关了 packet 但没写文件 | 看 `rig workflow trace` 和工作区 |
| 仓库里出现 `.agents/` | seat 启动注入 | 恢复 `AGENTS.md`，删 `.agents/`，gitignore |
| 整机 OOM / memory scope 很大 | broad scan 放大 page cache | 加 cgroup 限制；删 broad scan |
| `rig send` 返回 advisory | 无 activity hook / 未知 sender | 用 seat shell 签名发送，或改用 `rig workflow run` |

## 11. 发布与脱敏

发布前：

```bash
make check
make doc
make test
make demo
make bench-smoke
```

`make check` 包含：

```text
scripts/check_repo.py
scripts/check_content.py
scripts/check_sanitization.py
compileall
```

如果旧 revision 含个人路径，发布前把公开 history 重写为干净单提交；删除旧
tag/release，只发布干净 tag。

## 12. 命令速查

```text
控制面：
  wf.py new-run / new-round / append-status / state / doctor
  wf_close_lint.py --run <run-id>

OpenRig 单线：
  rig workflow validate <spec>
  rig workflow run <spec> --root-objective ... --created-by ... --rig ...
  rig workflow show/trace <instance-id>

OpenRig 调试：
  rig up <rig.yaml> --plan
  rig up <rig.yaml> --non-interruptive --yes
  rig send <seat> "..."
  rig queue list / show / update
  rig ps --nodes --rig <rig>
  rig capture / transcript <seat>

收口：
  archive -> rig workflow abort/close -> rig down -> rig daemon stop
```

## 13. 本指南不声称什么

- 不声称真实 5-seat E2E 通过；
- 不声称模型质量或 benchmark 结果；
- 不把 `rig workflow run` 当成角色合同的替代；目标、决策、验收仍归控制面。
