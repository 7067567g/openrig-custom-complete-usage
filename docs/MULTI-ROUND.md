**English** | [简体中文](MULTI-ROUND.zh-CN.md)
> This document covers workflow-group rounds. For OpenRig steps, packets, and the one-line path, see [`OPENRIG-WORKFLOW-GUIDE.md`](OPENRIG-WORKFLOW-GUIDE.md).


# Multi-round workflow

## Roles

- **MAIN** — delegates, collects, decides, closes; does not write TDO/QA content.
- **PMO** — owns `PROJECT.md`: goal, scope, metrics, work packages, round summary.
- **TDO** — owns `STATUS-Round-n.md`: progress, evidence, blockers; lock before write.
- **QA** — owns `ISSUES.xlsx`: findings, severity, decision-needed flags.
- **SAFETY** — optional, independent review of failed/destructive actions.

## Round loop

```text
new-run
  -> PMO plan
  -> brief TDO(s)
  -> TDO execute + append STATUS
  -> QA review + ISSUES
  -> PMO close round + PROJECT §6
  -> MAIN reads PROJECT §6, writes DECISIONS
  -> new-round
```

## State transitions

Use only the documented transition owner:

```bash
python3 scripts/wf.py state <run-id> STATUS qa-pending --by main
python3 scripts/wf.py state <run-id> STATUS qa-done --by qa
python3 scripts/wf.py state <run-id> PROJECT waiting-main --by pmo
```

## Locks

TDO must lock before writing STATUS:

```bash
python3 scripts/wf.py lock <run-id>
# append one status entry
python3 scripts/wf.py unlock <run-id>
```

## Close

```bash
python3 scripts/wf_close_lint.py --run <run-id>
# ERROR must be 0
python3 scripts/wf.py state <run-id> PROJECT closed --by main
```
