# 入口与调用 — openrig-workflow-master v1.2

> 目的：回答两个问题：**从哪里进入？进入后调用哪一层？**
> 本文件是路由说明，不替代 `SPEC.md`（双平面契约）、`PROJECT.md`（每个 run 的目标）与 `ARCHITECTURE.md`（详细设计）。

## 0. 一句话判断

- 只想确认母版/文档是否可发布 → **只读核对**；
- 只做规划、拆包、QA 文档闭环，不需要真实多 seat → **workflow-group local-only**；
- 需要 OpenRig 的真实 queue / seat / workflow / transcript / resume → **hybrid 双平面**；
- 已经有 run 正在跑 → **先接续/诊断，不要新建同名 run**；
- 要给 `deepseek-项目` 开项目票 → **不要在本仓 GitHub 开票，也不要直接加 `.ticket-store/tickets/` 文件**；先按项目 `tickets-as-code` 的 declaration 规则规划。

## 1. 入口选择表

| 你的目标 | 入口 | 是否启动 OpenRig | 首选命令/文档 |
| --- | --- | --- | --- |
| 核对母版版本、契约、测试、baseline | 母版目录 | 否 | `VERSION`、`pytest workflow-group/tests -q`、`sha256sum -c BASELINE-post.sha256` |
| 只做控制面规划/审阅/文档收口 | `workflow-group/runs/<run-id>/` | 否 | `wf.py new-run` + `wf.py brief` |
| 让 PMO/TDO/QA 在真实 seat 上执行 | 本文件 + `workflow.yaml` | 是 | `render_master.py` → `rig up` → `rig workflow validate/instantiate` |
| 接续一个已有 run | 已有 run 的 `PROJECT.md` / bridge | 视情况 | `wf.py doctor`、`openrig_bridge.py doctor/status`、`rig up --existing` |
| 项目侧立项/开票 | `deepseek-项目/.ticket-store/` | 否 | 先读 `.ticket-store/docs/ticket-policy.md`，规划 declaration |
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

## 5. 票入口：KB 与项目是两套系统

### 5.1 KB 仓（本仓）

- 仓库：`7067567g/deepseek-knowledge-base`
- 跟踪器：GitHub Issues，读写走 deck 工具；
- 票模板：`docs/agents/issue-tracker.md`（标题 + 目标/依据/出口/不做/进度）；
- 分类标签：恰一枚 `cat:*`，工作流入口/仓库基建用 `cat:repo`；
- **当前入口图：** [#35](https://github.com/7067567g/deepseek-knowledge-base/issues/35)（`wayfinder:map`，保持 open）
  - #37：KB 入口文档与调用链落盘（已关闭，commit `d170b35`）
  - #36：`deepseek-项目` tickets-as-code 接入预研（open）
- 入口票保持 open，作为跨会话路由；子任务完成后再关子票，不急着关地图。

### 5.2 项目文件夹（`deepseek-项目`）

项目侧**不是**本仓的 GitHub issue 直开模式，而是 `tickets-as-code`：

```text
$OPENRIG_REPO/.ticket-store/
  declarations/<project>.toml   # map + content_tickets + terminal + whitelist
  tickets/NNNN.toml             # 每张票一个文件
  docs/ticket-policy.md         # 纪律
  scripts/ticket_plan.py        # 先规划 declaration
  scripts/ticket_new.py         # 按计划建票
  scripts/ticket_gate.py check  # 门禁
```

必须遵守：

1. **不能直接在 `tickets/` 新增一个白名单外的票号**；
2. 先 `ticket_plan.py` 规划 declaration（1 张 map + N 张 content + 1 张 terminal）；
3. 再按 plan 用 `ticket_new.py` 建票；
4. 修改后 `python3 scripts/ticket_gate.py check` 必须 exit 0；
5. 按项目纪律走 PR，不直接 push `main`。

OpenRig 的项目侧工作不应塞进 `deepseek-project-work` 的旧票号；推荐新开一个独立块（暂定名 `deepseek-project-openrig`），先在该块 map 中登记：
- KB 入口 map 票号/URL；
- 本项目路径 `10-openrig-deepseek/`；
- 与 KB `workflow-group/` 的职责边界；
- 何时从“预研”转“实施”。

该块尚未创建；在创建前由 KB #36 承接，不产生“预计外票号”。

项目侧已落地的入口块（`tickets-as-code`）：

- declaration：`deepseek-项目/.ticket-store/declarations/deepseek-project-openrig.toml`，`mode=active`，白名单 `[38,39,40,41]`；
- 项目 map：`tickets/0038.toml`（open）
- 内容票：`tickets/0039.toml`（项目侧入口与文档落位，open）、`tickets/0040.toml`（运行时验证与交付回填，open，`depends_on=[39]`）
- terminal：`tickets/0041.toml`（open，尚无预计外 item）
- 规划文档：`deepseek-项目/.ticket-store/docs/openrig-workflow-entry-plan.md`
- 现有项目 work map `tickets/0001.toml` 保持 open，并已加 KB #35/#36 指针；
- 项目票仓 PR：#1（建票/指针）、#2（declaration 激活）、#3（文档回写）均已合入；
- `ticket_gate.py check` = `Ticket Gate OK`。

项目票链接（tickets-as-code ID，不是 GitHub issue 号）：

- https://github.com/7067567g/deepseek-project-issues/blob/main/tickets/0038.toml
- https://github.com/7067567g/deepseek-project-issues/blob/main/tickets/0039.toml
- https://github.com/7067567g/deepseek-project-issues/blob/main/tickets/0040.toml
- https://github.com/7067567g/deepseek-project-issues/blob/main/tickets/0041.toml

## 6. 跨仓链接规则

- 记录 **canonical 票号 + URL + 仓库路径 + 最后一个 commit**；
- 不在两套跟踪器之间复制整张票正文；
- KB 票负责“工作流入口与调用逻辑”，项目票负责“项目侧落地与项目验收”；
- 回填只写指针，不写第二事实源。

## 7. 进入前检查清单

- [ ] 已确定是 local-only 还是 hybrid；
- [ ] 已确认目标仓库与写权限白名单；
- [ ] 已确认 `openrigCli` 可解析；`doctor` 通过；
- [ ] 新 bridge 为 `schemaVersion: 2`；旧 bridge 只读兼容；
- [ ] `workflow.yaml` 的 7 步与 `max_hops` 符合 v1.2 形状；
- [ ] 已确认项目侧是 `tickets-as-code` 还是 KB GitHub issue；
- [ ] 知道收口后 teardown 是最后动作；
- [ ] 已安排 teardown 前执行 `scripts/openrig-archive.py`，并知道 `archiveStatus=COMPLETE` 是硬门。

## 8. 常见误区

| 误区 | 正确做法 |
| --- | --- |
| 用 `doctor` 的 PASS 声称“CLI live 已跑通” | v1.2 的 `doctor` 只做结构/可解析性检查；live 命令在 `status`，见 1.3 候选 P-006 |
| 没有 `rig` 也硬跑 pytest | CI 等价环境应 2 个带理由 SKIP；有 rig 时 live 用例应真实执行 |
| 为了绿色删掉断言或用假 CLI | 禁止；只允许 skip-with-reason 或具名 hermetic stub |
| 在项目 `.ticket-store` 直接新建票文件 | 先 declaration 白名单，再 `ticket_plan.py` / `ticket_new.py` |
| 把 KB 票复制到项目票 | 只回填票号/URL/commit 指针 |
| 重渲染正在跑的 bundle 来“统一 v2” | 在跑实例与旧图绑定；只在下一轮/新 run 渲染 v2 |

## 9. 相关入口

- 本母版：`README.md` / `SPEC.md` / `ARCHITECTURE.md`
- 项目内归档规则：`$OPENRIG_REPO/var/openrig-archive/MANDATORY.md`
- v1.2 发布验证：`validation/v1.2.0/RELEASE.md`
- v1.2 入口 run 证据：`workflow-group/runs/openrig-master-v12-20261020/`
- KB issue tracker 规则：`docs/agents/issue-tracker.md`
- 项目票仓规则：`$OPENRIG_REPO/.ticket-store/docs/ticket-policy.md`
