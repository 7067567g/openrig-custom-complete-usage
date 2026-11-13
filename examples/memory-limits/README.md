**English** | [简体中文](README.zh-CN.md)

# Memory limits example

Reference patterns for running an agent seat under a cgroup and for a
non-destructive memory guard.

```text
service drop-ins: `agent-host-memory.conf`, `app-service-memory.conf`
seat-launch.example.sh   systemd-run --scope with 5G/6G/1G
guard.example.sh         dry-run cgroup throttle for dsh-terminal scopes
```

These are examples, not a drop-in production guard. Review thresholds against
your host's RAM and workload.

## Why

A `dsh-terminal` cgroup can show 4–11G while `/bin/bash` itself is only a few
MB; the difference is page cache from large file reads. `MemoryMax` is what caps
that; `ulimit -v` does not.

## Run

```bash
bash examples/memory-limits/seat-launch.example.sh --help
bash examples/memory-limits/guard.example.sh --dry-run
```

## Policy

- automatic seat: `MemoryHigh=5G`, `MemoryMax=6G`, `MemorySwapMax=1G`
- disposable apps first: browser > image generation > SD > chat/VM
- agent terminal last; it may carry workflow state
