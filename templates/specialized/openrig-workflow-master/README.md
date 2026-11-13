# openrig-workflow-master — OpenRig 混合编排母版

版本：`1.2.0`（见 `VERSION` / `CHANGELOG.md` / [`validation/v1.2.0/RELEASE.md`](../../../VALIDATION.md)）

## 是什么

一套 **workflow-group 控制面 + OpenRig 执行面** 的母版：

- workflow-group：目标、决策、验收、证据；
- OpenRig：rig、seat、queue、workflow、transcript、恢复；
- `render_master.py`：每个 run 生成唯一、自包含的 OpenRig bundle + bridge。

详细设计见 [`ARCHITECTURE.md`](ARCHITECTURE.md)；**进入与调用先看 [`ENTRYPOINTS.md`](ENTRYPOINTS.md)**；v1.2.0 发布验证见 [`validation/v1.2.0/RELEASE.md`](../../../VALIDATION.md)；v1.1.0 自优化验证见 [`validation/v1.1.0/`](../../../VALIDATION.md)；最终基线见 `BASELINE-post.sha256`。

## v1.1.0 自优化新增

- generator：`--dry-run`、`--json`、写盘前参数校验、退出码契约、逐产物 `render-manifest.json`、声明式产物表。
- bridge：`doctor` 交叉校验 bridge ↔ rig/workflow spec ↔ home；`status` 聚合 seats/workflow/queue 并支持 `--json`；`capture` 生成 sha256 清单并做密钥模式扫描。
- 文档：`ARCHITECTURE.md` 增加 queue 调优契约与 SAFETY 扩展契约（SAFETY 仅契约；v1.2 未实现执行器，已转 v1.3 候选）。
- 兼容：v1.0.0 的 render 产物字段保持可用；新增字段为 additive。

## v1.2.0 新增（可搬迁 / 可返工 / 可复算）

- **bridge v2**：`OPENRIG-BRIDGE.json` 升 `schemaVersion: 2`，bundle 内路径相对化（`bundleDir: "."`、`rigSpec: "rig.yaml"`、`workflowSpec: "workflow.yaml"`），整目录可搬迁；`projectRoot`/`openrigHome`/`openrigCli` 仍为运行期绝对语义。同 run 同参数渲染到两个不同 output-dir，5 个产物逐字节一致。
- **有界 QA→TDO 返工边**：workflow 模板改为分支专属 QA（`qa_opencode` / `qa_dsh` → `qa_join` → `close_round`）。各分支 `next_hop.on.failed` **静态**回边到本分支 TDO，失败可回到正确 TDO 并再次进入该分支 QA；只用既有 `next_hop.on` + `loop_guards.max_hops`，不新增引擎字段/API。
- **doctor 兼容**：v2 正例 PASS；绝对 `workflowSpec`/绝对 `bundleDir`/逃逸 `rigSpec` 等负例 rc=1 并指名字段；**v1 legacy bridge 仍只读兼容**（给出迁移提示，不静默改写）。
- **pytest 前置**：全仓测试全绿需 **`rig` 与 `node` 均可解析**。无 `rig`（保留 `node`，CI 等价）→ 137 passed + 2 skipped / rc=0；缺 `node` → 135/4；两者皆缺 → 133/6。M1 结论必须连同环境陈述。
- 发布证据与已知限制见 [`validation/v1.2.0/RELEASE.md`](../../../VALIDATION.md)。

## 目录

```text
openrig-workflow-master/
  SPEC.md                 # 双平面规则、证据、DoD
  PROJECT.md              # 控制面计划/指标/WS
  DECISIONS.md            # 决策账本
  README.md               # 本文件
  ENTRYPOINTS.md          # 入口选择与调用链（KB/项目双入口）
  ARCHITECTURE.md         # 接入/管理/优化详解
  render_master.py        # 渲染唯一 OpenRig bundle
  templates/              # rig/workflow/agent/guidance 模板
```

## 快速实例化

### 1. 建本地 run

```bash
cd $REPO_ROOT
python3 scripts/wf.py new-run <run-id> \
  --template templates/specialized/openrig-workflow-master \
  --goal "用 OpenRig 执行 <项目目标>" \
  --project-root /path/to/project \
  --scope 'runs/<run-id>/**；<project>/**' \
  --tdo 2
```

### 2. 渲染 OpenRig bundle

```bash
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id <run-id> \
  --project-root /path/to/project \
  --output-dir runs/<run-id>/openrig \
  --opencode-model opencode-go/deepseek-v4.1-flash \
  --dsh-profile headless
```

生成：

```text
runs/<run-id>/openrig/
  rig.yaml
  workflow.yaml
  agents/worker/agent.yaml
  guidance/team.md
  OPENRIG-BRIDGE.json
```

### 3. 隔离启动

```bash
export OPENRIG_HOME=/tmp/openrig-workflow-<run-id>
export OPENRIG_OPENCODE_BIN=opencode
export OPENRIG_DSH_BIN=dsh
export OPENRIG_OPENCODE_MODEL=opencode-go/deepseek-v4.1-flash

rig daemon start --no-kernel --port 47890
rig up runs/<run-id>/openrig/rig.yaml \
  --cwd /path/to/project --non-interruptive --yes --json
rig workflow validate runs/<run-id>/openrig/workflow.yaml --json
rig workflow instantiate runs/<run-id>/openrig/workflow.yaml \
  --root-objective "Execute <run-id>" \
  --created-by control-main@openrig-<run-id> --json
```

### 4. 执行与回执

- PMO 领取 entry packet；
- PMO 把计划/验收标准写入本地 `PROJECT.md`，把工作包投到 OpenRig queue；
- TDO-OC/TDO-DSH 各自领包执行，回执写 queue + transcript；
- 本地 `STATUS` 只留 packet id、证据路径、阻塞、完成状态；
- QA 对照 `SPEC.md` 和证据开 ISSUE；
- MAIN 在 `DECISIONS.md` 收口。

### 5. 收口

> **硬门：先归档，后 teardown。** 未生成 `MANIFEST.json.archiveStatus=COMPLETE` 的 run 不得 `rig down`、`daemon stop` 或删 `OPENRIG_HOME`。

```bash
cd $OPENRIG_REPO
python3 scripts/openrig-archive.py \
  --run-dir $REPO_ROOT/runs/<run-id> \
  --openrig-home /tmp/openrig-workflow-<run-id> \
  --session-id <control-session-id> --session-id <seat-session-id>
# 必须看到 status=COMPLETE；随后再 teardown

cd $REPO_ROOT
rig workflow abort <instance-id> --actor-session control-main@openrig-<run-id> \
  --reason "round closed" --json   # 或正常 close/project
rig down openrig-<run-id> --json
rig daemon stop
```

清理后检查：

```bash
ps -eo pid,args | grep -E 'opencode run|dsh --profile|cli-agent-runner' | grep -v grep
tmux ls
```

### Teardown 硬门

优先使用 OpenRig 项目中的归档校验包装器，而不是裸 `rig down`：

```bash
cd $OPENRIG_REPO
python3 scripts/openrig-teardown.py --run-id <run-id> --json            # 只读预检
python3 scripts/openrig-teardown.py --run-id <run-id> --execute \
  --teardown-cmd "rig down <rig-name> --json"                           # COMPLETE 才执行
```

`PARTIAL` 会 rc=2 且不执行 teardown；历史缺口必须用 `--allow-incomplete --decision D-xxx` 显式豁免。

## Bridge

`OPENRIG-BRIDGE.json` 是两边唯一映射：

```json
{
  "schemaVersion": 2,
  "runId": "...",
  "projectRoot": "...",
  "bundleDir": ".",
  "rigName": "openrig-...",
  "workflowId": "openrig-workflow-...",
  "rigSpec": "rig.yaml",
  "workflowSpec": "workflow.yaml",
  "openrigHome": "/tmp/openrig-workflow-...",
  "daemonPort": 47890,
  "seatMap": {
    "main": "control-main@...",
    "pmo": "control-pmo@...",
    "tdo_opencode": "exec-tdo-oc@...",
    "tdo_dsh": "exec-tdo-dsh@...",
    "qa": "assurance-qa@..."
  },
  "runtimeEnv": {},
  "policy": {}
}
```

> v2 约定：**bundle 内**路径（`bundleDir` / `rigSpec` / `workflowSpec`）必须相对且不得逃逸 bundle；`projectRoot` / `openrigHome` / `openrigCli` 是运行期字段，保持绝对语义。v1 legacy bridge 仍可由 `doctor` 只读校验。

## Bridge 工具

渲染后可用只读/证据型 bridge 工具：

```bash
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor \
  --run-dir runs/<run-id>
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py status \
  --run-dir runs/<run-id>
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py capture \
  --run-dir runs/<run-id>
```

- `doctor`：检查 bridge 字段、spec/project root、CLI、seat map；
- `status`：调用 `rig ps --nodes ... --json` 和 `rig workflow status --json`，写 `OPENRIG-STATE.json`；
- `capture`：把 `<OPENRIG_HOME>/transcripts/<rig>` 复制到 run evidence，不修改执行面。

## 默认策略

| 项             | 默认                                              |
| -------------- | ------------------------------------------------- |
| 运行模式       | managed isolated                                  |
| seats          | 5（MAIN/PMO/TDO-OC/TDO-DSH/QA）                   |
| 最大活跃 agent | 2                                                 |
| OC model       | `opencode-go/deepseek-v4.1-flash`（可按角色覆盖） |
| DSH profile    | `headless`                                        |
| resume         | 优先，fresh 必须记录原因                          |
| SAFETY         | 高风险时按需扩展                                  |
| 源码权限       | 项目 WS 决定；母版本身不授权删除/发布             |

## 注意

- 不修改 `60-外部仓库/openrig`；生成物在 run 目录；
- 不把 auth/key 写进 bridge；
- 不同 run 不共享 `OPENRIG_HOME`；
- `rig workflow instantiate` 需要 rig 已启动；
- 运行中的真实模型调用必须有 runtime 自己的认证；
- 母版只负责编排契约，具体项目的验收命令由 `PROJECT.md`/WS 决定。

## 已知限制

- `render-manifest.json` 与 5 个 bundle 产物在**同一 run、同一参数**下跨 output-dir 逐字节一致；`renderedAt` 仅存在于 manifest 元数据，不参与产物身份。不同 run 的 `runId/rigName/workflowId` 不同，不能直接比较。
- OpenRig v1 的 handoff 多 successor 场景只保证 `transitionNote` 有 successor 数量；`closureReason/closureTarget` 可能为 `null`，不要把它当唯一证据。
- SAFETY 目前是契约与 gate 账本格式，执行器未实现；高风险动作仍需独立门控。
