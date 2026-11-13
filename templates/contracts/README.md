# templates/contracts — 冻结的原子轮型

> 这里不是 run 模板，不能直接传给 `wf.py new-run --template`。
> 原子轮型是单轮的最小稳定接口；复合类型见 `templates/baseline/`，领域特化见 `templates/specialized/`。

## 文件

| 路径 | 作用 |
| --- | --- |
| `VERSION` | 当前冻结版本 |
| `BASE-MASTER.md` | 原子轮型依附的基础母版与冻结协议 |
| `_shared/PLAN-GATE.md` | 开工前 7/7 计划门 |
| `_shared/VERDICT.md` | 每轮 CONTINUE/ADJUST/STOP 判词 |
| `<type>/CONTRACT.md` | 7 个原子轮型契约 |
| `LOCK.json` | 基础母版 + 契约文件的 sha256 冻结清单 |
| `FREEZE-NOTES.md` | 本次冻结的来源、改动、兼容性与升级记录 |

## 七个原子轮型

`strategy` · `research` · `diff` · `architecture` · `optimize` · `verify` · `audit`

## 使用

1. 在 run 的 `SPEC.md` §0 声明 `contracts: research@1.0.0, verify@1.0.0`；复合类型同时声明 `baseline: composite/<name>@1.0.0`。现有领域模板映射见 `../specialized/BASELINE-MAP.md`。
2. MAIN/PMO 写 `ROUND-PLAN.md`，第一行声明本轮 `contract: <type>@<version>`。
3. QA 按 `_shared/PLAN-GATE.md` 跑 7/7；任一 FAIL 不得开工。
4. 收轮前按 `_shared/VERDICT.md` 写判词。
5. 运行 `python3 scripts/contract_lock.py check` 确认冻结文件未漂移。

## 新增/升级

- 新增原子轮型：先在 `DESIGN.md` 说明为什么现有 7 类不能组合覆盖，再新增目录、VERSION、LOCK。
- 修改契约：按 `BASE-MASTER.md` §4 新建版本；禁止原地改冻结文件。
