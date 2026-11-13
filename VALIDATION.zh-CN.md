[English](VALIDATION.md) | **简体中文**

# 验证 — 2026-11-13

环境：

- 仓库：`openrig-custom-complete-usage`
- Python：3.12（workflow-group venv）
- OpenRig CLI：本地 `rig` 0.1.4
- 未启动 live seat；这是 spec / render / bridge 层验证

## 测试

```text
146 passed, 1 skipped
```

## 12 轮 OpenRig 渲染

```text
smoke-001 ... smoke-012
daemon ports 47901 ... 47912
```

每轮：

- `render_master.py` exit 0；
- `OPENRIG-BRIDGE.json` schemaVersion=2；
- `openrig_bridge.py doctor` => `PASS`；
- 5 个 seat：main、pmo、tdo_opencode、tdo_dsh、qa。

## Spec 校验

```text
12/12 rounds: workflow validate => ok=true
Each: 7 steps
Warnings: declared_not_enforced_v1 + role_no_live_preferred_target
```

这些 warning 是因为没有启动 live rig，不是 render/schema 失败。

## 启动计划

```text
12/12 rounds: rig up --plan => status=planned
Each: 5 seats resolved
Warnings: permission_policy absent; launch_posture=floor
```

## 不声称

- 没有做 live 5-seat 执行；
- 没有模型 token/成本测量；
- 没有 hybrid E2E 通过；
- live 启动需要配置好的 OpenCode/DSH seat 和独立 `OPENRIG_HOME`。

## 12 轮工作流案例

用真实 `wf.py` 状态机生成三个案例：

```text
case-12-rounds-hardening  12 轮  closed
case-12-rounds-release    12 轮  closed
case-12-rounds-docs       12 轮  closed
```

每个案例有 12 个 STATUS、12 条轮次决策、终止决策、证据日志、
`ROUNDS.md` 和 `ROUNDS.json`。见 `examples/round-cases/`。
