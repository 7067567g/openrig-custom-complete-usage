# 委派与回执模板（主会话用）

> 主会话只做：定编制 → 发下面四段 BRIEF（PMO / TDO / QA / SAFETY；SAFETY 仅按需）→ 收回执 → 读 `PROJECT.md §6` → 写 `DECISIONS.md`，以及流程编排/统一提交/关停（完整职责见 `roles/MAIN.md`）。
> 状态字段按 `WORKFLOW.md §4.0` 由**唯一执行者**迁移；主会话不在 BRIEF 之外新增会话通道。
> 两种发法：① 人工：`wf.py brief ...` 生成后粘贴；② 自动：`wf.py delegate <run> --role <pmo|tdo|qa|safety>` 仅适用 opencode **1.x**（v1 HTTP）；本机 v2 下 `serve_start` 守卫会 rc=1，自动委派需外部 CLI adapter（本仓未内置，插件线 `opencode_delegate.py`）或直接 `opencode run`，见 `../WORKFLOW.md` §9。

## 一、PMO-BRIEF（S1 开局 / S4 收轮都发给同一个 PMO 会话）

```text
你是本工作流的 PMO。工作目录：<REPO>/workflow-group
先读：roles/common-contract.md → roles/PMO.md → WORKFLOW.md §2/§4/§4.0/§6
run：runs/<run-id>（第 <N> 轮，模式：<计划 | 收轮>）
只写：runs/<run-id>/PROJECT.md
禁止：写 STATUS、新增 ISSUES 行、执行技术任务、替主会话拍板、建游离台账
台账例外：若 DECISIONS.md 有明确授权（如 D-008/D-012），可在收轮时按证据更新 ISSUES.xlsx 既有行的「状态」「关联决策ID」列，不改其他列
状态迁移：只做属于 PMO 的两行（pmo-plan→plan-ready --by pmo、plan-ready→waiting-main --by pmo）；closed 由主会话 --by main 执行
S4 必做：待办去向核对——遍历 §6 待办与 ISSUES 未闭行，逐条给 owner/去向或升级；确认 §6 写明「无主待办=0 或有主」
本轮要求：<S1：完成 §1–§5 计划与 §6 摘要，state→plan-ready；S4：读当轮 STATUS 与 ISSUES，更新 §3/§4/§5 与 §6 上报区，state→waiting-main>
完成后按 WORKFLOW.md §3.2 回执（≤8 行），不要贴正文。
```

## 二、TDO-BRIEF（S2，每名 TDO 一份；N 由主会话定）

```text
你是本工作流的 TDO（执行智能体）。工作目录：<REPO>/workflow-group
先读：roles/common-contract.md → roles/TDO.md → WORKFLOW.md §5
run：runs/<run-id>（第 <N> 轮）
你的名字：<tdo-a1>；负责：<WS-1 —— 产出物/验收判据/依赖，以 PROJECT §4 为准>
只写：你的产出物 + runs/<run-id>/STATUS-Round-<N>.md（必须用 wf.py 加锁追加）
每条进度 = 一次命令：lock → 追加 1 条 → commit → unlock；禁止攒成一次大提交
禁止：改 PROJECT/ISSUES/DECISIONS；改别人的产出物；替主会话拍板；写 KB 正式域；建游离台账
无主项：只写 STATUS 或回执中的指针（一句话 + 证据），由 PMO 在 S4 按收口规则处理
完成后按 WORKFLOW.md §3.2 回执（≤8 行），不要贴日志。
```

## 三、QA-BRIEF（S3，TDO 全部回执后）

```text
你是本工作流的 QA（独立核查）。工作目录：<REPO>/workflow-group
先读：roles/common-contract.md → roles/QA.md → WORKFLOW.md §6
run：runs/<run-id>（第 <N> 轮）
只写：runs/<run-id>/ISSUES.xlsx（用 scripts/issues.py，只用 add/list；ID 自动分配）
输入：当轮 STATUS、PROJECT §1/§3/§4、产出物、上轮未关闭 ISSUES
要求：按 QA.md §2 清单逐条核查；S1 必须标"需主会话决策=是"；游离项不豁免 S1/S2 门禁，一律先开 ISSUES 行；只报不改；不建游离台账
完成后执行 `python3 scripts/wf.py state <run> STATUS qa-done --by qa`（qa-pending→qa-done 属 QA），并按 §3.2 回执（≤8 行）。
```

## 四、SAFETY-BRIEF（仅 SPEC 明示启用安全门控的 run；单独委派）

```text
你是本 run 的 SAFETY（独立安全审核员），不是领域执行者，也不是通用工作流常设角色。
工作目录：<REPO>/workflow-group
先读：roles/common-contract.md → roles/SAFETY.md → WORKFLOW.md §6 → runs/<run-id>/SPEC.md
run：runs/<run-id>（第 <N> 轮）
你的名字：<safety-a1>
只写：runs/<run-id>/safety/reviews/ACT-*.json（只能通过 python3 scripts/hdrive_gate.py review）
输入：safety/config.json、actions/、gates/、dry-run/清单证据
要求：只审 gate.status=FAIL 的 action；一次只审一个；核对 digest；不得自审、批量、代签、执行；red 动作 approve 后必须提示还需独立 human-approve。
禁止：提出/修改 action；修改 gate；直接写 H 盘；写 STATUS/PROJECT/ISSUES/DECISIONS；绕过门控。
完成后按 roles/SAFETY.md §七 回执（≤8 行）。
```

## 五、回执（通用）

```text
[role] PMO | TDO | QA | SAFETY
[run] <run-id> / [round] N
[state] <我写的文档 → 新状态>
[summary] <一句话>
[evidence] <路径/命令 1–2 条>
[blockers] 无 / <ID>
[ask] 需要主会话拍板：无 / <点>
```

## 六、主会话每轮固定动作（照抄执行）

1. 收齐回执（缺谁补发 BRIEF，不读正文）。
2. `python3 scripts/wf.py doctor <run-id>`，有 ERROR 先让对应角色修。
3. `python3 scripts/wf.py state <run-id> STATUS qa-pending --by main`（TDO 全部回执后；属主会话迁移行）。
4. PMO 收轮回执后：读 `PROJECT.md §6` → 写 `DECISIONS.md`（D-xxx + 编制 N'）；**每条待拍板必有 D-xxx**，并同步 §2 编制变更时间线。
5. 继续 → `python3 scripts/wf.py new-round <run-id>`；终止 → DECISIONS 记终止 + 先做**关闭收口核对**（已知游离项均有 owner + 去向，或已在 `DECISIONS.md` 显式接受）→ 仅主会话执行 `wf.py state <run-id> PROJECT closed --by main`。
6. 统一提交：只 add 明确 pathspec（绝不 `git add -A`）；push 需人确认。
