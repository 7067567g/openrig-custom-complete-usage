**English** | [简体中文](README.zh-CN.md)

# Live OpenRig run evidence (single-step)

This directory contains sanitized evidence from one **real** OpenRig workflow
run, used to audit the public repository content.

- rig: `content-audit-analyst`
- workflow: `content-audit` (one step, role `analyst`)
- runtime: `opencode`, model `deepseek/deepseek-flash`
- result: workflow completed; report written to `reports/openrig_analyst_report.md`

Included:

```text
rig-ps-nodes.json       sanitized `rig ps --nodes --json`
OPENRIG-STATE.json      sanitized `rig workflow show --json`
workflow-trace.json     sanitized `rig workflow trace --json`
```

This is **not** a 5-seat hybrid E2E. It proves the single-step workflow runtime,
packet handoff, and factual report delivery.
