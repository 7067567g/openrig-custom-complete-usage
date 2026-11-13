# OPENRIG AGENT PREFLIGHT — 启动任何新 run 前必读

> 给执行 OpenRig / workflow-group 的 AI 看的入口，不是给人看的欢迎页。
> 进入新 run 前先跑：`python3 scripts/openrig_preflight.py --json`
> 若你已经被委派为某个 seat，而工作区里没有这段 preflight，先要求主控注入或读本文件。

## 0. 30 秒硬检查（不合格就停）

1. **选型**：先查 `templates/baseline/REGISTRY.md` 选复合类型，再查 `templates/contracts/README.md` 选原子轮型；`SPEC.md §0` 必须写 `baseline:` 与 `contracts:`。
2. **唯一命名**：一个 run 一个唯一 rig 名、一个唯一 workflow id、一个隔离 `OPENRIG_HOME`/daemon 端口；禁止复用别的 run 的 seat/tmux。
3. **单一写者**：一个写权限目录/文件只能有一个 WS/seat 写；跨片依赖用波次，不靠并发写同一文件。
4. **先快照**：改任何 live 前必须有 pre 快照 + sha256 + 回滚脚本；项目不是 git 时快照就是唯一回滚介质。
5. **文档即接口**：workflow-group 只通过 `PROJECT / DECISIONS / STATUS / ISSUES` 交接；不要用聊天正文代替文档。
6. **不越权**：execution plane 不直接改 OpenRig SQLite/queue 表；control plane 不复制 queue 实时状态当验收结论。
7. **先归档后 teardown**：`MANIFEST.json.archiveStatus=COMPLETE` 之前不得 `rig down`、`daemon stop` 或删 `OPENRIG_HOME`。
8. **有停止条件**：必须有 `DONE` / `BLOCKED` 标记、心跳停止命令、回滚命令；不允许无限空转。

## 1. 双平面职责

```text
workflow-group（控制面）
  目标 / 决策 / 验收 / 证据 / 轮次
        ▲ OPENRIG-BRIDGE.json + evidence paths
        ▼
OpenRig（执行面）
  daemon / rig / seat / queue / workflow / transcript
```

- 控制面权威：目标、范围、验收判据、决策账本。
- 执行面权威：谁在跑、queue 状态、workflow frontier、transcript、seat liveness。
- 两者不互相抄状态；实时状态只查 OpenRig，目标与裁决只查 workflow-group。

## 2. 角色与默认编制

- `MAIN`：唯一决策、统一提交、关停；只写 `DECISIONS.md`。
- `PMO`：计划、分任务、收轮、上报；只写 `PROJECT.md`。
- `TDO`：按分片执行、写 `STATUS-Round-n.md`；只能写自己的产出物。
- `QA`：独立核查、写 `ISSUES.xlsx`；只报不改。
- `SAFETY`：仅安全关键 run 按需启用，只审 gate FAIL action，不与 TDO/QA 同身份。

默认 `PMO×1 + TDO×N + QA×1`；N 按“互不触碰文件的独立片”决定，不要为了并行而并行。

## 3. 一轮状态机

```text
S0 立项/建 run
 → S1 PMO plan-ready
 → S2 TDO 执行，逐条 STATUS
 → S3 QA 核查
 → S4 PMO 收轮 waiting-main
 → S5 MAIN 拍板 → new-round 或 closed
```

关键约束：

- `STATUS` 写入必须锁：`lock → append 1 条 → commit → unlock`。
- 状态迁移只由 `WORKFLOW.md §4.0` 指定角色执行，不手改状态行。
- 每条进度必须带可复现证据（命令、路径、hash、数字）。
- 分歧不落地：需要取舍就写 `PROJECT §6` 待拍板 + ISSUES，不自行顺手做掉。

## 4. OpenRig 运行注意事项

1. **daemon 必须脱离临时 shell**：用 `setsid` 或 `systemd-run --user` 启动 daemon；不要从会被回收的工具 shell 直接 `nohup` 起长期进程。
2. **seat 可能依赖 dsh-web**：shared-web DSH seat 是 3080 进程的子进程；不要直接 kill 其父进程。需要切换 3080 时用 detached `systemd-run --user` 脚本，并在脚本末尾 `rig up <rig> --existing` + `rig send` 恢复。
3. **resume 用 `rig up <rig> --existing`**；不要新建同名 rig 冒充 resume。
4. **queue 是唯一执行所有权**：`rig queue claim` 后才算 in-progress；workflow 前进用 `rig workflow project --exit ...`，不要直接关闭 queue 行。
5. **workflow 完成 ≠ 发布验收**：最终验收必须看 `FINAL.md` + 证据 + 独立复跑。
6. **heartbeat 只做唤醒，不做进度真值**：进度以 `STATE.md`/`STATUS` 为准；watchdog 只是定时唤醒。
7. **停止条件**：`DONE`/`BLOCKED` 后必须 `rig watchdog stop <jobId>`；不要让 periodic-reminder 永久空转。
8. **安全边界**：不把 API key、auth token、`.credentials.yaml` 内容写进 bridge、日志、报告或 qitem body。

## 5. 参考模板索引

| 类型 | 路径 | 何时用 |
| --- | --- | --- |
| 双平面母版 | `templates/specialized/openrig-workflow-master/` | workflow-group + OpenRig 混合编排、多 seat、可搬迁 bundle |
| 单用户治理实例 | `templates/specialized/<your-domain>/` | 单项可靠性/运维专项，单 seat + 心跳，先 staging 后 live |
| 微信桥产品重设计 | `templates/specialized/<your-domain>/` | 单窗口产品形态/交互重设计 |
| fix-wave | `templates/baseline/fix-wave/BASELINE.md` | 缺陷票批量修复，先红后绿、门禁化 |
| ops-hardening | `templates/baseline/ops-hardening/BASELINE.md` | 分发/同步/调度/入口可靠性加固 |
| refactor-decompose | `templates/baseline/refactor-decompose/BASELINE.md` | 先归属/冻结基线，再做行为不变重整 |
| product-redesign-live | `templates/baseline/product-redesign-live/BASELINE.md` | 反目标→设计→staging→live/回滚 |
| two-plane-orchestration | `templates/baseline/two-plane-orchestration/BASELINE.md` | 双权威、隔离 home/port、QA+join+有界回边 |
| 原子契约 | `templates/contracts/{strategy,research,diff,architecture,optimize,verify,audit}/` | 每轮 `ROUND-PLAN.md` 只声明一个 contract |

新增模板前先看 `templates/specialized/README.md`；不要直接把 baseline/contracts 当 `--template`。

## 6. 标准启动序列

```bash
cd $REPO_ROOT

# 1) 选模板并建 run
python3 scripts/wf.py new-run <run-id> \
  --template templates/specialized/<name> \
  --goal "..." --project-root <project> --scope '<paths>' --tdo <N>

# 2) 填 PROJECT §0–§5 / DECISIONS D-001，跑 doctor
python3 scripts/wf.py doctor <run-id>

# 3) 渲染 OpenRig bundle（若用双平面母版）
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id <run-id> --project-root <project> \
  --output-dir runs/<run-id>/openrig

# 4) 隔离 daemon + rig
export OPENRIG_HOME=/tmp/openrig-workflow-<run-id>
export OPENRIG_DSH_BIN=<shim 或 dsh>
rig daemon start --no-kernel --port <port>
rig up runs/<run-id>/openrig/rig.yaml --cwd <project> --non-interruptive --yes

# 5) 校验 + 实例化 workflow
rig workflow validate runs/<run-id>/openrig/workflow.yaml --json
rig workflow instantiate runs/<run-id>/openrig/workflow.yaml \
  --root-objective "..." --created-by <main>@<rig> --json
```

## 7. 监控台自动接入

新 run 启动后，用同一入口注册到只读监测台：

```bash
python3 scripts/openrig_preflight.py \
  --run-id <run-id> \
  --rig <rig> \
  --seat <member>@<rig> \
  --run-dir $REPO_ROOT/runs/<run-id> \
  --gov-dir <workspace> \
  --job <watchdog-job-id> \
  --workspace <workspace> \
  --json
```

它会：

- 打印本 preflight 给 AI；
- 把注意事项注入 `<workspace>/AGENTS.md`（OpenRig seat 启动即可读到）；
- 写监测台 target 配置并启动 `openrig-monitor.service`；
- 输出 `http://127.0.0.1:3190`。

## 8. 完成定义

- `PROJECT §1` 全部判据满足；
- `STATUS` 无 open S1/S2，`ISSUES` 无未处理 S1/S2；
- `reports/FINAL.md` 有 G×证据×命令映射；
- `DONE` 存在，watchdog 已 stop；
- 先归档后 teardown，回滚命令可执行。
