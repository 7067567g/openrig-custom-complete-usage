<!-- wf-doc
run: case-12-rounds-release
round: 12
doc: DECISIONS
owner: 主会话
state: closed
updated: 2026-11-13
-->

# DECISIONS — OpenRig 混合编排母版实例

## 0. 记录规则

1. 每条决策唯一 ID，按时间只增不改。
2. 目标、删除、发布、预算、权限、跨 run 边界必须由本账本记录。
3. 执行状态由 OpenRig queue/workflow 负责，不在本文件抄写实时状态。
4. 任何“跳过 OpenRig 直接做”的降级必须单独决策并标注原因。

## 1. 决策账本

### D-001（Round 1）双平面权威

- **决策**：workflow-group 控制面负责目标/决策/验收；OpenRig 执行面负责 seat/queue/workflow/transcript；`OPENRIG-BRIDGE.json` 是唯一映射。
- **背景/选项**：
  - A：把 queue 当项目账本，容易丢失决策和验收；
  - B：两边各存一份全量状态，容易漂移；
  - C（采用）：各管一类事实，证据路径相互指向。
- **影响面**：所有 WS 必须引用 bridge；禁止双写全量状态。
- **状态**：生效

### D-002（Round 1）每 run 生成唯一 rig/workflow spec

- **决策**：由 `render_master.py` 生成唯一 rig 名、workflow id、cwd、seat map 和 bridge；同一台机器可并行多个 run，不共享 namespace。
- **影响面**：不直接复用示例 rig/workflow 名字；生成物进 run 目录。
- **状态**：生效

### D-003（Round 1）默认隔离运行

- **决策**：默认 managed isolated：独立 `OPENRIG_HOME`、端口、tmux；attached 模式需主会话显式批准。
- **理由**：避免跨项目 queue/session 污染，便于清理与复现。
- **状态**：生效

### D-101（Round 1）freeze scope

- **决策**：Round 1 按计划完成；证据写入 `STATUS-Round-1.md`。
- 状态：生效

### D-102（Round 2）verify version consistency

- **决策**：Round 2 按计划完成；证据写入 `STATUS-Round-2.md`。
- 状态：生效

### D-103（Round 3）audit docs links

- **决策**：Round 3 按计划完成；证据写入 `STATUS-Round-3.md`。
- 状态：生效

### D-104（Round 4）run example demo

- **决策**：Round 4 按计划完成；证据写入 `STATUS-Round-4.md`。
- 状态：生效

### D-105（Round 5）run sanitization scan

- **决策**：Round 5 按计划完成；证据写入 `STATUS-Round-5.md`。
- 状态：生效

### D-106（Round 6）verify OpenRig render

- **决策**：Round 6 按计划完成；证据写入 `STATUS-Round-6.md`。
- 状态：生效

### D-107（Round 7）verify bridge doctor

- **决策**：Round 7 按计划完成；证据写入 `STATUS-Round-7.md`。
- 状态：生效

### D-108（Round 8）review release notes

- **决策**：Round 8 按计划完成；证据写入 `STATUS-Round-8.md`。
- 状态：生效

### D-109（Round 9）check CI matrix

- **决策**：Round 9 按计划完成；证据写入 `STATUS-Round-9.md`。
- 状态：生效

### D-110（Round 10）prepare tag checklist

- **决策**：Round 10 按计划完成；证据写入 `STATUS-Round-10.md`。
- 状态：生效

### D-111（Round 11）run final smoke

- **决策**：Round 11 按计划完成；证据写入 `STATUS-Round-11.md`。
- 状态：生效

### D-112（Round 12）close release case

- **决策**：Round 12 按计划完成；证据写入 `STATUS-Round-12.md`。
- 状态：生效

### D-999（Final）case-12-rounds-release 收口

- **决策**：12 轮全部完成，QA 无阻塞项，证据见 `ROUNDS.md`。
- 状态：达成

## 2. 待决清单

| 编号 | 待决问题 | 选项 A | 选项 B | 主会话拍板 | 状态 |
| --- | --- | --- | --- | --- | --- |
| Q-1 | 两个 TDO 分支并行还是串行 | 预算允许时并行（推荐） | 始终串行 | — | 待决 |
| Q-2 | SAFETY 是否强制 | 仅高风险动作强制（推荐） | 所有 run 强制 | — | 待决 |
| Q-3 | 失败后 fresh 还是 resume | 优先 resume，明确 fresh 需 DECISION（推荐） | 一律 fresh | — | 待决 |

## 3. 编制变更时间线

| 轮次 | PMO | TDO | QA | 变更理由 | 决策 ID |
| --- | --- | --- | --- | --- | --- |
| R1 | 1 | 1 | 1 | 初始立项 | D-001 |
