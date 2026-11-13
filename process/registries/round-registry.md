# OpenRig 总指挥部 · 轮次登记视图

- 版本：`v1.0.0`（2026-11-14）
- 机器台账：`reports/command-center/ROUND-REGISTRY.json`
- 协议：`docs/command-center/COMMAND-CENTER.md`
- CLI：`node tools/round-command-center.mjs list|show|conflicts|validate`
- Owner：Lead/MAIN
- 边界：登记**非 SOLO** 的长运行轮/主支；SOLO 由 `reports/rounds/STANDALONE-ROUNDS.json` 管理。

## 1. 当前登记

| ID | Kind | Status | Current round | Branch | Head | Owner |
|---|---|---|---|---|---|---|
| `FORMAL-30-20261113` | formal | **blocked** | R16 | `remediation/20261113` | `dcd9f93` | MAIN |
| `REMEDIATION-20261113` | integration | active | R16 | `remediation/20261113` | `dcd9f93` | Lead/MAIN |
| `UX6-R15` | branch | active | UX6-R15 | `feat/r15-ux6` | `dcd9f93` | Lead |
| `QUIET-200` | branch | active | UX6-R15-02a/02b | `feat/quiet-200` | `dcd9f93` | Lead |
| `FAST-RESPONSE` | branch | active-qa-ready | FAST-RESPONSE-QA | `feat/fast-response` | `7ad2c24` | Lead/QA |
| `ANDROID-UX6-R15-06` | external | planned | ANDROID-UX6-R15-06 | `TBD` | `UNKNOWN` | Android/Lead |

## 2. 状态/基线备注

- `FORMAL-30-20261113`：15/30 passed；R16 **NEED_MAIN**；`terminal=false`；无 DONE/PASS。
- `REMEDIATION-20261113`：集成线；主工作树审计时 clean；最终 `remediation → main`。
- `UX6-R15` / `QUIET-200`：父子支线；当前同一 worktree（`feat/quiet-200`），审计时 clean。
- `FAST-RESPONSE`：独立 worktree clean；ADB 27/27、debug 24/24；ledger base `f973b3f`，审计观测实际 merge-base B2 `7680b1d`，QA 前需修 base 元数据。
- `ANDROID-UX6-R15-06`：planned external；不参与 active 冲突检测。

## 3. 冲突候选（按 resourceKey 重叠 + active）

当前 active 条目中：

| A | B | 共享 resourceKey | 说明 |
|---|---|---|---|
| `UX6-R15` | `QUIET-200` | `path:sim/app.js` | **已知父子重叠**；不是未知冲突，但并发编辑前必须按父子顺序协调 |

- `FORMAL-30`、`REMEDIATION`、`FAST-RESPONSE` 与上述无共享 active resourceKey。
- 冲突查询只读本 registry，不遍历全库；CLI 输出为准。

## 4. CLI

```bash
cd <BRIDGE_REPO>
node tools/round-command-center.mjs list
node tools/round-command-center.mjs list --active
node tools/round-command-center.mjs show FAST-RESPONSE
node tools/round-command-center.mjs conflicts
node tools/round-command-center.mjs validate
```

- `list`：全部登记；`--active` 只看 active 状态。
- `show <id>`：单条详情。
- `conflicts`：active 条目两两 resourceKey 交集。
- `validate`：schema/字段/唯一 ID/active 必填/冲突键子集；`--strict` 将冲突也视为失败。
- 全部命令支持 `--json`，便于自动化。

## 5. 维护时机

长运行轮/主支在以下时点必须更新 registry：

1. 开始（status active，写 owner/branch/worktree/base/head/currentRound/scope/resourceKeys）。
2. 切轮/换 currentRound。
3. 停止/阻塞（status blocked/waiting/paused + wait reason）。
4. 合并/完成/废弃（status merged/done/abandoned + links）。
5. 每次审计/交接后更新 `lastSeenAt`。

## 6. 引用

- `docs/command-center/COMMAND-CENTER.md`
- `reports/command-center/ROUND-REGISTRY.json`
- `tools/round-command-center.mjs`
- `reports/branches/BRANCH-LEDGER.json`
- `reports/sctg/FORMAL-RUN-STATE.json`
- `docs/branches/REFERENCE-INDEX.md`
- `docs/BRANCHING-PROTOCOL.md`


## 7. 验证（2026-11-14）

| 命令 | 结果 |
|---|---|
| `node --check tools/round-command-center.mjs` | PASS |
| `node tools/round-command-center.mjs validate` | OK：6 entries / 5 active / 1 conflict candidate（warning） |
| `node tools/round-command-center.mjs validate --strict` | exit 1（已知 UX6/QUIET 父子冲突；符合 strict 语义） |
| `node tools/round-command-center.mjs list --json` | 6 entries，IDs 与 registry 一致 |
| `node tools/round-command-center.mjs list --active` | 5 active（formal blocked 计入） |
| `node tools/round-command-center.mjs show FAST-RESPONSE` | status/branch/head/currentRound/owner 正确 |
| `node tools/round-command-center.mjs conflicts` | 1 个：UX6-R15 ↔ QUIET-200，shared `path:sim/app.js` |

详见 `reports/command-center/COMMAND-CENTER-VERIFY.md`。
