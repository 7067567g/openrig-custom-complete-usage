# Benchmark status

## Status: NOT RUN

Benchmark tests were **not run** for this release.

## Reason

The benchmark requires paid model calls, a stable live environment, and a time
budget. That budget is currently unavailable, so no benchmark result is claimed.

## What this means

- No token/cost measurement is claimed.
- No latency/throughput comparison is claimed.
- No model-quality or “better than X” claim is claimed.
- Unit tests, document consistency checks, render checks, and smoke checks are
  validation evidence; they are **not** a benchmark.

## What was verified instead

- Repository hygiene and link checks.
- Document consistency and bilingual-document checks.
- Render/bridge/spec validation where the repository provides it.
- Targeted tests that do not require paid model calls.

## Revisit condition

Run the benchmark only when there is an explicit budget, a fixed environment,
and a defined comparison protocol. Publish the raw configuration and the exact
limitations, not just a headline number.
