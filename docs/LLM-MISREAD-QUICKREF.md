**English** | [简体中文](LLM-MISREAD-QUICKREF.zh-CN.md)

# LLM quick reference — common user misreads

Audience: an LLM/agent reading a short human instruction.

Purpose: map ambiguous user phrases to the right layer and command path, and
decide when to **ask instead of guessing**.

## 0. Operating rule

1. Classify the phrase into a layer:
   - SCTG protocol/kit;
   - workflow-group control plane;
   - OpenRig execution plane.
2. Check the current context: repo, open rig, workflow instance, queue, recent
   commands.
3. If the phrase maps to **more than one layer**, or changes cost / state /
   irreversible action, ask.
4. Ask with **concrete choices**, not “please clarify”.
5. If you proceed on an assumption, state it in one line.
6. Never silently switch layers or substitute a different command path.

### Clarification gate: ask once, then never mid-flow

This policy is for a **complete multi-round automated flow**, not a per-turn
chat. Questions are allowed only **before** the run starts.

#### Before start: one consolidated clarification pass

Resolve all material ambiguity in one batch:

1. **Layer** — SCTG kit, workflow-group control plane, or OpenRig execution plane?
2. **Count unit** — rounds or steps? How many?
3. **Output / acceptance** — what file or state proves completion?
4. **Irreversible actions** — publish, delete, teardown, cost, credentials?
5. **Budget / timeout** — max wall time, token/cost, or concurrency?

Prefer 1-3 concrete A/B/C questions in one message. Do not run a multi-turn
interrogation.

Small deviations at this stage are allowed: choose the most likely meaning,
state the assumption, and include it in the run notes.

#### After start: no questions

Once the automated run starts:

- **Do not ask the user anything.**
- Use documented defaults for low-risk ambiguity; record the assumption in
  `DECISIONS.md`, `STATUS`, or a run note.
- If genuinely blocked, write `BLOCKED` / `NEED_MAIN` with the exact decision
  needed, continue unblocked work, and report at the end.
- If the next action is irreversible/destructive and was not authorized at the
  start gate, stop with a written blocker; do not ask interactively.

#### Question budget

```text
before start: one consolidated batch (1-3 concrete questions max preferred)
after start:  zero questions
```

## 1. Master quick table

| User phrase | Could mean | Default reading | Ask when |
|---|---|---|---|
| “使用 OpenRig” | create rig; open seat; run workflow; use SCTG nickname | run a workflow only if a workflow spec/rig exists | no rig/workflow context |
| “跑个工作流” | workflow-group rounds; OpenRig workflow steps; local docs only | OpenRig `workflow run` if a spec exists | no spec or “round” mentioned |
| “10 步 / 10 轮” | OpenRig steps; workflow-group rounds | use the unit the user explicitly said | counts affect scope/close |
| “自动化” | `rig workflow run`; manual `rig send`; burner queue | `rig workflow run` | no rig/spec or “unattended” |
| “跑完了” | workflow completed; packet done; local round closed; report accepted | check actual state first | state disagrees |
| “上传 / 发布” | git push; GitHub release; public content; artifact upload | ask unless repo/release context is explicit | any publish action |
| “检查 / 审计” | spec validate; live run; content audit; security scan | ask which layer | no artifact named |
| “脱敏” | remove secrets; remove paths; rewrite history; redact transcripts | ask which target | public release |
| “内存 / 资源” | cgroup limit; host pressure; model context window | ask which resource | OOM/limits mentioned |
| “多轮” | workflow-group rounds; OpenRig rework loop | workflow-group rounds if `wf.py` context | OpenRig workflow context |
| “Command Center / General Staff / organization department / SOLO / Medical Center” | Project-local governance layers, not OpenRig kernel | Read guide §0.2, then the project repo's matching directory | The project repo has no such governance directory |

## 2. “OpenRig” is not one thing

| User may mean | Correct mapping | LLM action |
|---|---|---|
| “OpenRig 起个 team” | `rig up` / `rig create` | create/launch rig; do not claim workflow ran |
| “OpenRig 跑工作流” | `rig workflow run` | render/validate/run workflow |
| “OpenRig 发消息” | `rig send` | manual/debug path |
| “OpenRig 调试” | `rig ps`, `queue`, `workflow show/trace` | inspect, do not mutate blindly |
| “OpenRig 就是我的 SCTG 工作流” | user’s nickname, not the CLI | confirm whether they mean control plane or execution plane |

**Ask template**

> 你说的 OpenRig 是指：
> A. 起 rig / seat；B. 用 `rig workflow run` 跑工作流；C. 手动 `rig send` 调试；
> D. 你的 SCTG 工作流（不启动 OpenRig）？

### 2.1 Project-local governance: Command Center / General Staff / SOLO / Medical Center

When you see “Command Center”, “General Staff”, “organization department”, “SOLO”,
or “Medical Center”, first check whether it is a project-local governance layer,
not an OpenRig kernel command:

| Phrase | What it means | Action |
|---|---|---|
| “Command Center / organization department / round registry” | Registers non-SOLO long-running rounds/branches and exposes branch/worktree conflicts | Read `docs/command-center/` and `ROUND-REGISTRY.json` in the project repo |
| “General Staff / staff department” | Indexes thinking rounds, scores them, reuses dimensions, and requires consultation before analysis | Read `docs/general-staff/`; run `consult_staff` before `analyze` |
| “Standalone round / SOLO / discrete / scattered” | One-off governed round with ID/anchor/branch/QA/closeout | Read `docs/rounds/` and `.solo-round.json` |
| “Medical Center / medical center / patient intake” | Triage/isolation/stamps/propose-only patches/RCA for injured objects | Read `docs/medical-center/`; not an OpenRig kernel feature |
| The project repo has none of these | Work with the three-layer model only | Do not invent governance layers |

See [`OPENRIG-WORKFLOW-GUIDE.md`](OPENRIG-WORKFLOW-GUIDE.md) §0.2.

**Semantic matching**: names need not match exactly; match by the governance
dimension. If a name maps to Command Center / General Staff / SOLO / Medical
Center, use that layer. If it could be two layers, inspect whether it reads
`ROUND-REGISTRY.json` (Command Center) or `THINKING-ROUNDS.json` (General Staff).
If it matches nothing, or the decision changes scope/cost/irreversible action,
ask once with A/B/C/D options; do not invent a fifth layer.

## 3. “Workflow” is not one thing

| Phrase | Likely layer | Check |
|---|---|---|
| “跑 workflow-group” | control plane | `wf.py`, PROJECT/STATUS |
| “跑 OpenRig workflow” | execution plane | `workflow.yaml`, `rig workflow run` |
| “跑 SCTG 工作流” | protocol + workflow-group | `sctg-kit`, `wf.py` |
| “跑多轮” | workflow-group rounds | `new-round`, STATUS-Round-n |
| “跑 12 步” | OpenRig steps | workflow spec `steps:` |

**Ask template**

> 你说的“工作流”是：
> A. workflow-group 的 12 轮；B. OpenRig 的 12 个 step；C. 两者组合？

## 4. “Done” is not one thing

| User says “done” | Verify |
|---|---|
| “workflow done” | `rig workflow show <id>` status completed |
| “packet done” | `rig queue show <qitem>` state done |
| “round done” | `wf.py doctor` / STATUS state |
| “report done” | file exists and has content |
| “accepted” | independent review/decision, not just packet closure |

**Rule:** packet closure ≠ acceptance. Do not report “done” from a chat message
alone.

**Ask template**

> 你说的“完成”是指 workflow completed、packet done、round closed，还是报告已验收？

## 5. “Automate it” is not one thing

| User intent | Command path |
|---|---|
| One declarative workflow, followed to terminal | `rig workflow run <spec>` |
| Manual seat conversation | `rig send <seat>` |
| Batch queue of long-running sessions | queue/burner automation |
| Local-only document rounds | `wf.py` |

**If no rig/spec exists, ask** whether to create the rig first or run local-only.

## 6. “Check / audit” is not one thing

| Check type | Command |
|---|---|
| spec syntax | `rig workflow validate <spec>` |
| launch plan | `rig up <spec> --plan` |
| live workflow state | `rig workflow show/trace` |
| queue state | `rig queue list/show` |
| repo content | `scripts/check_content.py` |
| sanitization | `scripts/check_sanitization.py` |
| tests | `make test` |

Do not answer “audit passed” from only one of these.

## 7. “Memory / resource” is not one thing

| Phrase | Meaning |
|---|---|
| “memory limit” | cgroup `MemoryHigh/MemoryMax/MemorySwapMax` |
| “host OOM” | system-wide pressure / page cache |
| “context window” | model context, not host RAM |
| “too many seats” | concurrency + global slice |

**Rule:** `MemoryHigh` is soft inside `MemoryMax`; swap is separate. They are not
additive.

## 8. “Upload / publish” is not one thing

| Phrase | Action |
|---|---|
| “push” | git commit + push |
| “发布” | tag + GitHub release |
| “上传内容” | publish files/docs/examples |
| “公开仓库” | which repo: SCTG-public or openrig-custom-complete-usage? |
| “脱敏后上传” | run sanitization + history scan first |

**Always ask before** force-push, history rewrite, tag deletion, or public release.

## 9. Clarification templates

Use concrete options:

```text
你说的 X 是指：
A. ...
B. ...
C. ...
如果是 A，我会 ...；如果是 B，我会 ...
```

```text
这里有一个跨层歧义：你说的是 workflow-group 的 round，还是 OpenRig 的 step？
两者的计数和关闭方式不同。
```

```text
这个操作会改公开历史 / 删除 tag / 触发发布；请确认是否继续。
```

## 10. Fast triage flowchart

```text
User phrase
  -> mentions wf.py / PROJECT / round?       -> workflow-group control plane
  -> mentions rig / seat / queue / step?      -> OpenRig execution plane
  -> mentions card / gate / submission?       -> SCTG kit
  -> mentions publish / push / release?       -> ask before acting
  -> ambiguous across layers?                 -> ask with A/B/C choices
  -> same layer and reversible?               -> proceed + state assumption
```
