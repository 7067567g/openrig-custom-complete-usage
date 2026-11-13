# 入口与调用 — openrig-workflow-master v1.2

> 目的：回答两个问题：**从哪里进入？进入后调用哪一层？**
> 本文件是路由说明，不替代 `SPEC.md`（双平面契约）、`PROJECT.md`（每个 run 的目标）与 `ARCHITECTURE.md`（详细设计）。

## 0. 一句话判断

- 只想确认母版/文档是否可发布 → **只读核对**；
- 只做规划、拆包、QA 文档闭环，不需要真实多 seat → **workflow-group local-only**；
- 需要 OpenRig 的真实 queue / seat / workflow / transcript / resume → **hybrid 双平面**；
- 已经有 run 正在跑 → **先接续/诊断，不要新建同名 run**；
- 要给 `$PROJECT_REPO` 开项目票 → **不要在本仓 GitHub 开票，也不要直接加 `.ticket-store/tickets/` 文件**；先按项目 `tickets-as-code` 的 declaration 规则规划。

## 1. 入口选择表

| 你的目标 | 入口 | 是否启动 OpenRig | 首选命令/文档 |
| --- | --- | --- | --- |
| 核对母版版本、契约、测试、baseline | 母版目录 | 否 | `VERSION`、`pytest workflow-group/tests -q`、`sha256sum -c BASELINE-post.sha256` |
| 只做控制面规划/审阅/文档收口 | `workflow-group/runs/<run-id>/` | 否 | `wf.py new-run` + `wf.py brief` |
| 让 PMO/TDO/QA 在真实 seat 上执行 | 本文件 + `workflow.yaml` | 是 | `render_master.py` → `rig up` → `rig workflow validate/instantiate` |
| 接续一个已有 run | 已有 run 的 `PROJECT.md` / bridge | 视情况 | `wf.py doctor`、`openrig_bridge.py doctor/status`、`rig up --existing` |
| 项目侧立项/开票 | `$PROJECT_REPO/.ticket-store/` | 否 | 先读 `.ticket-store/docs/ticket-policy.md`，规划 declaration |
| 跨仓找入口 | 本文件 + KB 入口票 | 否 | KB 地图票（`wayfinder:map`）与项目 map 互链 |

## 2. 控制面调用链

```text
人 / MAIN
  → workflow-group/AGENTS.md + roles/common-contract.md
  → runs/<run-id>/{SPEC,PROJECT,DECISIONS,STATUS,ISSUES}
  → PMO 写计划、拆 WS、投 packet
  → TDO 执行并写证据指针
  → QA 独立复核并登记 ISSUES
  → MAIN 读 PROJECT §6 + QA 结论，写 DECISIONS，关轮/关 run
```

权威边界：

- 目标、范围、验收、决策、最终结论：**workflow-group 控制面**；
- packet/claim/blocked/transcript/session：**OpenRig 执行面**；
- 两者只通过 `OPENRIG-BRIDGE.json` + evidence 路径映射，不互相复制全量状态。

## 3. 执行面调用链（hybrid）

```text
render_master.py
  → OPENRIG-BRIDGE.json + rig.yaml + workflow.yaml
  → OPENRIG_HOME + rig daemon start
  → rig up --plan
  → rig up（真实 5 seats）
  → rig ps 5/5 ready
  → rig workflow validate
  → rig workflow instantiate
  → entry packet 到 PMO
  → plan → implement_opencode / implement_dsh
  → qa_opencode / qa_dsh → qa_join → close_round
  → rig down → daemon stop → 清理核验
```

硬门：

- 未 `5/5 ready` 不 instantiate；
- 未 `workflow validate` rc=0 不 instantiate；
- 不用 fresh seat 冒充 resume；
- 进入收口后，teardown 是**最后动作**；teardown 前不能再需要 live rig 的验证。
- **强制归档先于 teardown**：必须先完成项目内 OpenRig 归档并通过 `MANIFEST.json.archiveStatus == "COMPLETE"`；详见 §3.1。


### 3.1 收口前强制归档（不可跳过）

**任何 hybrid OpenRig run 在 `rig down`、`rig daemon stop`、删除 `OPENRIG_HOME` 之前，必须先归档；归档不完整不得 teardown。**

默认归档位置（项目内，随工作区镜像传输）：

```text
$OPENRIG_REPO/var/openrig-archive/
  machines/<machine>/runs/<run-id>/{MANIFEST.json,RECORD.md,run/,home/}
  machines/<machine>/sessions/<session-id>/
```

标准命令：

```bash
cd $OPENRIG_REPO
python3 scripts/openrig-archive.py \
  --run-dir $REPO_ROOT/runs/<run-id> \
  --openrig-home /tmp/openrig-workflow-<run-id> \
  --session-id <control-session-id> \
  --session-id <seat-session-id>
```

硬判据：

- `MANIFEST.json.archiveStatus == "COMPLETE"`；
- `required.runSnapshot / sessionSnapshots / transcriptCapture / openrigState / homeSnapshot` 全部为 `true`；
- `RECORD.md` 写明 run、会话、transcript、home、恢复方法；
- run 的 `STATUS`/`DECISIONS` 回填 archive 路径与 sha256；
- 历史 run 的 live home 已丢失时，只能加 `--allow-incomplete` 补档，并明确记为历史缺口，不能冒充 COMPLETE。

详细规则：`$OPENRIG_REPO/var/openrig-archive/MANDATORY.md`。

## 4. 三种实际入口

### A. 只读核对母版

```bash
cd $REPO_ROOT/templates/specialized/openrig-workflow-master
cat VERSION
cd $REPO_ROOT
python3 -m pytest tests -q
cd templates/specialized/openrig-workflow-master
sha256sum -c BASELINE-post.sha256
```

不写 run，不启动 daemon。

### B. local-only（只跑工作流文档面）

```bash
cd $REPO_ROOT
python3 scripts/wf.py new-run <run-id> \
  --template templates/specialized/openrig-workflow-master \
  --goal-file kickoff/<goal>.txt \
  --project-root $REPO_ROOT \
  --scope 'workflow-group/runs/<run-id>/**' \
  --tdo 2
python3 scripts/wf.py brief --role pmo --run <run-id>
python3 scripts/wf.py doctor <run-id>
```

适合：选题、计划、文档重构、静态测试；**不得**把 local-only 写成真实 E2E 通过。

### C. hybrid（真实多 seat 执行）

```bash
cd $REPO_ROOT

# 1) 控制面 run
python3 scripts/wf.py new-run <run-id> \
  --template templates/specialized/openrig-workflow-master \
  --goal-file kickoff/<goal>.txt \
  --project-root $REPO_ROOT \
  --scope 'runs/<run-id>/**；<target>/**' \
  --tdo 2

# 2) 渲染 bundle
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id <run-id> \
  --project-root $REPO_ROOT \
  --output-dir runs/<run-id>/openrig \
  --openrig-cli 'node $OPENRIG_REPO/packages/cli/dist/bin-wrapper.js' \
  --openrig-home /tmp/openrig-workflow-<run-id> \
  --daemon-port <port>

# 3) bridge 预检
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor \
  --run-dir runs/<run-id>

# 4) 启动（把 <RIG_CLI> 替换为 bridge 里的 openrigCli 命令）
export OPENRIG_HOME=/tmp/openrig-workflow-<run-id>
<RIG_CLI> daemon start --no-kernel --port <port>
<RIG_CLI> up runs/<run-id>/openrig/rig.yaml \
  --cwd $REPO_ROOT \
  --non-interruptive --yes --json
<RIG_CLI> workflow validate runs/<run-id>/openrig/workflow.yaml --json
<RIG_CLI> workflow instantiate runs/<run-id>/openrig/workflow.yaml \
  --root-objective 'Execute <run-id>' \
  --created-by control-main@openrig-<run-id> --json
```

### D. 接续已有 run

```bash
python3 scripts/wf.py doctor <run-id>
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor --run-dir runs/<run-id>
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py status --run-dir runs/<run-id>
```

先读 bridge 的 `openrigHome`/`daemonPort`/`workflowId`，再决定 `rig up --existing` 或重新渲染；**不要**新建同名 run、不要复用别人的 `OPENRIG_HOME`。

## 5. 外部票系统（可选）

OpenRig 执行面不绑定某个特定的 issue tracker。使用本仓库时，请把你自己的
项目票系统放在外部，并通过 `$PROJECT_REPO` 之类的占位符引用：

```text
$PROJECT_REPO/
  declarations/<project>.toml
  tickets/NNNN.toml
  docs/ticket-policy.md
```

硬规则：

1. 不在本仓直接写真实项目票号或私有链接；
2. 票的创建、声明、门禁遵循项目自己的 policy；
3. 项目票系统与 workflow-group 的文档合同保持单向映射，不互相复制全量状态。
