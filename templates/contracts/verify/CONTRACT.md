# CONTRACT — verify@1.0.0（独立验证与发布断言）

> **状态：frozen**。属于 `atomic-contract-set@1.0.0`，建立在 `workflow-group-base@1.0.0` 之上。
> 本契约只定义接口，不规定具体 WS 切分、模型、工具或领域路径；这些由 run 的 `SPEC.md` / `ROUND-PLAN.md` 特化。
> 不可覆盖的四条通用约束仍然有效：文档即接口、单一写者、STATUS 加锁逐条提交、分歧不落地。

## purpose

独立复跑上一轮产物，核对门禁、接线、版本与发布事实，给出发布/不发布结论。

## requires（必读输入）

- 上一 optimize 轮的代码/产物与 VERIFY
- 基线门禁与版本四件套
- 目标环境说明（依赖/工具/端口/凭据边界）
- 发布/不发布判据

## produces（必产文件 + schema）

- `reports/VERIFY-FINAL.md`：独立复跑的命令、环境、输出、exit code
- `reports/RELEASE-NOTES.md`：版本/tag/push 记录或明确不发布
- `reports/VERDICT.md`：PASS/WARN/FAIL + 发布结论

## mandatory_gates（强制门）

- 独立复跑，不采信上一轮的摘要数字。
- “全绿”必须连环境陈述：缺哪个依赖、通过/失败数、skip 原因。
- 验证轮只读；发现问题登记 ISSUE/裁决，不顺手改代码。
- 未验证、未覆盖或环境不满足的项目必须显式列出。

## hard_boundaries（硬边界）

- 不修改代码/配置/发布事实。
- 不把部分验证写成全面通过。
- push/tag 只能按授权在事前约定的仓库/分支执行。

## budget_defaults

默认 TDO ≤3；单轮 ≤2h；复跑命令与矩阵由 SPEC 冻结。

## done（完成定义）

VERIFY-FINAL + RELEASE-NOTES + VERDICT 落盘；PLAN-GATE 7/7；QA 通过；DONE/BLOCKED 明确。

## handoff（交接）

VERIFY-FINAL + RELEASE-NOTES → audit / 下一轮 strategy。

## domain_adapter_hooks

领域 adapter 负责测试入口、环境要求、发布仓库/分支和已知限制。

## plan_gate / verdict

- 执行前必须通过 `templates/contracts/_shared/PLAN-GATE.md` 的 7/7。
- 每轮结束由 MAIN 写 `reports/VERDICT.md`（`CONTINUE | ADJUST | STOP`）；规则见 `_shared/VERDICT.md`。
- 如果本类型是该 run 的最后一轮，VERDICT 与 DONE/BLOCKED 必须同时存在。
