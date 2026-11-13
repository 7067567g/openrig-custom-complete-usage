# STOP-SWEEP · 总任务中途停止时的清扫边界

- 日期：2026-11-14
- 类型：治理/收尾流程设计，不改产品代码
- 关联：QUIET-200 / UX6-R15 / 正式 30 轮 R16（NEED_MAIN）
- 已记录问题：deck issue `01`（QUIET-200 基线未冻结）

## 目标

设计一套可重复的“总任务中途停止”清扫边界，并写一份完整收尾手册给 QA：

1. 停止时先冻结状态，不立即删除/清理；
2. 为 QA 新建收尾任务（或保留/重启 QA 步骤），把残留清单交给 QA；
3. QA 把每项残留判为：
   - `CLOSE_OUT`：实际已完成，只差收尾/关单/补证据；
   - `ABANDON`：标记废弃，保留最小引用，让下一轮可参照/回避；
   - `ARCHIVE_RECYCLE`：已无利用价值或会造成干扰，归档后回收；
4. 所有分类必须有证据、有 owner、有动作、有回滚路径；
5. 收尾完成后恢复主链锚点/回归点，不跳过 R16。

## 必须覆盖的停止场景

- 用户主动停 / 中止
- 预算/时间/内存/并发上限
- gate FAIL / BLOCKED / NEED_MAIN
- seat 卡死、watchdog、qitem 超时
- 进程崩溃、断电/重启
- 多轮支线中途停止

## 必须盘点的残留

- OpenRig workflow instance / frontier qitem / queue rows / recovery qitems
- seat 进程、tmux、systemd scope、watchdog
- git 分支、worktree、dirty 文件、stash、tag、merge 状态
- 分支文档/ledger/索引/报告/证据
- 临时文件、原始截图、UI dump、logcat、token（禁止泄露）
- snapshots/staging/dist 等只读目录
- 后台服务、锁文件、端口、ADB 锁

## 输出

- `docs/CLOSEOUT-MANUAL.md`：完整收尾手册（给 QA）
- `reports/operations/STOP-SWEEP.md`：边界/分类/决策分析
- `reports/operations/STOP-SWEEP.json`：机器可读规则与清单
- `reports/operations/QA-CLOSEOUT-TASK.md`：QA 新任务模板（可直接复制）
- 可选：`reports/operations/CLOSEOUT-LEDGER-TEMPLATE.json`

## 关键要求

- 不把“已停止”误记为 `done`；停止是 `aborted/failed/blocked/NEED_MAIN` 等真实状态。
- 不在 QA 分类前删除分支/文件/快照/qitem。
- 不把原始截图、聊天正文、token、logcat 正文写进手册或证据。
- 归档回收前必须有 QA 签字 + 回滚路径。
- QA 分类结果要能驱动下一轮：`CLOSE_OUT` 可关，`ABANDON` 可跳过/引用，`ARCHIVE_RECYCLE` 可从工作区移走但保留归档索引。
