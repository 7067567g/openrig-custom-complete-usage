**English** | [简体中文](02-12-round-cases.zh-CN.md)

# Case 02 — three 12-round workflow cases

## Question

Can the workflow-group state machine carry a synthetic run through more than ten
complete rounds without losing status, decisions, evidence pointers, or close
semantics?

## Method

For each of three themes (`hardening`, `release`, `docs`):

1. `wf.py new-run`;
2. twelve times: `append-status`, `state STATUS qa-pending/qa-done`,
   write a round decision, `new-round`;
3. fill PROJECT §6, close PROJECT/DECISIONS/STATUS;
4. export and sanitize into `examples/round-cases/<case>/`.

## Result

```text
3 cases × 12 rounds = 36 STATUS files
3 × 12 round decisions + 3 terminal decisions
all cases: PROJECT closed, DECISIONS closed, STATUS closed
doctor: PASS for each case
```

## What it proves

- the 12-round state machine and document contracts are runnable;
- close semantics can be satisfied after >10 rounds;
- the exported cases are small enough to ship as public examples.

## What it does not prove

- real project quality or model output;
- a live OpenRig 5-seat hybrid run.

See `examples/round-cases/` and `scripts/generate_round_cases.py`.
