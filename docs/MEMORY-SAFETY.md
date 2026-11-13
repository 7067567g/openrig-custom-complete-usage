**English** | [简体中文](MEMORY-SAFETY.zh-CN.md)

# Memory safety for agent seats

Agent seats can grow far beyond their visible RSS because their systemd scope
also accounts page cache from large file reads. A cgroup limit is the right
control surface; `ulimit -v` is not enough.

## cgroup semantics

| Setting | Meaning | Additive? |
|---|---|---|
| `MemoryHigh` | soft threshold; reclaim/throttle | no, it lives inside `MemoryMax` |
| `MemoryMax` | hard RAM limit | yes, separate from swap |
| `MemorySwapMax` | swap limit | yes, separate from RAM |

```text
MemoryHigh=5G
MemoryMax=6G
MemorySwapMax=1G
```

means roughly **6G RAM + 1G swap**, not 12G.

## Recommended policy

```text
automatic seat:        MemoryHigh=5G  MemoryMax=6G  MemorySwapMax=1G
interactive terminal:  cap only as a last resort
host pressure order:   Chrome > image-gen > SD > chat/VM > agent terminal
```

Rationale: browser and image-generation processes are disposable; an agent
terminal may be carrying packet state, so it should not be the first victim.

## Seat launch example

Use a transient user scope:

```bash
systemd-run --user --scope --quiet \
  --unit="dsh-seat-$(date +%s)" \
  --property=MemoryAccounting=yes \
  --property=MemoryHigh=5G \
  --property=MemoryMax=6G \
  --property=MemorySwapMax=1G \
  -- dsh --profile headless "run one bounded task"
```

## Guard example

A generic guard is in [`examples/memory-limits/`](../examples/memory-limits/).
It only demonstrates the cgroup throttling path; thresholds must be reviewed for
your own host.

## Monitoring

```bash
grep -E 'MemTotal|MemAvailable|Cached|SwapTotal|SwapFree' /proc/meminfo
systemd-cgtop --order=memory
for u in $(systemctl --user list-units 'dsh-terminal-*.scope' --all --no-legend | awk '{print $1}'); do
  systemctl --user show "$u" -p Id -p MemoryCurrent -p MemoryPeak -p MemorySwapPeak --no-pager
done
```

## Safety rules

- Do not scan the DSH state directory, `$HOME`, or `/` from an agent shell.
- Use targeted paths; put `--max-filesize`, `head`, and `tail` on large reads.
- Redirect long seat output to a file; never capture unbounded output in Python.
- Treat `NEED_MAIN`/`BLOCKED` markers as authoritative; do not fake `DONE`.
