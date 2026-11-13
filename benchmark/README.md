# Benchmark module

This directory is reserved for the end-to-end benchmark harness that accompanies
the workflow examples.

Planned contents:

```text
benchmark/
  harness/          run_suite.py, run_pilot.py, sandbox.py, report_pilot.py
  local_judge/      task interface, oracle/generator examples, scorer
  tasks/            synthetic, redistributable demo tasks only
  README.md         how to run a raw-vs-SCTG smoke
```

The public repository will **not** ship copyrighted problem statements or
internal benchmark results. The harness will accept user-supplied task packs.

For the current status, see `docs/PUBLISHING.md`.
