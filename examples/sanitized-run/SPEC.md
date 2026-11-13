# SPEC — demo-run

## 0. Layering

```text
baseline: composite/two-plane-orchestration@1.0.0
contracts: strategy@1.0.0, verify@1.0.0
```

## 1. Rules

- TDO writes only under the declared write scope.
- QA does not edit product files.
- MAIN records irreversible decisions in `DECISIONS.md`.
- No direct OpenRig SQLite/queue mutation.
