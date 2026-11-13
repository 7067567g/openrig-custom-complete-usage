# SYNC-GUARD · QUIET-200 后续 + 引用链接 + 多文件夹一致性

- 日期：2026-11-14
- 类型：治理/后续分析轮，不改产品代码
- 锚点：R15（最后已闭合主链轮）
- 回归点：R16（仍 NEED_MAIN，不跳过）
- 父支线：`UX6-R15` / `feat/r15-ux6`
- 子支线：`QUIET-200` / `feat/quiet-200`

## 目标

1. 审阅 `QUIET-200-IMPLEMENTATION-PLAN` 的未决问题，给出可执行默认决策；
2. 建立跨文档引用索引，保证 branch → issue → plan → evidence 双向可追溯；
3. 盘点多文件夹职责，定义 source-of-truth、只读快照、生成物和禁止手改区域；
4. 设计“仓库同步 + 多文件夹一致性”检查规则，给出可落地命令/门禁；
5. 产出后续行动清单，不进入代码实现。

## 必读输入

- `docs/BRANCHING-PROTOCOL.md`
- `docs/branches/UX6-R15.md`
- `docs/branches/QUIET-200.md`
- `reports/branches/BRANCH-LEDGER.json`
- `reports/issues/SIX-ISSUES-INTAKE-20261113.md` / `.json`
- `reports/issues/QUIET-200-IMPLEMENTATION-PLAN.md` / `.json`
- `discussions/quiet-200-20261114/BRIEF.md`
- 目录盘点：
  - 主仓：`bridge repo`
  - 外部原生：`bridge-app`
  - 治理 staging：`governance-20261110/staging/bridge repo`
  - 历史快照：`governance-20261110/snapshots/**`
  - 分发包：`dist/v3 workspace-share-20261025`
  - 其他备份/无关目录：`the assistant project-备用/**`、`qq-bridge*`

## QUIET-200 待决问题

1. 分支基线：`280de35` vs 当前 remediation 工作树（含未提交 R17–R20 改动）如何定？
2. IndexedDB 明文缓存是否接受？清空/删除/退出登录时如何清理？
3. 最近 200 条是否包含媒体？v1 只缓存元数据是否接受？
4. 全局 2000 LRU 是否保护当前会话最近 200？
5. 消息身份 key 优先级：id / mid / clientMessageId / 指纹？
6. 离线缓存文案与范围提示最终措辞？
7. 清屏是否清缓存？
8. 预加载阈值用 1.5/2.5 屏 + 40 行/秒，还是 px/s？
9. U2a 是否把 historyMessages 上限从 1000 提到 2000？

## 多文件夹一致性要求

- 明确哪些目录是 source-of-truth，哪些是只读快照/生成物，哪些是外部仓；
- 不得把历史快照或 staging 当成可编辑主线；
- 文档引用必须用仓库相对路径或稳定的绝对路径，禁止引用 `/tmp` 原始截图；
- 不能把原始截图、聊天正文、token 入库；
- 给出“同步检查”建议：需要检查哪些文件、哪些允许差异、哪些必须一致；
- 产出可复制的检查命令/门禁草案（本轮不实现脚本也可）。

## 输出

- `reports/issues/QUIET-200-FOLLOWUP.md`
- `docs/branches/REFERENCE-INDEX.md`
- `reports/branches/SYNC-GUARD.md`
- `reports/branches/SYNC-MANIFEST.json`

约束：只读代码；只写上述四个报告/索引文件；不改产品代码、不提交原始截图/聊天正文。
