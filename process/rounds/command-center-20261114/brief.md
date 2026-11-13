# SOLO-20261114-07 · OpenRig 总指挥部（轮次集散中心）

- 类型：单独轮（STANDALONE）
- 别名：离散轮 / 零散轮
- 主策略：GOVERN + OPS
- Anchor：R15；Rejoin：R16
- 目标：建立 OpenRig 总指挥部/轮次集散中心，登记所有**非单独轮**的长运行轮/主支；
  提供 ID、简况、owner、branch、base、anchor/rejoin、scope、resourceKeys/conflictKeys，
  支持不遍历全库即可查运行中任务和冲突。

## 必须登记的对象

当前已知：
- `FORMAL-30-20261113`：正式 30 轮（R16 NEED_MAIN，15/30）
- `REMEDIATION-20261113`：集成线 `remediation/20261113`
- `UX6-R15`：父支线 `feat/r15-ux6`
- `QUIET-200`：子支线 `feat/quiet-200`
- `FAST-RESPONSE`：支线 `feat/fast-response`（active-qa-ready）
- `ANDROID-UX6-R15-06`：planned external `bridge-app`

不登记：
- 单独轮（SOLO-*）→ 由 STANDALONE registry + stamp 管理。

## 必须定义的字段

- id / kind / title / status / owner
- branch / worktree / baseCommit / headCommit
- anchorRound / rejoinRound / currentRound
- scope / resourceKeys / conflictKeys
- lastSeenAt / updatedAt / links / notes
- 冲突查询语义（同一个 resourceKey 被两个 active 项占用 = 冲突候选）

## 输出

- `docs/command-center/COMMAND-CENTER.md`（标准协议）
- `reports/command-center/ROUND-REGISTRY.json`（机器台账）
- `reports/command-center/ROUND-REGISTRY.md`（人读视图）
- `tools/round-command-center.mjs`（list/show/conflicts/validate）
- 更新 `docs/branches/REFERENCE-INDEX.md`、`docs/BRANCHING-PROTOCOL.md` 引用

## 约束

- 只写治理/台账/工具；不改产品代码；不清理/重置工作树；
- 不登记单独轮；
- 不把全库遍历作为常规查询方式；查询以 registry/CLI 为准；
- 不提交原始截图/聊天正文/token。
