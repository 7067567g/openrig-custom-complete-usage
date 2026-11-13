<!-- wf-doc
run: <RUN-ID>
round: <ROUND-N>
doc: DECISIONS
owner: 主会话
state: open
updated: <DATE>
-->

# DECISIONS — OpenRig 混合编排母版实例

## 0. 记录规则

1. 每条决策唯一 ID，按时间只增不改。
2. 目标、删除、发布、预算、权限、跨 run 边界必须由本账本记录。
3. 执行状态由 OpenRig queue/workflow 负责，不在本文件抄写实时状态。
4. 任何“跳过 OpenRig 直接做”的降级必须单独决策并标注原因。

## 1. 决策账本

### D-001（Round <ROUND-N>）双平面权威

- **决策**：workflow-group 控制面负责目标/决策/验收；OpenRig 执行面负责 seat/queue/workflow/transcript；`OPENRIG-BRIDGE.json` 是唯一映射。
- **背景/选项**：
  - A：把 queue 当项目账本，容易丢失决策和验收；
  - B：两边各存一份全量状态，容易漂移；
  - C（采用）：各管一类事实，证据路径相互指向。
- **影响面**：所有 WS 必须引用 bridge；禁止双写全量状态。
- **状态**：生效

### D-002（Round <ROUND-N>）每 run 生成唯一 rig/workflow spec

- **决策**：由 `render_master.py` 生成唯一 rig 名、workflow id、cwd、seat map 和 bridge；同一台机器可并行多个 run，不共享 namespace。
- **影响面**：不直接复用示例 rig/workflow 名字；生成物进 run 目录。
- **状态**：生效

### D-003（Round <ROUND-N>）默认隔离运行

- **决策**：默认 managed isolated：独立 `OPENRIG_HOME`、端口、tmux；attached 模式需主会话显式批准。
- **理由**：避免跨项目 queue/session 污染，便于清理与复现。
- **状态**：生效

## 2. 待决清单

| 编号 | 待决问题 | 选项 A | 选项 B | 主会话拍板 | 状态 |
| --- | --- | --- | --- | --- | --- |
| Q-1 | 两个 TDO 分支并行还是串行 | 预算允许时并行（推荐） | 始终串行 | — | 待决 |
| Q-2 | SAFETY 是否强制 | 仅高风险动作强制（推荐） | 所有 run 强制 | — | 待决 |
| Q-3 | 失败后 fresh 还是 resume | 优先 resume，明确 fresh 需 DECISION（推荐） | 一律 fresh | — | 待决 |

## 3. 编制变更时间线

| 轮次 | PMO | TDO | QA | 变更理由 | 决策 ID |
| --- | --- | --- | --- | --- | --- |
| R<ROUND-N> | 1 | <TDO-N> | 1 | 初始立项 | D-001 |
