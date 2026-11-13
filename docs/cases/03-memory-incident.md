**English** | [简体中文](03-memory-incident.zh-CN.md)

# Case 03 — cgroup page cache and a host OOM

## Question

Why did a 14 GB host run out of memory even though the agent shell itself
looked small, and what is the right guardrail?

## Observation

A `dsh-terminal` systemd scope showed:

```text
MemoryCurrent  4.6G
MemoryPeak     4.6G–11.1G
/bin/bash RSS  a few MB
```

The same scope also accounted large file page cache from broad reads. On a
14 GB host, several such scopes plus desktop apps and an image-generation
service triggered a global OOM. The kernel killed a browser process and the
user session; `systemd-oomd` killed chat/browser scopes. The agent terminal was
not the first victim.

## Root cause

- cgroup memory accounting includes page cache;
- broad `rg`/`find`/`grep`/`zstd` over a 27 GB state directory can fill GBs of
  page cache in a terminal scope;
- `ulimit -v` does not cap page cache;
- no cgroup limit and no output cap meant one scope could grow to 7–11 GB;
- the host had 14 GB RAM, not enough for dsh + desktop + image generation.

## Fix

```text
automatic seat:        MemoryHigh=5G  MemoryMax=6G  MemorySwapMax=1G
interactive terminal:  last-resort throttle only
pressure order:        browser > image-gen > SD > chat/VM > agent terminal
```

`MemoryHigh` is a soft threshold; `MemoryMax` is the hard RAM cap;
`MemorySwapMax` is separate. They are **not additive**:

```text
5G high + 6G max + 1G swap ≈ 6G RAM + 1G swap
```

Also:

- redirect long seat output to a log file, not unbounded Python capture;
- forbid broad scans from agent prompts;
- record `MemoryPeak` per round;
- clean/move large state directories instead of scanning them.

## What this case proves

- the problem was workflow/execution-environment memory amplification, not a
  single model hallucination;
- an automatic seat can be bounded without killing the interactive workflow;
- disposable GUI/image workloads should be reclaimed first.

See [`examples/memory-limits/`](../../examples/memory-limits/) and
[`docs/MEMORY-SAFETY.md`](../MEMORY-SAFETY.md).
