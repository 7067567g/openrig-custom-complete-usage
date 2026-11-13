[English](ARCHITECTURE.md) | **简体中文**
> 三层模型、step vs round、内存/并发见 [`OPENRIG-WORKFLOW-GUIDE.zh-CN.md`](OPENRIG-WORKFLOW-GUIDE.zh-CN.md)。


# 架构

## 双平面

```text
控制面（workflow-group）
  PROJECT / SPEC / DECISIONS / STATUS / ISSUES
  roles: MAIN, PMO, TDO, QA, SAFETY
  wf.py: state、锁、brief、轮次、关闭 lint

执行面（OpenRig）
  rig / seats / queue / workflow / transcripts / snapshots
  render_master.py -> rig.yaml + workflow.yaml + bridge
  openrig_bridge.py -> doctor / status / capture
```

## 权威边界

| 事实 | 权威 |
|---|---|
| 目标、范围、验收 | 控制面 |
| 决策、预算、权限 | 控制面 |
| 实时 seat/queue/workflow 状态 | OpenRig |
| packet 投递 / transcript | OpenRig |
| 证据指针 | 两边通过 bridge + evidence 路径 |

两侧通过 `OPENRIG-BRIDGE.json` 映射，任何一侧都不能静默覆盖另一侧。

## 执行模式

- **local-only**：不启动 OpenRig，只跑文档和门禁；
- **hybrid**：渲染 bundle，启动隔离的 OpenRig home/daemon，拉起 seat，实例化 workflow，执行、关闭、归档；
- **attached**：仅在明确要求时复用已有 daemon/rig。

## 硬门

- rig 名和 workflow id 唯一；
- 每个 run 独立 `OPENRIG_HOME` 和 daemon 端口；
- 一个写权限一个 owner；
- 改 live 前先快照/回滚；
- teardown 前必须归档（`MANIFEST.json.archiveStatus == "COMPLETE"`）；
- 不得把 local-only 通过写成 hybrid E2E 通过。
