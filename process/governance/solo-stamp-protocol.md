# 单独轮标戳标准协议（SOLO STAMP）

- **协议版本**：`v1.0.0`（standard，2026-11-14）
- **状态**：`standard / reusable` —— 长期复用的单独轮识别/收集标准，不是一次性脚本说明。
- **范围**：所有 `SOLO-YYYYMMDD-NN` 单独轮（含已关闭/运行中）；不登记 out-of-scope 项。
- **主真值**：每个单独轮根目录的 `.solo-round.json` 是**主真值**；主文档 marker 可选。
- **维护者**：Lead/MAIN + QA lead；见 §10 变更记录。
- **工具**：`tools/solo-round-stamp.mjs`（`stamp` / `collect` / `verify` / `find`）。
- **台账**：`reports/rounds/STANDALONE-ROUNDS.json`（stampPath/stampStatus 同步）。
- **相关**：`docs/rounds/STANDALONE-ROUND-PROTOCOL.md`、`reports/command-center/ROUND-REGISTRY.json`、`docs/branches/REFERENCE-INDEX.md`。

---

## 0. 原则

1. **stamp 是主真值**：只要 `.solo-round.json` 存在且 `verify` 通过，就以 stamp 为准；主文档/README 的 marker 只是辅助。
2. **就地放置**：stamp 放在该单独轮的根目录，不移动/重命名来源目录。
3. **不重复**：一个 `SOLO-ID` 只能有一个 stamp；ID 唯一。
4. **out-of-scope 不加 stamp**：QUIET/UX6/正式轮/输出物等不登记为 SOLO 的，不加 `.solo-round.json`。
5. **可验证**：stamp ↔ registry ↔ 路径三方一致；`verify` 失败必须修，不静默忽略。

---

## 1. 放置路径

```text
<round-root>/.solo-round.json
```

示例：

| SOLO | root | stamp |
|---|---|---|
| `SOLO-20261113-01` | `discussions/fast-response-adb-20261113/` | `discussions/fast-response-adb-20261113/.solo-round.json` |
| `SOLO-20261113-04` | `reports/compare-20261113/` | `reports/compare-20261113/.solo-round.json` |
| `SOLO-20261114-08` | `discussions/solo-20261114-08/` | `discussions/solo-20261114-08/.solo-round.json` |

- `root` 必须是实际存在的目录；不创建/移动来源目录。
- `stampPath` 写绝对路径，便于跨 worktree/归档后定位。
- 不把 stamp 写到 `out-of-scope` 目录（如 `feat/quiet-200` 工作树根、正式轮报告根）。

---

## 2. Schema

```json
{
  "schema": "example-solo-round-stamp/v1",
  "stampVersion": "v1.0.0",
  "id": "SOLO-YYYYMMDD-NN",
  "aliases": ["DISCRETE", "SCATTERED"],
  "title": "<short title>",
  "strategy": "<GOVERN|ANALYZE|OPS|QA|SMALL_FIX|RESEARCH|RECOVERY>[+<secondary>]",
  "status": "<CLOSED|RUNNING|ACTIVE|BLOCKED|ABANDONED|ARCHIVED>",
  "anchor": "R15",
  "rejoin": "R16",
  "owner": "<session/role>",
  "registry": "<absolute path to STANDALONE-ROUNDS.json>",
  "source": ["<source paths>"],
  "sourceRoot": "<absolute round root>",
  "stampPath": "<absolute path to .solo-round.json>",
  "createdAt": "<ISO>",
  "updatedAt": "<ISO>",
  "notes": "<short; no sensitive content>"
}
```

### 2.1 必填

`schema` / `stampVersion` / `id` / `aliases` / `strategy` / `status` / `anchor` / `rejoin` / `owner` / `registry` / `source` / `stampPath` / `createdAt` / `updatedAt`。

### 2.2 规则

- `schema` 固定 `example-solo-round-stamp/v1`；`stampVersion` 当前 `v1.0.0`。
- `id` 必须匹配 `^SOLO-\d{8}-\d{2}$`，且与 registry 唯一。
- `aliases` 至少包含 `DISCRETE`/`SCATTERED`。
- `strategy`/`status`/`anchor`/`rejoin`/`owner` 与 registry 一致；`status` 用 registry 的 `CLOSED`/`RUNNING` 等。
- `registry` 写绝对路径；`source` 保留来源；`sourceRoot`/`stampPath` 是绝对路径。
- `createdAt` 首次写入保留；`updatedAt` 每次 `stamp`/状态变化更新。
- 不含原始截图/聊天正文/token/logcat。

---

## 3. 主文档 marker（可选）

可在单独轮主文档顶部写：

```markdown
<!-- solo-round: SOLO-20261114-08 -->
```

或 frontmatter `solo_round: SOLO-...`。

- marker 只做人类可读提示；**stamp 文件是主真值**。
- marker 与 stamp 不一致时，以 stamp 为准，并修 marker。
- 没有 marker 不影响 `verify`。

### 3.1 沙箱/只读 fallback

如果来源目录在沙箱中不可写（例如 `discussions/*` 在 repo workspace 外），允许写 **mirror stamp**：

```text
reports/rounds/stamps/<SOLO-ID>/.solo-round.json
```

- stamp 增加 `stampMode: "mirror"` 与 `stampTarget: "<sourceRoot>/.solo-round.json"`；`stampPath` 指向 mirror。
- `stampStatus` 记为 `MIRROR`；`verify` 给 warning，不当作 in-place 成功。
- 宿主有写权限时，必须把 mirror stamp 复制到 `stampTarget`，再跑 `verify`，`stampStatus` 才能改 `OK`。
- in-place 仍是主路径；mirror 只是受限环境的降级，不是标准替代。

---

## 4. CLI

```bash
# 写/更新一个 stamp
node tools/solo-round-stamp.mjs stamp --id SOLO-20261114-08 --dir discussions/solo-20261114-08

# 按 registry 全量补齐（confirmed/candidate，sourceRoot 存在）
node tools/solo-round-stamp.mjs stamp --all

# 收集 root 下所有 stamp
node tools/solo-round-stamp.mjs collect --root <WORKSPACE>

# 校验 stamp ↔ registry ↔ 路径
node tools/solo-round-stamp.mjs verify

# 按 ID 找
node tools/solo-round-stamp.mjs find SOLO-20261114-08
```

选项：

- `--registry <path>`：默认 `reports/rounds/STANDALONE-ROUNDS.json`。
- `--root <dir>`：collect/verify 可重复；默认 workspace root（repo 的父目录）。
- `--json`：机器输出。
- `stamp --all`：只处理 registry 中 `classification=confirmed|candidate` 且有 `sourceRoot` 的条目；不碰 out-of-scope。

退出码：0 成功；1 verify/find 失败；2 用法/IO/JSON 错误。

---

## 5. 更新规则

| 事件 | 动作 |
|---|---|
| 新建单独轮 | 先在 registry 登记，再 `stamp --id` 写 stamp；status `RUNNING`/`PROPOSED` |
| 状态变化（QA/CLOSED/ABANDONED） | 更新 registry，再 `stamp` 重写（`updatedAt` 变化） |
| 切目录/归档 | 不移动来源；stamp 随根目录移动；更新 `sourceRoot`/`stampPath` |
| 关闭/归档 | stamp 保留；status 改 CLOSED/ARCHIVED；不删 |
| 发现重复/漂移 | `verify` 报错；修 registry/stamp，不静默跳过 |

---

## 6. verify 检查

`node tools/solo-round-stamp.mjs verify`：

- registry 可解析；entries 为数组；ID 唯一。
- 每个 confirmed/candidate 有 `sourceRoot`/`stampPath`；文件存在。
- stamp 的 `id/status/strategy/anchor/rejoin/owner` 与 registry 一致。
- `stamp.schema`/`stampVersion` 正确；`stampPath` 与 registry/文件路径一致。
- 没有 out-of-scope 条目被加 stamp。
- 没有额外 stamp（不在 registry 的 `.solo-round.json`）——按 `--root` 收集范围。
- 路径存在、无重复 ID。

失败必须修；`verify` 不通过不算收口。

---

## 7. collect 输出

`collect --root <dir>` 输出：

```json
{
  "schema": "example-solo-stamp-collection/v1",
  "generatedAt": "<ISO>",
  "root": "<dir>",
  "count": 13,
  "stamps": [
    {"path": "<...>/.solo-round.json", "stamp": {"id": "SOLO-...", "...": "..."}}
  ]
}
```

只读扫描 `.solo-round.json`；不读聊天/图片/产品源码。

---

## 8. 与其它协议

| 对象 | 关系 |
|---|---|
| `STANDALONE-ROUND-PROTOCOL` | 定义单独轮生命周期/字段；stamp 是其机器识别 |
| `STANDALONE-ROUNDS.json` | 主台账；stampPath/stampStatus 同步 |
| `COMMAND-CENTER` | 非 SOLO 长运行轮登记；stamp 不替代 command center |
| `CLOSEOUT-MANUAL` | 停止/归档时更新 status/stamp；不删除 stamp |
| `BRANCHING-PROTOCOL` | 单独轮升级支线时，stamp 保留来源记录 |
| R15/R16 | anchor R15，rejoin R16；不跳过 R16 |

---

## 9. 隐私/安全

- stamp 只存 ID/title/path/status/owner/strategy，不存聊天正文/token/原始截图。
- `collect` 只读 `.solo-round.json`，不读其它文件。
- 共享设备上，`sourceRoot` 不写用户隐私目录。

## 10. 变更记录

| 版本 | 日期 | 作者/角色 | 变更 |
|---|---|---|---|
| v1.0.0 | 2026-11-14 | builder / MAIN review | 建立 stamp schema/放置/主真值/marker/CLI/verify/collect/更新规则。 |
| v1.0.1 | `<YYYY-MM-DD>` | `<maintainer>` | `<change>` |
