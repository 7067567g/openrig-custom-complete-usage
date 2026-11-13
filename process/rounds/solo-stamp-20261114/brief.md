# SOLO-20261114-08 · 单独轮独立识别标戳

- 类型：单独轮（STANDALONE）
- 别名：离散轮 / 零散轮
- 主策略：GOVERN + OPS
- Anchor：R15；Rejoin：R16
- 目标：为所有单独轮增加独立识别标戳，便于检索、收集、归档；单独轮可以散落在任意目录，但必须有统一 stamp。

## 标戳设计

- 每个单独轮根目录放 `.solo-round.json`（机器可读）
- stamp 必填：
  - schema / stampVersion
  - id（SOLO-YYYYMMDD-NN）
  - aliases（DISCRETE/SCATTERED）
  - strategy / status / anchor / rejoin
  - owner / registry / source / stampPath
  - createdAt / updatedAt
- 可选：主文档 marker `<!-- solo-round: SOLO-... -->` 或 frontmatter，但 stamp 文件是主真值。

## 工具

新增 `tools/solo-round-stamp.mjs`：

- `stamp --id <id> --dir <dir>`：写/更新 `.solo-round.json`
- `collect --root <dir>`：收集所有 stamp，输出 JSON
- `verify`：校验 stamp ↔ STANDALONE-ROUNDS.json 一致、ID 唯一、路径存在
- `find <id>`：按 ID 找路径

## 需要补齐的现有单独轮

从 `reports/rounds/STANDALONE-ROUNDS.json` 全量生成 stamp，至少包括：

- SOLO-20261026-01
- SOLO-20261113-01..04
- SOLO-20261114-01..08（含本轮 SOLO-07/SOLO-08 自身）

不登记为单独轮的 out-of-scope 项不加 stamp。

## 输出

- `docs/rounds/SOLO-STAMP-PROTOCOL.md`
- `tools/solo-round-stamp.mjs`
- `reports/rounds/SOLO-STAMP-COLLECTION.json`
- `reports/rounds/SOLO-STAMP-COLLECTION.md`
- `reports/rounds/SOLO-STAMP-VERIFY.md`
- 更新 `STANDALONE-ROUNDS.json` / `.md`，增加 stampPath/stampStatus
- 更新引用索引/协议

## 约束

- 只写治理/工具/报告；不改产品代码；
- 不移动/重命名单独轮来源目录；stamp 就地放置；
- 不提交原始截图/聊天正文/token。
