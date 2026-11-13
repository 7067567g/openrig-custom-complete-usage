# PLAN-GATE — 原子轮型开工前计划门（7/7）

> 执行者：QA。机械项先跑命令，QA 只审“是否对照契约覆盖”；7/7 PASS 才允许开工。
> 本文件随 `atomic-contract-set@1.0.0` 冻结；领域 SPEC 可加检查，不能减项。

## 机械检查

```bash
R=runs/<RUN-ID>
test -s "$R/SPEC.md"
test -s "$R/PROJECT.md"
test -s "$R/ROUND-PLAN.md"
grep -q '^contract:' "$R/ROUND-PLAN.md"
grep -q '^produces:' "$R/ROUND-PLAN.md"
grep -q '^gate:' "$R/ROUND-PLAN.md"
grep -q '^budget:' "$R/ROUND-PLAN.md"
grep -q '^NOT-DOING:' "$R/ROUND-PLAN.md"
```

## QA checklist（逐条 PASS/FAIL）

1. `contract:` 指向已冻结的 `templates/contracts/<type>/CONTRACT.md`，且版本与 `LOCK.json` 一致。
2. `SPEC.md` 是否声明 baseline 与领域 adapter；若没有 baseline，必须写 `none` 和理由。
3. 契约 `produces` 的每个文件都在 `ROUND-PLAN.md` 的 `produces:` 行有落点。
4. 契约 `mandatory_gates` 的每条都在 `gate:` 行有对应命令/检查。
5. 预算未突破：目标数、TDO 数、时长、周期轮数都在 `budget:` 与 NOT-DOING 中声明。
6. `requires` 的文件存在，或明确写出缺失替代与风险。
7. 证据落点与 owner 明确：谁在何时把证据写到哪里，QA/主会话如何复核。

**判定**：7/7 PASS → 开工；任一 FAIL → MAIN 修 ROUND-PLAN 后重审，不得先做后补。
