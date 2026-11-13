# templates — 母版与模板分层

> 本目录分四层：`templates/` 根 = 可实例化四件套母版；`contracts/` = 冻结原子轮型；
> `baseline/` = 复合类型基准模板（重点参考，不可直接实例化）；`specialized/` = 领域 run 模板。

| 层 | 路径 | 实例化 | 作用 |
| --- | --- | --- | --- |
| 四件套母版 | `templates/{PROJECT,DECISIONS,STATUS-Round-n,ISSUES.xlsx}` | 自动回退 | 所有 run 的文档底座 |
| 原子轮型 | `templates/contracts/<type>/CONTRACT.md` | 否 | 单轮最小接口；`SPEC §0` 引用 |
| 基准模板 | `templates/baseline/<name>/BASELINE.md` | 否 | 复合类型重点参考；`SPEC §0` 引用 |
| 领域特化 | `templates/specialized/<name>/` | 是 | 具体 run 的写权限/证据/DoD |

> `wf.py new-run --template` 只接受领域特化目录；`contracts/` 与 `baseline/` 会被拒绝。
> 自动引用规则、冻结与变更协议见 `WORKFLOW.md §4.2–§4.3`。

## 四件套母版
> **不要直接改模板**：母版只读。实例化用 `python3 scripts/wf.py new-run/new-round`（从本目录复制到 `runs/<run-id>/`）。
> 要改流程：`WORKFLOW.md` 是 canonical。先改 `WORKFLOW.md`，再同步 `roles/`、`templates/`、`scripts/`，最后回写 `DESIGN.md` 记录理由。

## 文件

| 文件                | 实例名                          | 写者                                                                             | 说明                              |
| ------------------- | ------------------------------- | -------------------------------------------------------------------------------- | --------------------------------- |
| `PROJECT.md`        | `PROJECT.md`                    | PMO（S0 bootstrap 窗口 MAIN 仅可写 §0 元信息与 §1 G1；PMO 接管后 MAIN 只读）       | 目标/范围/指标/分任务/轮次/上报区 |
| `DECISIONS.md`      | `DECISIONS.md`                  | 主会话                                                                           | 决策账本 + 编制时间线             |
| `STATUS-Round-n.md` | `STATUS-Round-1.md` / `-2.md` … | TDO                                                                              | 当轮进度/阻塞/交接（加锁写）      |
| `ISSUES.xlsx`       | `ISSUES.xlsx`                   | QA（只新增行）；PMO 仅在 `DECISIONS.md` 授权下更新既有行的「状态」「关联决策ID」 | 问题/风险/变更                    |

## 占位符（`new-run` 自动替换）

| 占位符             | 含义                                                     |
| ------------------ | -------------------------------------------------------- |
| `<RUN-ID>`         | run 目录名（kebab-case）                                 |
| `<PROJECT-NAME>`   | 项目显示名，默认同 run-id                                |
| `<GOAL>`           | 主会话给定的一句话目标（可用 `--goal-file` 读长文）      |
| `<PROJECT-ROOT>`   | 真实项目根路径（`new-run --project-root`）               |
| `<WRITE-SCOPE>`    | 写权限白名单，如 `10-signaldeck/**`（`new-run --scope`） |
| `<DATE>`           | 建档日期 `YYYY-MM-DD`                                    |
| `<ROUND-N>`        | 当前轮次数字                                             |
| `<TDO-N>` / `<N'>` | 编制建议数                                               |

> `主会话提交范围`（`PROJECT.md §0`）**不是** `new-run` 占位符：模板以非占位默认文案给出（“项目仓 run 填本次改动文件路径；工作流自身 run 留空；主会话仅用明确 pathspec”），由 PMO 在 S1 写具体值（S0 bootstrap 窗口 MAIN 仅可写 §0 元信息与 §1 G1，PMO 接管后 MAIN 不得再写），避免 `new-run` 不替换而在 `plan-ready` 触发 `doctor` ERROR。**不要把 `COMMIT-SCOPE` 这类尖括号占位符再写回模板。**

## `wf-doc` 元信息块（每份 md 头部）

```text
<!-- wf-doc
run: <run-id>
round: <当前轮次>
doc: PROJECT | DECISIONS | STATUS
owner: PMO | 主会话 | TDO
state: <状态值，见下>
updated: YYYY-MM-DD
-->
```

状态值（只允许这些，迁移用 `wf.py state`）：

| doc       | 允许状态（按迁移顺序）                                                  |
| --------- | ----------------------------------------------------------------------- |
| PROJECT   | `pmo-plan` → `plan-ready` → `waiting-main` → `closed`                   |
| DECISIONS | `open` → `closed`                                                       |
| STATUS    | `tdo-pending` → `tdo-in-progress` → `qa-pending` → `qa-done` → `closed` |

## ISSUES.xlsx 结构

- `账本`：唯一数据表，列见下；ID 由 `issues.py` 自动分配（`P-` 问题 / `R-` 风险 / `C-` 变更）。
- `汇总`：按严重度/状态/类型/是否需主会话决策的 COUNTIF 汇总，打开 Excel 自动计算。
- `说明`：字段字典、严重度定义、命令行示例、硬规则。

列：`ID | 轮次 | 类型 | 标题 | 描述 | 严重度 | 状态 | 责任角色 | 来源 | 建议动作 | 需主会话决策 | 关联决策ID | 创建时间 | 更新时间`

硬规则：`S1` 行必须 `需主会话决策=是`（doctor 检查）；行只增不删，作废改状态；修改一律走 `issues.py`，不要手编；关闭/挂起行必须有可追溯证据落点（`PROJECT §6` 或 `DECISIONS D-xxx`）。

## 收口与承接（2026-10-15）

- **关闭收口规则**：run `closed` 前，所有已知游离项必须有 owner + 去向，或由主会话在 `DECISIONS.md` 显式接受；否则不得关闭。
- **跨轮承接规则**：跨轮/跨 run 承接项必须写 owner + 去向 + 最晚复核轮；未立项的“下一 run”不算有效去向。
- 本工作流不设额外常设角色；游离项由 PMO 在 S4 做结构核对，不新建游离台账。详见 `WORKFLOW.md §3.1/§6/§7`、`roles/MAIN.md`。
