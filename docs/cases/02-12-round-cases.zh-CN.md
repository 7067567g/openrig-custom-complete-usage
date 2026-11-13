[English](02-12-round-cases.md) | **简体中文**

# 案例 02 — 三个 12 轮工作流案例

## 问题

workflow-group 状态机能否把一个合成 run 完整跑过十轮以上，同时不丢
STATUS、决策、证据指针或关闭语义？

## 方法

对三个主题（`hardening`、`release`、`docs`）分别：

1. `wf.py new-run`；
2. 连续 12 次：`append-status`、`state STATUS qa-pending/qa-done`、
   写一条轮次决策、`new-round`；
3. 填 PROJECT §6，关闭 PROJECT/DECISIONS/STATUS；
4. 导出并脱敏到 `examples/round-cases/<case>/`。

## 结果

```text
3 个案例 × 12 轮 = 36 个 STATUS 文件
3 × 12 条轮次决策 + 3 条终止决策
所有案例：PROJECT closed、DECISIONS closed、STATUS closed
每个案例 doctor: PASS
```

## 证明了什么

- 12 轮状态机和文档合同可以完整运行；
- 十轮以上仍能满足关闭语义；
- 导出的案例足够小，可以作为公开示例。

## 没有证明什么

- 真实项目质量或模型输出；
- 真实 OpenRig 5-seat hybrid run。

见 `examples/round-cases/` 和 `scripts/generate_round_cases.py`。
