[English](03-memory-incident.md) | **简体中文**

# 案例 03 — cgroup page cache 与主机 OOM

## 问题

为什么 14GB 主机会 OOM，但 agent shell 自身看起来很小？正确的限制方式是什么？

## 观测

一个 `dsh-terminal` systemd scope 显示：

```text
MemoryCurrent  4.6G
MemoryPeak     4.6G–11.1G
/bin/bash RSS  几 MB
```

同一个 scope 还统计了大文件读取产生的 page cache。14GB 主机上多个这样的
scope，加上桌面应用和生图服务，触发全局 OOM。内核杀了浏览器进程和用户会话；
`systemd-oomd` 杀了聊天/浏览器 scope。agent terminal 不是第一个被杀的对象。

## 根因

- cgroup memory 统计包含 page cache；
- 在 27GB 状态目录上跑 broad `rg`/`find`/`grep`/`zstd`，会把数 GB page cache
  记进 terminal scope；
- `ulimit -v` 限制不了 page cache；
- 没有 cgroup 上限、没有输出上限，一个 scope 可以涨到 7–11GB；
- 14GB RAM 不足以同时承载 dsh + 桌面 + 生图。

## 修复

```text
自动 seat：        MemoryHigh=5G  MemoryMax=6G  MemorySwapMax=1G
交互 terminal：    只在最后兜底时限流
压力回收顺序：     浏览器 > 生图 > SD > 聊天/VM > agent terminal
```

`MemoryHigh` 是软阈值，`MemoryMax` 是 RAM 硬上限，`MemorySwapMax` 是独立
swap 上限，**不是叠加关系**：

```text
5G high + 6G max + 1G swap ≈ 6G RAM + 1G swap
```

另外：

- 长输出重定向到日志文件，不用无界 Python capture；
- agent prompt 禁止宽范围扫描；
- 每轮记录 `MemoryPeak`；
- 大状态目录应清理/迁移，而不是扫描。

## 证明了什么

- 问题在工作流/执行环境的内存放大，不是单纯模型幻觉；
- 自动 seat 可以被限制，而不必先杀交互工作流；
- 可牺牲的 GUI/生图负载应优先回收。

见 [`examples/memory-limits/`](../../examples/memory-limits/) 和
[`docs/MEMORY-SAFETY.md`](../MEMORY-SAFETY.md)。
