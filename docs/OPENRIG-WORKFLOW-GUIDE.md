**English** | [简体中文](OPENRIG-WORKFLOW-GUIDE.zh-CN.md)

# OpenRig + workflow — complete guide

This is the single entry point for using OpenRig with the workflow-group /
SCTG control plane. It exists because the same words mean different things at
different layers, and because LLMs reliably conflate them.

## 0. Read this first: the five hard distinctions

| Do not say | Say instead |
|---|---|
| "OpenRig is SCTG" | SCTG is the protocol/kit; OpenRig is the execution plane; workflow-group is the control plane. |
| "workflow run does the work" | `rig workflow run` instantiates and follows a workflow. Seats do the work and close packets. |
| "rig send is the automation path" | `rig send` is manual/debug. One-line automation is `rig workflow run`. |
| "a step is a round" | A **step** is an OpenRig engine unit. A **round** is a PMO -> TDO -> QA -> MAIN cycle. |
| "validate/plan means E2E passed" | `workflow validate` and `rig up --plan` validate specs, not model execution. |

If you remember only one thing: **rounds belong to workflow-group; steps and
queue packets belong to OpenRig.**

> For a checklist of common user misreads and when to ask, see [`LLM-MISREAD-QUICKREF.md`](LLM-MISREAD-QUICKREF.md).

## 0.1 How to ask for this (short phrases)

Use an intent-specific phrase. A bare “use OpenRig” is ambiguous — it can mean
“create a rig”, “open a seat”, or “run a workflow”.

| Intent | Short Chinese phrase | What it should mean |
|---|---|---|
| One-line automated OpenRig workflow | **“用 OpenRig 跑工作流。”** | render -> validate -> `rig workflow run` |
| Full SCTG control plane + OpenRig execution | **“用 OpenRig 执行 SCTG 工作流，单线跑。”** | workflow-group owns goals/decisions; OpenRig owns seats/queue/workflow |
| SCTG rounds only, no OpenRig | **“跑 SCTG 多轮。”** | `wf.py new-run` / `new-round` |
| Manual seat debugging | **“OpenRig 手动调试。”** | `rig up` + `rig send` + queue inspection |
| Spec/plan check only | **“OpenRig 预检。”** | `workflow validate` / `rig up --plan` |

Default recommendation: **“用 OpenRig 跑工作流。”**  
Most precise: **“用 OpenRig 执行 SCTG 工作流，单线跑。”**

### Clarification gate: ask once before start, never mid-flow

For a complete multi-round automated flow, questions are allowed only **before**
the run starts. Do one consolidated clarification pass covering: layer
(SCTG/workflow-group/OpenRig), count unit (rounds vs steps), output/acceptance,
irreversible actions, and budget/timeout. Prefer 1-3 concrete A/B/C questions.

After the run starts:

- do not ask the user anything;
- use documented defaults and record assumptions in `DECISIONS.md` / `STATUS`;
- if blocked, write `BLOCKED` / `NEED_MAIN` and continue unblocked work;
- if an unauthorized irreversible action is next, stop with a written blocker.

Question budget: **one consolidated batch before start, zero after start.**

## 0.2 Project-local governance layers (not OpenRig core)

OpenRig core provides rigs, seats, queue packets and workflow instances. Mature
projects usually add a project-local governance layer on top. An agent that
reads only this guide must still know that layer exists; otherwise it will
misread a governance problem as an OpenRig bug.

| Layer | One-line job | Read it before... | Typical entry (inside the project repo) |
|---|---|---|---|
| **Command Center** (round organization) | Registers non-SOLO long-running rounds/branches; exposes branch/worktree/resourceKey conflicts | starting, switching, stopping, or merging a long-running round | `docs/command-center/`, `ROUND-REGISTRY.json` |
| **General Staff** | Indexes thinking rounds, scores them, reuses dimensions, and requires consultation before analysis | any analysis/design/governance/research task; run `consult_staff` before `analyze` | `docs/general-staff/`, `THINKING-ROUNDS.json`, `THINKING-DIMENSIONS.json` |
| **Standalone round (SOLO)** | A one-off governed container with ID, anchor, branch, rejoin, QA, evidence and closeout | a one-off task that is neither a formal round nor a long-running branch | `docs/rounds/`, `.solo-round.json` |
| **Medical Center** (optional, on demand) | Triages injured data/processes, isolates evidence, stamps patients, proposes patches without applying them, and writes RCA | corrupt data, orphan worktrees, half-finished workflows, wrong conclusions | `docs/medical-center/`, `reports/medical-center/` |

Boundaries:

- These layers are **project-local governance**, not OpenRig kernel features.
  No `rig ...` command replaces them.
- Long-running round -> Command Center; one-off governed task -> SOLO; thinking
  consultation -> General Staff; stop/closeout -> CLOSEOUT manual; injured
  object -> Medical Center.
- If the project repo has no such directories, use the three-layer model in this
  guide and do not invent governance layers.

### 0.2.1 Common aliases and semantic matching

The same governance dimension may have different names in different projects or
domains. **Match by responsibility, not by exact name.**

| Dimension | Canonical name | Common aliases / misuses | How to recognize it |
|---|---|---|---|
| Round/conflict governance | **Command Center** | organization department, round registry, round collection center, Command Center, Round Registry | It registers long-running rounds/branches or answers "what is running now and what may collide?" |
| Thinking/evaluation governance | **General Staff** | staff department, staff center, General Staff, Thinking Staff | It indexes thinking rounds, scores them, reuses dimensions, or requires consultation before analysis |
| One-off governed round | **Standalone round (SOLO)** | discrete round, scattered round, Standalone Round, DISCRETE, SCATTERED | It is a one-off container with ID/anchor/branch/rejoin/QA/evidence/closeout |
| Injured data/process governance | **Medical Center** | medical center, patient intake center, Medical Center, Medic Center | It triages/isolates/stamps, proposes patches without applying them, and writes RCA; it is not a monitor or auto-fixer |

Semantic-matching rules:

1. Match by the governance dimension, not by exact wording;
2. If it maps to one row above, use that layer and keep the original wording in the current record;
3. If a name could mean two layers, inspect what it actually reads/writes:
   - `ROUND-REGISTRY.json` / branch / worktree -> Command Center;
   - `THINKING-ROUNDS.json` / scoring / consultation -> General Staff;
4. If it matches nothing, or the decision changes scope/cost/irreversible action,
   **ask once before acting**, with concrete options:
   "By X do you mean: A Command Center (rounds/conflicts); B General Staff
   (thinking/consultation); C SOLO; D Medical Center?"
5. Do not invent a fifth governance layer just because the name is unfamiliar;
   match semantics or ask first.

## 1. One-page decision table

| You want to... | Use | Entry |
|---|---|---|
| Plan / review / write documents only | local-only | `python3 scripts/wf.py new-run ...` |
| Run 10+ control-plane rounds | workflow-group | `wf.py new-run` -> `append-status` -> `state` -> `new-round` |
| Run one declarative OpenRig workflow end-to-end | hybrid one-line | `rig workflow run <spec> --rig <rig> ...` |
| Inspect or debug a stuck workflow | hybrid debug | `rig workflow show/trace`, `rig queue list` |
| Send one manual message to a seat | debug only | `rig send <seat> "..."` |
| Reuse a stopped team | attached | `rig up <rig> --existing` |

## 2. Three layers

```text
SCTG protocol / kit
  card -> submission -> gate -> decision -> ledger
  package: sctg-kit/

workflow-group control plane
  PROJECT / SPEC / DECISIONS / STATUS / ISSUES
  roles: MAIN, PMO, TDO, QA, SAFETY
  one round = PMO plan -> TDO execute -> QA review -> MAIN decide

OpenRig execution plane
  rig / seats / queue qitems / workflow instance / steps / transcripts
  one step = one workflow packet handled by an actor role
```

`OPENRIG-BRIDGE.json` is the only mapping between the control plane and the
execution plane. It maps run id, rig, workflow id, seat map, OpenRig home, and
daemon port.

## 3. Terms that LLMs confuse

| Term | Meaning |
|---|---|
| **Rig** | A live team topology: pods, seats, edges. |
| **Seat** | One agent identity inside a rig (`main-analyst@my-rig`). |
| **Qitem / packet** | One queue item delivered to a seat. |
| **Workflow instance** | One run of a workflow spec; has a frontier and a step trail. |
| **Step** | A declared unit in a workflow spec (`audit`, `plan`, `qa`). |
| **Round** | A workflow-group cycle with STATUS/DECISIONS updates. |
| **Closure** | The seat reports the packet outcome (`done`, `failed`, `handoff`, ...). |
| **Bridge** | `OPENRIG-BRIDGE.json`; maps control-plane facts to execution state. |

### Step vs round

```text
12 steps:  one workflow instance with 12 declared steps
12 rounds: 12 PMO -> TDO -> QA -> MAIN cycles in workflow-group
```

They can be combined, but they are not the same count and should never be
described interchangeably.

## 4. Path A — 12 control-plane rounds

```bash
python3 scripts/wf.py new-run case-001 \
  --template templates/specialized/openrig-workflow-master \
  --goal "Harden a small service" \
  --project-root "$PWD" \
  --scope 'runs/case-001/**' \
  --tdo 1

# round 1
python3 scripts/wf.py append-status case-001 --agent tdo-a1 --ws WS-1 \
  --action "R1: implement" --evidence "evidence/r1.log" --no-commit
python3 scripts/wf.py state case-001 STATUS qa-pending --by main
python3 scripts/wf.py state case-001 STATUS qa-done --by qa
python3 scripts/wf.py new-round case-001

# ... repeat 12 times ...
```

See `examples/round-cases/` for three complete 12-round exports.

## 5. Path B — one-line OpenRig workflow

### 5.1 Prepare a rig with the target seat

```yaml
# /tmp/one-line.rig.yaml
version: "0.2"
name: "one-line-audit"
pods:
  - id: main
    label: Main
    members:
      - id: analyst
        agent_ref: "path:<OPENRIG_REPO>/packages/daemon/specs/agents/research/analyst"
        profile: default
        runtime: opencode
        cwd: "<project-root>"
        model: "deepseek/deepseek-flash"
    edges: []
edges: []
```

```bash
rig up /tmp/one-line.rig.yaml \
  --cwd "<project-root>" --non-interruptive --yes --json
```

### 5.2 Declare a one-step workflow

```yaml
# /tmp/one-line.workflow.yaml
workflow:
  id: one-line-audit
  version: 1
  objective: Audit the repository and write one report.
  target:
    rig: one-line-audit
  entry:
    role: analyst
  exception_routing:
    orchestrator_role: analyst
  roles:
    analyst:
      preferred_targets: [main-analyst@one-line-audit]
  steps:
    - id: audit
      actor_role: analyst
      objective: >
        Read README.md and docs/INDEX.md. Write exactly one file
        reports/one-line-report.md with a verdict and five findings.
        Do not modify other files. Close the packet when done.
      allowed_exits: [done, failed]
  invariants:
    allowed_exits: [done, failed]
  loop_guards:
    max_hops: 3
```

### 5.3 Validate and run

```bash
rig workflow validate /tmp/one-line.workflow.yaml --json

rig workflow run /tmp/one-line.workflow.yaml \
  --root-objective "Audit the repository" \
  --created-by main-analyst@one-line-audit \
  --rig one-line-audit --json
```

Exit codes:

```text
0  workflow completed
3  workflow failed or aborted
1/2 transport/API error
```

### 5.4 Inspect the trail

```bash
rig workflow show <instance-id> --json
rig workflow trace <instance-id> --json
rig ps --nodes --rig one-line-audit --json
```

## 6. Path C — manual debug mode

Use this only when a seat or packet needs inspection.

```bash
rig send main-analyst@one-line-audit "Read reports/one-line-report.md and reply with a 5-line summary." --verify
rig queue list --all-rigs --limit 50
rig queue show <qitem-id>
rig workflow show <instance-id>
rig workflow trace <instance-id>
```

Closing a packet manually:

```bash
rig queue update <qitem-id> --state done --closure-reason no-follow-on
```

Valid closure reasons include `handed_off_to`, `blocked_on`, `denied`,
`canceled`, `no-follow-on`, `escalation`. Closing a packet is not the same as
accepting the work.

## 7. Queue and packet lifecycle

```text
pending -> in-progress -> done
                     \-> blocked / handed off / canceled
```

Typical flow:

1. `rig workflow run` creates the entry packet.
2. The seat claims the packet (`pending -> in-progress`).
3. The seat writes evidence and reports an exit (`done`, `failed`, `handoff`).
4. The engine projects the next step packet, or completes the instance.

If the workflow looks idle but not complete, check:

```bash
rig queue list --all-rigs --limit 50
rig workflow show <instance-id>
rig ps --nodes --rig <rig>
```

## 8. Preflight, bridge, teardown

```bash
python3 scripts/openrig_preflight.py --json --no-monitor
python3 templates/specialized/openrig-workflow-master/render_master.py \
  --run-id demo-001 --project-root /tmp/demo-project \
  --output-dir runs/demo-001/openrig
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py doctor --run-dir runs/demo-001
python3 templates/specialized/openrig-workflow-master/tools/openrig_bridge.py status --run-dir runs/demo-001
```

Hard rules:

- unique rig name / workflow id;
- isolated `OPENRIG_HOME` and daemon port;
- no direct SQLite/queue mutation;
- archive before `rig down` / `rig daemon stop`;
- never turn a local-only pass into a hybrid E2E claim.

### Seat startup side effects

OpenRig seat startup may inject a managed block into `AGENTS.md` and create
`.agents/skills/`. For a public repo, remove both or explicitly document them:

```bash
git checkout -- AGENTS.md
rm -rf .agents
echo '.agents/' >> .gitignore
```

## 9. Memory and concurrency safety

Agent seats can grow far beyond visible RSS because the systemd scope accounts
page cache from broad reads. `ulimit -v` is not enough.

```text
MemoryHigh=5G  (soft, inside MemoryMax)
MemoryMax=6G   (hard RAM)
MemorySwapMax=1G (separate swap)
=> roughly 6G RAM + 1G swap, not 12G
```

Recommended profiles:

```text
first seat:  heavy  5G high / 6G max / 1G swap
second seat: light  3.5G high / 4.5G max / 0.5G swap
global:             8G high / 9G max / 2G swap
```

Use `examples/memory-limits/` and a user slice (`dsh.slice`) to bound the sum of
parallel seats. Do not run broad `find /`, `rg` over `$HOME`, or unbounded
output capture from a seat.

## 10. Troubleshooting matrix

| Symptom | Likely cause | Check / fix |
|---|---|---|
| Agent keeps calling shell tools, never writes report | Prompt too broad; no stop condition | Use a one-step workflow with one output file and bounded tool calls |
| `workflow run` stays active but seat is idle | Packet waiting for claim/closure | `rig queue list`, `rig workflow show` |
| `no_activity_signal` | Activity hook/relay not configured | Advisory; verify via `rig capture` and queue state |
| `workflow validate` is green but nothing ran | Validate is spec-only | Use `rig workflow run` or `instantiate` |
| Workflow completed but no report | Seat closed packet without writing file | Inspect `rig workflow trace` and workspace |
| `.agents/` appeared in repo | Seat startup injection | Restore `AGENTS.md`, remove `.agents/`, gitignore |
| Host OOM / huge memory scope | Page cache from broad scans | Apply cgroup limits; remove broad scans |
| `rig send` returns advisory | No activity hook / unknown sender | Use signed seat shell or `rig workflow run`; verify delivery |

## 11. Publishing and sanitization

Before publishing:

```bash
make check
make doc
make test
make demo
make bench-smoke
```

`make check` includes:

```text
scripts/check_repo.py
scripts/check_content.py
scripts/check_sanitization.py
compileall
```

Then rewrite public history to a clean single commit if earlier revisions
contained personal paths; delete old tags/releases; publish only the clean tag.

## 12. Command cheat sheet

```text
Control plane:
  wf.py new-run / new-round / append-status / state / doctor
  wf_close_lint.py --run <run-id>

OpenRig one-line:
  rig workflow validate <spec>
  rig workflow run <spec> --root-objective ... --created-by ... --rig ...
  rig workflow show/trace <instance-id>

OpenRig debug:
  rig up <rig.yaml> --plan
  rig up <rig.yaml> --non-interruptive --yes
  rig send <seat> "..."
  rig queue list / show / update
  rig ps --nodes --rig <rig>
  rig capture / transcript <seat>

Close:
  archive -> rig workflow abort/close -> rig down -> rig daemon stop
```

## 13. What this guide does not claim

- It does not claim a live 5-seat E2E pass.
- It does not claim model quality or benchmark results.
- It does not make `rig workflow run` a replacement for role contracts; the
  control plane still owns goals, decisions, and acceptance.
