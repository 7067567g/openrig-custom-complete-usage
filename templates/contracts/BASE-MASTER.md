# BASE-MASTER — 原子轮型所依附的基础母版

> 本文件定义“冻结原子轮型”的基座，不重复 `WORKFLOW.md` / `roles/` 的规则。
> 冲突时以 `WORKFLOW.md` / `roles/` 为准；本文件只说明兼容边界和冻结协议。

## 1. 基础母版身份

| 项         | 值                                                                                 |
| ---------- | ---------------------------------------------------------------------------------- |
| id         | `workflow-group-base`                                                              |
| version    | `1.2.0`（2026-11-11 规范/角色/模板契约修复后升版；7 个原子契约语义未变；历史版本 `1.1.0`、首次冻结 `1.0.0`） |
| 规范正文   | `WORKFLOW.md`                                                                      |
| 角色契约   | `roles/common-contract.md` + `roles/{MAIN,PMO,TDO,QA,SAFETY}.md`                   |
| 四件套母版 | `templates/{PROJECT,DECISIONS,STATUS-Round-n,ISSUES.xlsx}`                         |
| 执行面扩展 | `templates/specialized/openrig-workflow-master@1.2.0`（可选；用于双平面 baseline） |

## 2. 原子轮型与基础母版的关系

- 原子轮型只增加“单轮输入/产出/门禁/预算/交接”的接口，不覆盖四条硬约束。
- 每次原子轮仍运行在具体 run 的四件套中：PROJECT 定目标/范围，DECISIONS 拍板，STATUS 承接进度，ISSUES 记录问题。
- `templates/contracts/LOCK.json` 记录基础母版文件的 sha256；基础母版变更后必须按 §4 重新冻结。

## 3. 领域 adapter 的职责

领域 adapter（canonical/外部/本地化 `SPEC.md`）负责：

1. 提供对象路径、写权限白名单、测试/证据入口和风险修饰；
2. 把原子契约的 `produces` 映射到本领域文件；
3. 声明额外强制门（如安全门控、发布四件套、全内容覆盖）；
4. 不改变原子契约的“必产/强制门/完成定义”最小集。

## 4. 冻结协议

- **只增不改**：要改变已冻结契约，必须新建版本（如 `research@1.1.0`），旧版本在 `LOCK.json` 中保持可核验。
- **版本升级**：更新 `templates/contracts/VERSION` + 所有受影响契约 ID + `LOCK.json`；在 `CHANGELOG` 或 `FREEZE-NOTES.md` 写变更理由与迁移影响。
- **核验命令**：`python3 scripts/contract_lock.py check`；CI/收口前必须 rc=0。
- **回滚**：若冻结变更失败，按 `LOCK.json` 恢复文件并重新核验；不得只改部分文件。
