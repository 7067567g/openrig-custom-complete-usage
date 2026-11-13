# INSERT-GUARD · 中途插入内容流程

- 日期：2026-11-14
- 类型：治理/流程商讨，不改产品代码
- 关联：
  - `docs/BRANCHING-PROTOCOL.md`
  - `docs/CLOSEOUT-MANUAL.md`
  - `docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`
  - `reports/branches/SYNC-GUARD.md`、`reports/branches/SYNC-MANIFEST.json`
  - 正式 30 轮当前停在 R16 NEED_MAIN
- 问题：我跑到一半，想插入一条新内容/新要求/新 bug，应该怎么进入流程？

## 目标

设计一套标准、可复用、可审计的“中途插入”流程：

1. 判断插入类型：澄清、同轮扩展、新轮、新支线、紧急中止、验收变更；
2. 定义插入点：当前 round / 下一轮 / 新支线 / STOP-SWEEP；
3. 定义不打断当前工作的默认策略；
4. 定义必须打断/中止的硬条件；
5. 定义插入记录（ID/来源/时间/锚点/分支/scope/owner/状态）；
6. 定义插入如何被下一轮消费、如何验收、如何关闭；
7. 与 QA、STOP-SWEEP、分支收敛、R15/R16 锚点兼容。

## 建议的插入分类

- `CLARIFY`：澄清当前轮，不扩 scope，不改 gate；
- `INLINE_EXTEND`：当前轮能吸收的小扩展，需要 owner 确认并更新卡/证据；
- `NEXT_ROUND`：新内容排队到当前分支下一轮；
- `SIDE_BRANCH`：独立支线/新分支，锚定最后闭合轮；
- `URGENT_STOP`：当前轮已不安全/会污染结论，走 STOP-SWEEP；
- `GATE_CHANGE`：验收/契约变更，当前轮结果失效，重开或重跑。

## 输出

- `reports/operations/MIDRUN-INSERTION.md`
- `reports/operations/MIDRUN-INSERTION.json`
- `docs/MIDRUN-INSERTION-PROTOCOL.md`（标准版、长期复用）
- `reports/operations/INSERTION-LEDGER-TEMPLATE.json`
- 更新 `docs/branches/REFERENCE-INDEX.md` 与 `docs/BRANCHING-PROTOCOL.md` 的引用

## 约束

- 只写治理/报告/索引；不改产品代码；
- 不提交原始截图/聊天正文/token；
- 不把“插入”静默塞进当前 packet 造成 scope drift；
- 插入记录必须可追溯，不能只靠聊天记忆。
