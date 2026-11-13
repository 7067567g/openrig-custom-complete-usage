[English](README.md) | **简体中文**

# 真实 OpenRig run 证据（单步）

本目录包含一次**真实** OpenRig workflow run 的脱敏证据，用来审计公开仓库
内容。

- rig：`content-audit-analyst`
- workflow：`content-audit`（单步，角色 `analyst`）
- runtime：`opencode`，模型 `deepseek/deepseek-flash`
- 结果：workflow completed；报告写入 `reports/openrig_analyst_report.md`

包含：

```text
rig-ps-nodes.json       脱敏后的 `rig ps --nodes --json`
OPENRIG-STATE.json      脱敏后的 `rig workflow show --json`
workflow-trace.json     脱敏后的 `rig workflow trace --json`
```

这**不是** 5-seat hybrid E2E。它证明的是单步 workflow runtime、packet 交接和
事实报告投递。
