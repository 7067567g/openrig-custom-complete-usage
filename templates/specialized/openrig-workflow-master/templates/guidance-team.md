# OpenRig hybrid workflow team

Use this rig as an execution plane, not as the project decision ledger.

- The control-plane run is `{{RUN_ID}}`.
- Project root: `{{PROJECT_ROOT}}`.
- Report execution facts through OpenRig queue/transcript; report decisions and acceptance through workflow-group.
- One work packet per bounded change. Keep evidence paths in the local STATUS and QA report.
- Do not put provider keys, auth files, or full conversations in reports.
- Prefer the smallest model that can do the job; keep at most two active agents at once unless the operator explicitly raises the budget.
