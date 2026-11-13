# templates/baseline — 基准模板（复合类型重点参考）

> **类定义**：基准模板是“复合类型”的稳定参考模板。它把多个原子轮型组合成一条标准管线，并记录主攻方向、特点、强制证据、领域参考和成熟度。
> **不是 run 模板**：基准模板不能直接传给 `wf.py new-run --template`；它不提供可直接执行的四件套。实例化时使用 `templates/specialized/<domain-template>`，在其 `SPEC.md` §0 引用 baseline id/version。

## 文件

| 路径 | 作用 |
| --- | --- |
| `VERSION` | 基准模板集版本 |
| `REGISTRY.md` | 人读注册表：每个基准模板的主攻方向/特点/契约/参考 |
| `REGISTRY.json` | 机器注册表，供工作流/插件读取 |
| `<name>/BASELINE.md` | 单个复合类型的完整基准说明 |
| `FREEZE-NOTES.md` | 基准模板集的来源、成熟度与升级记录（当前 1.1.0） |

## 当前基准模板

| baseline | 主攻方向 |
| --- | --- |
| `fix-wave` | 票源驱动修复，验证→修订→复跑→门禁化 |
| `refactor-decompose` | 先 100% 归属/冻结/门禁基线，再分区行为不变重整 |
| `ops-hardening` | 分发/同步/调度/入口可靠性，恢复性与负向门优先 |
| `safe-cleanup` | move-only + action digest + SAFETY + 人工批准的真实文件整理 |
| `knowledge-pipeline` | 来源入库→检索消费→方法实战回写 |
| `two-plane-orchestration` | workflow-group 控制面 + OpenRig 执行面 |
| `postmortem-meta-governance` | 复盘/角色/规则/模板的元治理回写 |
| `product-redesign-live` | 反目标→多 seat 设计→staging→live/回滚 |
| `hypothesis-analysis` | 未知项的假设矩阵 + 置信度 + 可证伪实验 |

## 使用规则

1. **先选 baseline，再选 specialized template**；没有合适 baseline 时，用原子轮型组合并记录理由。
2. 现有 26 个领域模板的映射见 [`../specialized/BASELINE-MAP.md`](../specialized/BASELINE-MAP.md)；新增模板必须补行。`issue-sync` 已是 specialized adapter（不再是 baseline）。
3. 在 `SPEC.md` §0 显式写：
   ```text
   baseline: composite/<name>@1.0.0
   contracts: <type>@1.0.0, ...
   ```
4. `ROUND-PLAN.md` 每轮只执行一个原子契约；按 `BASELINE.md §3` 的默认管线推进。
5. 领域 SPEC 可以加严，但不能删掉 baseline 的强制证据与风险修饰。
6. 基准模板只通过版本升级变更；变更需改 `VERSION`、`REGISTRY.md/json` 与对应 `BASELINE.md`，并同步标签清单。
