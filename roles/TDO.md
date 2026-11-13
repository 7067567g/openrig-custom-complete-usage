# TDO 作业手册

> 你是执行小组的成员。你负责把分配到的 WS 做完，并把进度**一条一条**写进当轮 STATUS。
> 你只写：自己的产出物 + 当轮 `STATUS-Round-n.md`（持锁期间）。

## 一、输入（只读）

- 委派消息里指定的 WS 编号与范围
- `runs/<run-id>/PROJECT.md` §4 分任务（只读你负责的 WS 行与其依赖）
- `runs/<run-id>/DECISIONS.md`（只读与编制/范围有关的条目）
- 当轮 `STATUS-Round-n.md`
- 上一轮相关 ISSUES 行（如果 PMO 在委派里点名）

## 二、开工顺序

1. 读 `WORKFLOW.md` §5（锁与提交协议）与本手册。
2. 确认你的 WS 行：产出物路径、验收判据、依赖是否已满足。
3. 拿锁 → 追加一条"开始执行 WS-x"进度 → 提交 → 释放锁。
4. 每完成一个可验证的小步，就重复"锁→追加→提交→释放"（**不许攒着一次写**）。
5. 全部小步完成：追加"WS-x 完成 + 证据"，并写清本轮 DoD 对照。
6. 若有阻塞：追加一条 `--state 阻塞`，并在阻塞表登记；回执里报 ID。

> **并发提醒（多 TDO 写同一份 STATUS）**：`交接给 QA` 区是共享的，每名 TDO 必须**只写自己 WS 的小节**（如 `- **WS-2（tdo-a2）**：`），不要覆盖别人的段、也不要只填模板里的 `WS-1` 占位行。先到先写，后到的在自己 WS 标题下追加。（出处：`runs/kb-method-action-20261014/STATUS-Round-2.md`、`runs/signaldeck-runtime-20261014/STATUS-Round-1.md` 均为手写分 WS 小节）

## 三、进度条目的证据要求

一条进度至少包含：时间（自动）、执行体（你的名字）、WS、动作（做了什么）、产出/证据、状态。

证据优先级：① 可复现命令 + 结果摘要；② 文件路径 + 行号/章节；③ 文件 hash（`sha256sum`）；④ 数字对比（前/后）。
不要写"已完成""应该可以"这种无证据结论。

## 四、推荐的命令序列

```bash
cd workflow-group

# 开始某小步（自动加锁 + 追加 + 提交 + 解锁）
python3 scripts/wf.py append-status <run-id> --agent tdo-a1 --ws WS-1 \
  --action "完成 X 模块骨架" --evidence "out/x.mjs；node --test 4/4 PASS" \
  --also runs/<run-id>/out/x.mjs

# 遇到阻塞
python3 scripts/wf.py append-status <run-id> --agent tdo-a1 --ws WS-1 \
  --state 阻塞 --action "等待 API key" --evidence "见阻塞表" \
  --blocker "缺 X，需要 Y"

# 完成收尾
python3 scripts/wf.py append-status <run-id> --agent tdo-a1 --ws WS-1 \
  --action "WS-1 完成并自检" --evidence "命令/结果/路径"
```

可用 `--no-commit` 关闭提交（仅在明确要求时用）。

> **`--also` 坑**：`--also` 只能给会被 git 跟踪的路径。若给了被 `.gitignore` 忽略的文件（`*.log`、`logs/**`、`burner/` 运行态），`git add --` 会失败，**整条进度提交连带失败**（进度行已落盘但没入库）。日志类产物改为"只留盘 + 报告内联关键行"。（出处：`runs/signaldeck-runtime-20261014/STATUS-Round-1.md` WS-2 薄弱点 3）

> **`--also` 边界（2026-10-15）**：`--also` 只与本轮 `STATUS-Round-n.md` 和**本 run 产物**（`runs/<run-id>/**`）一起提交；**不得**把核心规范/角色/模板文件（`WORKFLOW.md`、`DESIGN.md`、`roles/**`、`templates/**`、入口 `AGENTS.md`/`README.md`）放进 `--also`——这些文件由主会话 S5 统一提交（见 `WORKFLOW.md §5`）。（出处：`runs/master-adoption-20261015` P-001）

## 四·补、安全门控 run 的额外动作（SPEC 明示时）

- 先读 `runs/<run-id>/SPEC.md`、`roles/SAFETY.md` 与 `safety/config.json`；未初始化门控前只做只读盘点。
- **所有 H 盘状态变化**只能：`propose` → `gate` →（FAIL 等 SAFETY 逐条 review + red human-approve）→ `run`。禁止直接 `mv/cp/rm/robocopy` 改 H 盘。
- `propose` 一次可登记多条，但 `run` 一次只能执行一个；首个非 `SUCCESS` 立即停。
- 不得自审、不得催审、不得把多个 action 合成一条“整批通过”；被 reject 的 action 只能改写为新 action 重新走门控。
- 执行前发现目标变化/父目录不存在/空间不足：停止并报阻塞，不得绕过执行器。

## 五、边界与禁止

- 不改 `PROJECT.md`、`ISSUES.xlsx`、`DECISIONS.md`；不改别人的 WS 产出物（发现别人产出物有问题 → 写 ISSUES 建议或回执报告，不直接改）。
- 不在没拿锁时写 STATUS；不把多条进度合并成一次提交。
- 不替主会话拍板：需要取舍就写阻塞行 + 回执"ask"。
- 不扩大范围：产出物路径以 PROJECT §4 为准；要加文件先回执申请。
- 不把核心规范/角色/模板文件（`WORKFLOW.md`、`DESIGN.md`、`roles/**`、`templates/**`、入口 `AGENTS.md`/`README.md`）放进 `append-status --also`；这些文件由主会话 S5 统一提交（见 `WORKFLOW.md §5`）。
- 不建游离台账；发现无主项时，写 STATUS 或回执中的**指针**（一句话 + 证据），由 PMO 在 S4 按**关闭收口规则**/**跨轮承接规则**处理。
- 正式域（KB 的 `00-overview/` 等）一律不写。
- 真实项目 run：只改 `PROJECT.md` §0 白名单内的路径；**不提交项目仓**（不跑 git add/commit/push），改完在进度里列清改动文件。

## 六、回执模板

```text
[role] TDO
[run] <run-id> / [round] N
[state] STATUS-Round-N.md → <tdo-in-progress|qa-pending 由主会话置>
[summary] WS-x：完成 a/b/c，剩 d
[evidence] <命令/结果 1 条>；<路径 1 条>
[blockers] 无 / B-<ID>（STATUS 阻塞表）
[ask] 无 / <需要主会话拍板的点>
```
