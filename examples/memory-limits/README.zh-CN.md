[English](README.md) | **简体中文**

# 内存限制示例

Agent seat 的 cgroup 限制和非破坏性内存守护参考。

```text
seat-launch.example.sh   systemd-run --scope，5G/6G/1G
guard.example.sh         对 dsh-terminal scope 做 dry-run 限流
```

这些是示例，不是可直接上生产的守护脚本；阈值要按主机内存和工作负载复核。

## 为什么

`dsh-terminal` cgroup 可能显示 4–11G，但 `/bin/bash` 只有几 MB；差额是大文件读取产生的 page cache。`MemoryMax` 才能限制它，`ulimit -v` 不行。

## 运行

```bash
bash examples/memory-limits/seat-launch.example.sh --help
bash examples/memory-limits/guard.example.sh --dry-run
```

## 策略

- 自动 seat：`MemoryHigh=5G`、`MemoryMax=6G`、`MemorySwapMax=1G`
- 可牺牲应用优先：浏览器 > 生图 > SD > 聊天/VM
- agent terminal 最后；它可能承载工作流状态
