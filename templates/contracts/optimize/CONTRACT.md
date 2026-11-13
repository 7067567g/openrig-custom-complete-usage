# CONTRACT — optimize@1.0.0（实施优化与接线）

> **状态：frozen**。属于 `atomic-contract-set@1.0.0`，建立在 `workflow-group-base@1.0.0` 之上。
> 本契约只定义接口，不规定具体 WS 切分、模型、工具或领域路径；这些由 run 的 `SPEC.md` / `ROUND-PLAN.md` 特化。
> 不可覆盖的四条通用约束仍然有效：文档即接口、单一写者、STATUS 加锁逐条提交、分歧不落地。

## purpose

实施 ≤3 个已选目标，做到实现、接线、热路径/主路径可达，并留下先红后绿、回归和回滚证据。

## requires（必读输入）

- `reports/CANDIDATES.md` / `ARCH-ASSESSMENT.md` / `DIFF-SUMMARY.md` 中已选目标
- 写权限白名单（一目标一 owner/文件边界）
- 基线门禁命令与当前真值
- 回滚路径

## produces（必产文件 + schema）

- 代码/测试/配置改动（严格限定在 SPEC 白名单）
- `reports/VERIFY.md`：先红后绿证据、接线点、回归、回滚
- 版本四件套或项目等效发布记录（当本轮含版本）
- `reports/STATUS` 或等价执行回执

## mandatory_gates（强制门）

- 目标 ≤3；每个目标必须实现+接线+主路径证据齐全，否则降级进 backlog。
- 先红后绿：修复/新增前有失败证据，后有通过证据。
- 门禁不得低于基线；未验证项必须显式写。
- 跨仓/无版本控制/生产写入按领域 adapter 的风险修饰执行。

## hard_boundaries（硬边界）

- 只改 SPEC 白名单；不改别人文件边界。
- 不直接 push 上游；发布/推送按项目授权单独执行。
- 不得为了绿而伪造门禁或删测试。

## budget_defaults

默认 TDO ≤6；单轮 ≤2h；目标 ≤3；单周期轮数由 baseline/CYCLE-PLAN 限定。

## done（完成定义）

代码+测试+VERIFY+版本记录（若适用）落盘；PLAN-GATE 7/7；QA 独立复核；若为最后一轮则写 VERDICT。

## handoff（交接）

代码 + VERIFY + 版本记录 → verify。

## domain_adapter_hooks

领域 adapter 负责测试入口、发布四件套、风险白名单和回滚方式。

## plan_gate / verdict

- 执行前必须通过 `templates/contracts/_shared/PLAN-GATE.md` 的 7/7。
- 每轮结束由 MAIN 写 `reports/VERDICT.md`（`CONTINUE | ADJUST | STOP`）；规则见 `_shared/VERDICT.md`。
- 如果本类型是该 run 的最后一轮，VERDICT 与 DONE/BLOCKED 必须同时存在。
