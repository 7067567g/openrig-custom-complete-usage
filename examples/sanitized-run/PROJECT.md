# PROJECT — demo-run

## 0. Metadata

```text
run-id: demo-run
state: waiting-main
template: openrig-workflow-master
baseline: composite/two-plane-orchestration@1.0.0
contracts: strategy@1.0.0, verify@1.0.0
```

## 1. Goal

Add a small, verifiable feature to `<target-repo>` with one PMO, one TDO, and
one QA pass.

## 2. Scope

```text
write: runs/demo-run/**, <target-repo>/src/**
read:  everything else
never: secrets, credentials, production data
```

## 3. Acceptance

- feature test passes;
- existing test suite passes;
- evidence pointers recorded in `STATUS-Round-1.md`;
- QA opens no blocking issue.

## 4. Work packages

| WS | Owner | Outcome |
|---|---|---|
| WS-1 | tdo-a1 | implement feature + tests |
| WS-2 | qa | independent review |

## 5. Metrics

- test pass/fail
- changed files
- gate verdict
- wall-clock

## 6. Round summary

R1 complete; waiting for MAIN decision.
