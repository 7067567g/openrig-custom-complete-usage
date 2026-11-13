[English](README.md) | **简体中文**

# case-12-rounds-hardening

一个合成但真实的 12 轮 workflow-group 案例：**Harden a small service over 12 rounds**。

- 由 `scripts/generate_round_cases.py` 生成
- 每轮真实执行 `wf.py append-status`、`state`、`new-round`
- 包含 12 个 STATUS、12 条决策、`ROUNDS.md`、`ROUNDS.json`、证据日志
- 已脱敏：无个人路径、密钥、真实项目数据
