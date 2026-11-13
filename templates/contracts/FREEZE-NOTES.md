# FREEZE-NOTES — 原子轮型冻结记录

## 1.2.0 — 2026-11-11

- **变更**：基础母版 `workflow-group-base` 由 `1.1.0` 升为 `1.2.0`。变更面为规范/角色/模板契约修复：新增 `WORKFLOW.md §0` 权威链，明确 S0 bootstrap 单一写者例外，补齐状态迁移 `--by` 命令，修正回执口径与失效引用，并在 `templates/PROJECT.md` 同步写者边界。
- **原子契约语义未变**：`templates/contracts/VERSION` 仍为 `1.0.0`，7 个原子轮型及其 `_shared/**` 语义未改。
- **重签范围**：`LOCK.json` 重签基础母版与 `templates/contracts/**` 的 sha256；`contractSet.version` 保持 `1.0.0`。
- **新增关闭门**：`scripts/wf_close_lint.py` 为只读关闭语义 linter；新 run 在 `PROJECT closed` 前必须 ERROR=0，历史 run 的已知违规登记在 `reports/close-lint-20261111.txt`。
- **迁移影响**：旧 run/旧 SPEC 不需要改写；新 run 的 `SPEC.md §0` 仍写 `contracts: <type>@1.0.0`。引用 base 版本处应写 `workflow-group-base@1.2.0`。

## 1.1.0 — 2026-10-23

- **变更**：基础母版 `workflow-group-base` 由 `1.0.0` 升为 `1.1.0`。变更面仅为文档降噪与术语单一来源：`roles/*.md` 与 `AGENTS.md` 清退退役术语字面（操作语义保留）、`WORKFLOW.md §2/§4.3` 改用通用表述并删除 `issue-sync` baseline 行，另新增 `tests/test_doc_noise.py` 机检。
- **原子契约语义未变**：`templates/contracts/VERSION` 仍为 `1.0.0`，7 个原子轮型（`strategy / research / diff / architecture / optimize / verify / audit`）与 `_shared/**` 的语义和字节均未改动。
- **重签范围**：本次 `LOCK.json` 重签只反映 `BASE-MASTER.md`、`FREEZE-NOTES.md` 两个元数据文档的哈希变化；`contractSet.version` 保持 `1.0.0`。
- **建模说明**：`contractSet.files` 由 `scripts/contract_lock.py` 的 `rglob` 收集 `templates/contracts/**` 下全部 `.md` 与 `VERSION` 得到，因此这两份说明文档也在表内——这是脚本收集口径的产物，不代表它们是 contract-set 契约本体。
- **事实源**：基础母版身份与文件哈希以 `templates/contracts/LOCK.json` 为准；本记录只解释变更理由与迁移影响。
- **迁移影响**：旧 run/旧 SPEC 不需改写；新 run 的 `SPEC.md §0` 仍写 `contracts: <type>@1.0.0` 不变。引用 base 版本处应写 `workflow-group-base@1.1.0`。

## 1.0.0 — 2026-10-23

- **冻结对象**：`strategy / research / diff / architecture / optimize / verify / audit` 7 个原子轮型。
- **基础母版**：`workflow-group-base@1.0.0`；由 `WORKFLOW.md`、`roles/*`、四件套母版共同定义。
- **来源**：`60-外部仓库/workflow-group/round-types/` 的 7 类轮型契约 + `WORKFLOW-TAGS.md` 的横比结论。
- **做了什么**：
  - 把 gugu 领域路径/预算/边界从通用契约中剥离，改成 `domain_adapter_hooks`；
  - 统一 `purpose / requires / produces / mandatory_gates / hard_boundaries / budget_defaults / done / handoff` 接口；
  - 新增 `_shared/PLAN-GATE.md`（7/7）与 `_shared/VERDICT.md`；
  - 以 `LOCK.json` 绑定基础母版与契约 sha256，新增 `scripts/contract_lock.py check`。
- **兼容性**：旧 run/旧 SPEC 不需要改写；新 run 通过 `SPEC.md §0` 引用契约版本，`ROUND-PLAN.md` 声明本轮唯一 `contract:`。
- **未包含**：领域路径、测试入口、发布四件套、风险评估——由领域 adapter 与 `templates/baseline/` 负责。
- **升级规则**：只增不改；变更必须升 `VERSION`、写本记录、更新 `LOCK.json`，再跑 `python3 scripts/contract_lock.py check`。
