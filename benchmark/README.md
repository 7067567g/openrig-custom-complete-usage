**English** | [简体中文](README.zh-CN.md)

# Benchmark module

This is a **mechanics smoke harness**, not a model benchmark. It exists so the
repository has a real, runnable benchmark interface while the full raw-vs-SCTG
model harness is developed.

```text
benchmark/
  harness/run_benchmark.py   copy task workspace -> run arm -> verify -> JSON/MD
  arms.example.yaml          replace commands with real workflow launchers
  tasks/synthetic-v1/        synthetic, redistributable task pack
  results/                   generated smoke results
```

Run:

```bash
python3 benchmark/harness/run_benchmark.py
```

What it proves: task isolation, arm execution, verification, result capture.
What it does not prove: model quality, token/cost, or raw-vs-SCTG performance.

The full harness (model arms, local judge, sandbox, preflight audit) is tracked
as the remaining P0 gap in `reports/content_gap_audit.md`.
