[English](CONCEPTS.md) | **简体中文**

# 概念（本地术语表）

这里给从本仓库进入的读者一页术语。深入材料维护在 `SCTG-public` 的
`v0.5.1` tag。

| 术语 | 在本仓库中的含义 |
|---|---|
| **Card** | 有界任务：输入、写范围、交付物、gate。 |
| **Seat** | rig 中的一个 agent 身份；一次只接一张 active card。 |
| **Submission** | 生产者结构化结果：summary、changed files、commands、evidence。 |
| **Gate** | 确定性结构检查：schema、scope、evidence、command。 |
| **Decision** | 不可逆动作的独立批准/replay 记录。 |
| **Ledger** | 只追加事件历史；不是聊天 transcript。 |
| **Round** | workflow-group 的一轮 PMO -> TDO -> QA -> MAIN。 |
| **Bridge** | `OPENRIG-BRIDGE.json`：控制面事实到执行面状态的映射。 |
| **Control plane** | workflow-group 文档：PROJECT、SPEC、DECISIONS、STATUS、ISSUES。 |
| **Execution plane** | OpenRig：rig、seats、queue、workflow、transcripts、snapshots。 |

固定参考：[`SCTG-public@v0.5.1`](https://github.com/7067567g/SCTG-public/tree/v0.5.1)。
