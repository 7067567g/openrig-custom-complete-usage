# Changelog — openrig-workflow-master

## 1.2.0 — 2026-10-20

主题：**可搬迁、可返工、可复算的可发布母版**。

### Added

- **Bridge v2（bundle 可搬迁）**：`render_master.py` 产出的 `OPENRIG-BRIDGE.json` 升 `schemaVersion: 2`，bundle 内路径改为相对（`bundleDir: "."`、`rigSpec: "rig.yaml"`、`workflowSpec: "workflow.yaml"`）；`projectRoot`/`openrigHome`/`openrigCli` 保持运行期绝对语义。同 run 同参数渲染到两个不同 output-dir，5 个产物**逐字节一致**。
- **有界 QA→TDO 返工边**：`templates/workflow.yaml.tpl` 采用分支专属 QA（`qa_opencode` / `qa_dsh` / `qa_join`）：各分支 `next_hop.on.failed` 以**静态边**回到本分支 TDO，两分支通过后 `qa_join` 汇合再 `close_round`；仅使用既有 `next_hop.on` 与 `loop_guards.max_hops`（=10，含 hop 预算计算），**不新增引擎字段/API**。返工边由隔离实例的**真实 failed-exit 投影**证明（`runs/openrig-master-v12-20261020/evidence/dsh/probe/**`），而非"图上画边"。
- 测试：`workflow-group/tests/test_render_master_portability.py`、`workflow-group/tests/test_workflow_rework.py`。
- 文档：新增 `ENTRYPOINTS.md`，梳理 local-only / hybrid / 接续已有 run 三种入口、控制面与执行面调用链，以及 KB GitHub issue 与 `$PROJECT_REPO` 的 `tickets-as-code` 双票制边界。

### Changed

- `scripts/wf.py`：`serve_start` 在拼 `serve --pure` / 发 HTTP 前探测 `opencode --version`；本机 v2.x（实测 v2.0.32）或版本未知时 **rc=1**，并提示改用 `opencode run` headless 或 `OPENCODE_BIN=/path/to/opencode-1.x`。`delegate`/`squad` 默认自动拉起服务，因此同经此失败；显式 `--server` 指向 v1 服务保留原 v1 路径。版本探测与实际 launch 共用 `OPENCODE_BIN`，避免“探测用兼容二进制、启动却仍用 PATH 中 v2”的半修。不再把 v1 预热 405 吞成 `[WARN]` + rc=0。同步纠正 `WORKFLOW.md §9`、`DESIGN.md §6`、`EVOLUTION.md` 对应行、`AGENTS.md` SAFETY 入口、`roles/delegation-briefs.md` 四段/v1-v2 口径。
- `tools/openrig_bridge.py`：doctor 支持 v2（正例 PASS；绝对 `workflowSpec` / 绝对 `bundleDir` / 逃逸 `rigSpec` 等负例 rc=1 且**指名字段**），并保留 **v1 legacy 只读兼容 + 迁移提示**，不静默改写旧 bridge（见 DECISIONS D-007）。
- `validation/README.md`：标注 `master-smoke-20261020` / `openrig-workflow-master-scratch-20261020` 的 run 目录未留存（仅保留抓取文件），补快照日期与 `sha256sum -c` 结论。

### Baseline

- `BASELINE-pre.sha256`：v1.1.0 → v1.2.0 改动前 36 文件基线（带注释头；建立时母版目录无 tracked diff）。建立后复算为 **33 OK + 3 个预期差异**，差异恰为 WS-A/WS-B 声明的 3 个母版改动文件。
- `BASELINE-post.sha256`：v1.2.0 收口全量重算（`sha256sum -c` rc 见 `validation/v1.2.0/RELEASE.md`）。
- pre/post 差异哈希对 v1.0.0 不可得（v1.0.0 无 pre 基线）；v1.2.0 起 pre/post 成对可复算。

### 前置条件（pytest 全绿的环境要求）

- 全仓 `pytest` 全绿需 **`rig` 与 `node` 均可解析**：
  - 缺 `rig` → **137 passed / 2 failed**（`test_render_master_portability.py` 两例；doctor 经 `run_cli` 返回 rc=127「CLI not found」）。
  - 缺 `node`（rig shim 在但其 exec 的 node 不可用）→ **135 passed / 4 failed**；两者皆缺 → **133 passed / 6 failed**。（`test_workflow_rework.py` 的 3 个 parser/validator 例 + 1 个 doctor live 例）
- 因此 M1 的 PASS 必须连同环境陈述，禁止只写「全绿」。证据：`DECISIONS` D-012 / D-016、`QA-REPORT.md` P-002。

### Known limitations

- **本 run 自身的 bundle 停留在 legacy `schemaVersion:1`**：它由改前 generator 于 PRECHECK 渲染，live 实例即由其实例化；doctor 对其 PASS 属**只读 legacy 兼容**，不代表 v2。v1.2 的 v2 证据在 M2/M3，见 `validation/v1.2.0/RELEASE.md`。
- doctor v2 未覆盖 **symlink 逃逸**；Windows 未实测（`QA-REPORT.md` R-002）。
- 执行面「一次发送→两次投递」缺陷（`QA-REPORT.md` P-001 / S2）**未在本 run 修复**（本 run 禁改 parent），去向见下节。

## 1.3 候选（明确延后，不在 1.2.0 内）

- **wake/delivery 幂等去重 + 唤醒快照新鲜度**：一次发送产生两次投递，击穿单一写者（本 run P-001）；watchdog 唤醒所依据的快照在交付时已过期（IC-1 三次样本）。
- **stuck 判定需证据/活性佐证**：`stalled-after-claim` 仅按队列变更年龄，对正在产出证据的 owner 会误报（R-001）。
- **真实模型 QA 失败任务 E2E**：本 run 按 D-008 取结构化投影，真实模型失败留待可靠性验证。
- **SAFETY 执行器**：当前仅契约，未实现。
- **DECISIONS 写入审计 / hash-chain / 单一写者强制**。
- **授权 → packet 自动核对**；**queue → STATUS 回填**。
- **多项目 registry**；**成本/延迟遥测**；**Tier B 全量 self-check**。
- **doctor 覆盖 symlink 逃逸与 Windows**（R-002）。
- **doctor 静态/live 拆分**：当前 doctor 只做结构/可解析性检查，不执行 live CLI 命令；portability 测试保留的是“可解析”断言而非“CLI 真能跑”断言，需要拆分 static 与 live 两段（P-006）。
- **queue packet body 512 字符截断**：需要附带 addendum 或结构化 evidence 指针（R-003）。

## 1.1.0 — 2026-10-20

### Added / changed

- `render_master.py`：写盘前参数校验、`--dry-run`、`--json`、退出码 0/2/3 契约。
- `render_master.py`：逐产物 `render-manifest.json`（path/template/bytes/sha256/masterVersion）。
- `render_master.py`：声明式 `ARTIFACTS` 产物表；未渲染占位符/缺模板仍硬失败。
- `tools/openrig_bridge.py`：`status` 聚合 seats/workflow/queue 指标，`--json`，0/2 退出码。
- `tools/openrig_bridge.py`：`doctor` 交叉校验 bridge ↔ rig.yaml ↔ workflow.yaml ↔ openrigHome。
- `tools/openrig_bridge.py`：`capture` 生成 sha256 清单并做密钥模式扫描。
- `ARCHITECTURE.md`：补 queue 调优契约与 SAFETY 扩展契约；SAFETY 仅契约，不实现执行器。
- 自优化 run 证据：`workflow-group/runs/openrig-master-selfopt-20261020/`；最终 QA = QA_PASS，open S1/S2=0。
- 自优化发现（v1.2 候选）：DECISIONS 缺写入审计/单一写者强制；授权存在 ≠ packet 已创建；未跟踪母版缺 pre/post baseline；workflow graph 缺 QA→TDO rework 边（引擎已有 resume，但图内没有返工边）。

### Known limitations

- `render-manifest.json` 的 sha256 只在同一 output-dir 内可比；跨目录时 bridge 的绝对路径字段会变化。路径相对化列入 v1.2。
- OpenRig v1 的 handoff 多 successor 场景可能只有 `transitionNote` 保留 successor 数量；`closureReason/closureTarget` 可能为 null。
- SAFETY 执行器未实现；高风险动作仍需独立 gate/人工批准。
- `--dry-run` / `--json` / manifest 是 additive；v1.0.0 的 rig/workflow/bridge 字段仍可用。
- 本轮自优化 run 的 workflow instance 因 QA 初检 `close_round` failed；QA 最终复核已 PASS，但实例终止状态不等于控制面 run 失败；rework/close 以控制面与后续实例为准。

## 1.0.0 — 2026-10-20

- 双平面契约：workflow-group 控制面 + OpenRig 执行面。
- `render_master.py` 每 run 生成唯一 rig/workflow/agent/guidance/bridge。
- 默认 managed isolated 运行模式。
- 默认 5 seats：MAIN/PMO/TDO-OC/TDO-DSH/QA。
- `tools/openrig_bridge.py` 提供 doctor/status/capture。
- 真实 OpenRig smoke：5/5 ready；workflow validate/instantiate/abort；entry packet 到 PMO。
- 文档：`ARCHITECTURE.md` / `SPEC.md` / `README.md`。
- 已知后续：SAFETY 扩展、全自动 status/queue 双写审计、跨项目 registry、成本遥测。

## 1.2 候选（历史，已处置）

v1.1.0 当时列出的 1.2 候选，现已分流完毕：

- bridge 路径相对化（bundle 可整体搬迁）→ **已在 1.2.0 交付**。
- SAFETY 执行器、queue→STATUS 回填、多项目 registry、成本/延迟采集、Tier B generator self-check → **转入上文 `## 1.3 候选`**。
