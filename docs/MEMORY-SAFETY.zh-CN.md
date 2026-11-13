[English](MEMORY-SAFETY.md) | **简体中文**

# Agent seat 的内存安全

Agent seat 的真实占用可能远大于 `RSS`，因为它的 systemd scope 还会统计大文件读取产生的 page cache。正确控制面是 cgroup，不是 `ulimit -v`。

## cgroup 语义

| 设置 | 含义 | 是否叠加 |
|---|---|---|
| `MemoryHigh` | 软阈值；超过后回收/节流 | 否，在 `MemoryMax` 内部 |
| `MemoryMax` | RAM 硬上限 | 是，与 swap 分开 |
| `MemorySwapMax` | swap 上限 | 是，与 RAM 分开 |

```text
MemoryHigh=5G
MemoryMax=6G
MemorySwapMax=1G
```

大约等于 **6G RAM + 1G swap**，不是 12G。

## 推荐策略

```text
自动 seat：          MemoryHigh=5G  MemoryMax=6G  MemorySwapMax=1G
交互 terminal：      只在最后兜底时限制
主机压力回收顺序：   Chrome > 生图 > SD > 聊天/VM > agent terminal
```

理由：浏览器和生图是可牺牲的；agent terminal 可能承载 packet 状态，不应第一个被杀。

## Seat 启动示例

```bash
systemd-run --user --scope --quiet \
  --unit="dsh-seat-$(date +%s)" \
  --property=MemoryAccounting=yes \
  --property=MemoryHigh=5G \
  --property=MemoryMax=6G \
  --property=MemorySwapMax=1G \
  -- dsh --profile headless "run one bounded task"
```

## Guard 示例

通用 guard 在 [`examples/memory-limits/`](../examples/memory-limits/)，只演示 cgroup 限流路径；阈值需要按你的主机复核。

## 监控

```bash
grep -E 'MemTotal|MemAvailable|Cached|SwapTotal|SwapFree' /proc/meminfo
systemd-cgtop --order=memory
for u in $(systemctl --user list-units 'dsh-terminal-*.scope' --all --no-legend | awk '{print $1}'); do
  systemctl --user show "$u" -p Id -p MemoryCurrent -p MemoryPeak -p MemorySwapPeak --no-pager
done
```

## 安全规则

- 不要在 agent shell 里扫描 the DSH state directory、`$HOME`、`/`；
- 大文件只读 `head/tail`，检索加 `--max-filesize`；
- 长输出重定向到文件，不要用 Python 无界 `capture_output`；
- `NEED_MAIN`/`BLOCKED` 是权威状态，不要伪造 `DONE`。
