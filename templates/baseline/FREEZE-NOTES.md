# FREEZE-NOTES — 基准模板集记录

## 1.1.0 — 2026-10-23

- **变更**：`issue-sync` 从复合类型基准模板降级为 `templates/specialized/issue-sync/` adapter（canonical 领域特化零引用）；baseline 由 10 项收敛为 9 项，其余 9 项内容不变。
- **冻结对象**：9 个复合类型基准模板：
  `fix-wave / refactor-decompose / ops-hardening / safe-cleanup / knowledge-pipeline / two-plane-orchestration / postmortem-meta-governance / product-redesign-live / hypothesis-analysis`。
- **成熟度**：不集中调整。M3 6 个（fix-wave / ops-hardening / safe-cleanup / knowledge-pipeline / two-plane-orchestration / hypothesis-analysis），M2 3 个（refactor-decompose / postmortem-meta-governance / product-redesign-live）。`issue-sync` 的 M2 标记随 adapter 沿用，不再计入 baseline 统计。
- **与领域模板关系**：现有 26 个领域模板的映射见 `../specialized/BASELINE-MAP.md`；新增模板必须补行并在 SPEC §0 引用 baseline/contracts，`scripts/doc_consistency.py --check` 校验一一对应。
- **升级规则**：修改 baseline 必须升 `VERSION`、更新 `REGISTRY.md/json` 与本记录；领域 run 引用固定版本，不跟随目录最新内容漂移。

## 1.0.0 — 2026-10-23

- **冻结对象**：10 个复合类型基准模板：
  `fix-wave / refactor-decompose / ops-hardening / safe-cleanup / knowledge-pipeline / two-plane-orchestration / postmortem-meta-governance / product-redesign-live / issue-sync / hypothesis-analysis`。
- **来源**：`WORKFLOW-TAGS.md` 的复合类型收束候选 + canonical/外部/obsidian 的成熟特化样本。
- **类语义**：基准模板是复合类型的**重点参考**，不是 run 模板；不得直接传给 `wf.py new-run --template`。
- **成熟度**：M3 6 个（fix-wave / ops-hardening / safe-cleanup / knowledge-pipeline / two-plane-orchestration / hypothesis-analysis），M2 4 个（refactor-decompose / postmortem-meta-governance / product-redesign-live / issue-sync）。
- **与原子契约关系**：每个 baseline 只能选 `templates/contracts/` 已冻结的 contract + version；不另造轮型。
- **与领域模板关系**：当时现有 22 个领域模板的映射见 `../specialized/BASELINE-MAP.md`；新增模板必须补行并在 SPEC §0 引用 baseline/contracts。
- **升级规则**：修改 baseline 必须升 `VERSION`、更新 `REGISTRY.md/json` 与本记录；领域 run 引用固定版本，不跟随目录最新内容漂移。
