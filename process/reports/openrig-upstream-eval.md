# gugu × Hermes 上游：跟版本 还是 钉版本（2026-10-25）

> 只读调研。上游克隆：`<HOME>/下载/deepseek/60-外部仓库/hermes-upstream`（`--filter=blob:none`，完整提交历史）。
> gugu 快照固定为 `22f6cbe9`（调研期间 gugu-work 的 HEAD 从 `3eb9c630` 漂移到 `22f6cbe9`，两者内核改动完全一致，见 §3.4）。
> 所有数字均可由文中命令复现；拿不到的写「未验证」。

---

## 1. 一页结论

### 结论：**A —— 跟着上游版本走**

理由：**上游的变动量是海量的，但 gugu 与上游的接触面极小且可枚举**。30 天、16,772 个上游提交之后，gugu 全部 2,215 行内核改动重新落地的实测代价是 **16 个冲突 hunk、14 个文件、4 个符号漂移**，且其中 65% 的内核新增行是纯新文件（零冲突面）。这属于「小改接入可控」，不属于「每个版本都是适配地狱」。

### 三条硬依据

| # | 依据 | 数字 | 证据 |
|---|---|---|---|
| 1 | **接触面有上限，不是无底洞** | gugu 只编辑 **26 个**上游已有内核文件（+774/−65 行），另有 **9 个全新文件**（+1,441 行，上游无对应文件 → 结构上不可能冲突） | `git diff --numstat 171fdfd7..22f6cbe9 -- agent tools hermes_cli gateway tui_gateway`，见 §3.3 |
| 2 | **30 天漂移的实测代价很小** | 16,772 个上游提交 / 8 个 release 之后：**12 个文件干净合并、14 个文件冲突、合计 16 个 hunk**；21 个可合并文件 **100% 编译通过** | `git merge-file --diff3` 逐文件三方合并，见 §3.3 / §3.5 |
| 3 | **产品层的三大件根本不碰内核** | 三模式壳、Design 画布 = **0 行内核改动**；上游自己提供插件/hook/插件路由（`_mount_plugin_api_routes` → `/api/plugins/<name>/`） | `git show --numstat f8695695 / 016bb536 / d64af3c8`；`web_server_dashboard.py:1002` |

### 一个数字

**每个上游 release 约 2 个冲突 hunk**（16 hunk ÷ 30 天内的 8 个 release），外加约 0.5 个符号漂移。
按低频 cadence（每月一次、覆盖 8 个 release）计：**每月约 16 个 hunk + 4 个符号 ≈ 0.5–1.7 人日**。

---

## 2. 上游画像

### 2.1 克隆结果

```
HEAD      571a5911ae6aaa05ef3df53bf0f6720c4556c24a  2026-10-24 12:01:20 -0700
          fix(gateway): a process watcher runs in its owning profile's scope throughout
branch    main            总提交 58,286        tag 总数 221
最新 tag  v0.22.5（2026-10-22，stable）；另有每日 canary：v0.22.5+canary.20261024T065630Z
```

> 任务书里写的「最新 tag v2026.9.24」实为**分叉基点**那个 tag；上游在 2026-10-08 起把日期式 tag 换成了 semver。
> `git rev-parse v2026.9.24` → `f97608f1`，提交信息 `chore: release v0.21.5 (2026.9.24)`。
> `git rev-list --count v2026.9.24..main` = **16,772**（与任务书一致）。

近 20 条提交（`git log --oneline -20`），可见几乎全是 fix / test / catalog 的细粒度演进，无大型重构宣告：

```
571a5911ae fix(gateway): a process watcher runs in its owning profile's scope throughout
c14a4400ad test(gateway): quote the release path in the handoff test
e56a5790a3 test(gateway): hold the handed-off process open until the handoff lands
fd29f67fe1 fix(gateway): a process handed to the parent completes into a parent turn, not a child one
97246dfcc2 chore(catalog): re-pin meshy to e746f4c6 (0.5.0)
14f14ed85a fix: keep the raw launch-key refusal code on a last Details line
a6d3d40bd5 fix: the late launch-key refusal and a reopened chat keep the /new remedy
f5900bf66e fix: a chat whose launch API key changed says so and names /new, not /retry
4dcef215cf fix(gateway): hold an image tag glued to punctuation or split across lines
01185213a3 fix(gateway): stream image tags prefix-stably and drop them from queued text
2959e3d93a fix(gateway): deliver a streamed reply's markdown images post-stream
99fcd69443 docs(memory): enabled: false keeps bare /refine working
20d4a80d69 fix(background-review): never requeue a preempted /refine for idle
46c9872a56 test(gateway): bare /refine runs while automatic reviews are disabled
2db3fba0c6 fix(background-review): preserve bare manual refine
d7094033f6 fix(oneshot): one-shot runs keep skill_manage
b73d7561af chore(catalog): re-pin blender to 9b11ffed (0.4.1: …)
adec2817ec chore(catalog): re-pin blender to 632c3df6 (0.4.0: …)
3403b92c4b refactor(gateway): directive hold-back in a sibling; hold a MEDIA prefix after punctuation
98373a07a7 chore: map santa-sketch's commit email for attribution
```

### 2.2 tag 节奏：这是「高速迭代」而非「稳定版本线」

`git tag --sort=creatordate` + 逐个 `git log -1 --format=%cs` 统计（只看正式 release tag，剔除 `+canary.*`、`rc.*`、`abandoned-*`）：

| 窗口 | release 数 | 间隔中位数 | 间隔均值 | 最短 / 最长 |
|---|---|---|---|---|
| 近 12 个月 | 41 | **5.0 天** | 5.6 天 | 0 / 14 天 |
| 近 20 个间隔 | — | **3.0 天** | 4.2 天 | 0 / 14 天 |
| 近 90 天 | 21 | **3.0 天** | 4.2 天 | 0 / 14 天 |
| 近 30 天（08-24…10-22 实测 8 个） | 8 | ~4 天 | — | — |

近 30 天的 8 个 release：`v0.21.6`(10-08)、`v0.21.7`(10-11)、`v0.22.0`(10-13)、`v0.22.1`(10-14)、`v0.22.2`(10-15)、`v0.22.3`(10-21)、`v0.22.4`(10-21)、`v0.22.5`(10-22)。

结论：**「每个版本」不是一个季度一次的事件，而是平均每 3–5 天一次**。任何「跟每个版本走」的方案都必须把单次成本压到小时级——这正是下面要量的。

### 2.3 内核目录 churn（近 12 个月）

```
git rev-list --count --since=2025-10-24 main -- <dir>
```

| 目录 | 近 12 月提交数 | 近 90 天 | 文件数 |
|---|---|---|---|
| `hermes_cli/` | **12,087** | 8,259 | 769 |
| `agent/` | 7,194 | 4,996 | 395 |
| `gateway/` | 7,162 | 4,419 | 331 |
| `tools/` | 6,501 | 4,195 | 368 |
| `tui_gateway/` | 2,508 | 1,973 | 118 |
| **合计** | **35,452** | 23,842 | 1,981 |
| 全仓（参照） | 58,249 | — | — |

改动最频繁的 20 个文件（`git log --since=2025-10-24 --name-only --no-renames -- agent tools hermes_cli gateway tui_gateway | sort | uniq -c | sort -rn`）：

| # | 提交数 | 文件 | gugu 是否改过 |
|---|---|---|---|
| 1 | 2,034 | `gateway/run.py` | ✗ |
| 2 | 1,218 | `hermes_cli/main.py` | ✗ |
| 3 | 1,011 | `hermes_cli/config.py` | ✗ |
| 4 | 1,002 | `tui_gateway/server.py` | ✗ |
| 5 | **756** | `hermes_cli/web_server.py` | ✓（+3 行） |
| 6 | 703 | `agent/auxiliary_client.py` | ✗ |
| 7 | **565** | `agent/context_compressor.py` | ✓（+7/−2） |
| 8 | **545** | `hermes_cli/models.py` | ✓（+10/−1） |
| 9 | 526 | `hermes_cli/gateway.py` | ✗ |
| 10 | 478 | `gateway/platforms/base.py` | ✗ |
| 11 | 465 | `agent/conversation_loop.py` | ✗ |
| 12 | 447 | `hermes_cli/auth.py` | ✗ |
| 13 | 423 | `agent/chat_completion_helpers.py` | ✗ |
| 14 | **395** | `hermes_cli/config_defaults.py` | ✓（+6/−3） |
| 15 | 376 | `hermes_cli/setup.py` | ✗ |
| 16 | 367 | `gateway/platforms/api_server.py` | ✗ |
| 17 | 360 | `agent/conversation_compression.py` | ✗ |
| 18 | 351 | `agent/model_metadata.py` | ✗ |
| 19 | 349 | `agent/agent_runtime_helpers.py` | ✗ |
| 20 | 344 | `hermes_cli/update_cmd.py` | ✗ |

**关键观察**：churn 最高的前 4 名 gugu 一行都没碰。gugu 的 26 个目标文件里只有 4 个落在 top-20。这是「接触面选得偏」的运气，也是 A 方案成本低的根本原因。

### 2.4 破坏性变更 / release notes：**没有**

- `ls CHANGELOG* RELEASE*` → No such file or directory
- `git ls-tree -r 571a5911ae | grep -cE "^docs/"` → **0**（上游仓库根本没有 `docs/`；文档在 `hermes-agent.nousresearch.com/docs` 站点）
- `README.md` / `CONTRIBUTING.md` 中 `grep -i "breaking\|semver\|api stability"` → 无 API 稳定性承诺
- 发布流程是**人工触发**：`.github/workflows/stable-release.yml` 的 `on:` 只有 `workflow_dispatch`（输入 claim tag）；另有 `canary-release.yml` 每日 06:41 UTC 自动打 canary

**含义**：跟版本不能靠读 changelog，只能靠**自己的 CI + 自建的符号漂移检查**兜底。这是 A 方案必须配套的纪律，也是它唯一的真实风险。

### 2.5 扩展点：上游自带的、且有兼容承诺

上游与 gugu 的插件 API 几乎同源（同一个 `VALID_HOOKS` 集合，上游还多 `on_session_delete`、`post_gateway_admission` 两个 hook）：

- `hermes_cli/plugins.py:108` `VALID_HOOKS`：约 40 个 hook，覆盖 `pre_tool_call` / `post_tool_call` / `pre_llm_call` / `transform_llm_output` / `on_session_start` / `pre_gateway_dispatch` / `pre_approval_request` / `post_approval_response` / `transform_api_error_classification` 等
- `hermes_cli/plugins_manifest.py:154`：**「manifest_version — absent means v1 (supported forever); api_version is the independent API generation」** ← 这是上游对插件格式的显式兼容承诺
- 插件能力字段：`provides_tools`、`provides_hooks`、`config_schema`、`capabilities`、`requires_hermes`（版本门）、`kind`（standalone/backend/exclusive/platform）
- 插件后端路由：`hermes_cli/web_server_dashboard.py:1002` `_mount_plugin_api_routes()`，把插件 `api` 文件里的 `router` 挂到 **`/api/plugins/<name>/`**（`web_server_dashboard.py:984`）；有信任门（只允许 `bundled`/`user` 源，且必须 `plugins.enabled` 显式启用，见 GHSA 注释）

---

## 3. 适配实测

### 3.1 方法

把 gugu 的 42 个提交（基点 `171fdfd7` → 顶点 `22f6cbe9`）落到上游 `main`（`571a5911ae`），三种层次各测一遍：

1. **提交级**：`git worktree add /tmp/hermes-eval main`，逐个 `git cherry-pick -n <sha>`
2. **文件级（主口径）**：对每个被改的上游文件做三方合并 `git merge-file -p --diff3 ours base theirs`，其中 base=`171fdfd7:f`、ours=`main:f`、theirs=`22f6cbe9:f`。这是 rebase 对单文件的等价操作，**不受提交顺序干扰**
3. **语义级**：AST 解析 gugu 文件的 import，检查上游是否还提供该符号

### 3.2 提交级统计

先看哪些提交真的动了内核（`git show --numstat` 过滤 `agent tools hermes_cli gateway tui_gateway`）：

**16 个提交 / 共 42 个** 触碰内核，其中内核行数最多的：
`cd73d657`(448)、`e24b4dc4`(361)、`54677bbc`(325)、`dea48343`(200)、`01744691`(196)、`e2d3649e`(141)、`bee9146a`(131)、`c6124521`(124)、`55a3a1a1`(114)。

逐个 `cherry-pick -n` 到 `main`：

| 结果 | 提交数 |
|---|---|
| 干净落地 | **5** |
| 冲突 | **11** |
| 合计冲突文件实例 / hunk | 49 / 26 |

**但提交级口径会系统性高估**，原因有两个，必须说明：

- 单独 cherry-pick 后面的提交时，它要修改的 `hermes_cli/gugu_service.py`、`docs/CHANGELOG-gugu.md`、`GUGU_VERSION`、`plugins/gugu-design/dashboard/plugin_api.py` 等文件是**更早的 gugu 提交创建的**，此时不存在 → 报 modify/delete 冲突（这些冲突的 `<<<<<<<` 数为 0，就是证据）。这是顺序假象，不是真实成本。
- 顺序叠加（stacked replay）走不通：**第 1 个提交 `cd73d657` 就有 6 个真内容冲突（UU）**，叠加脚本当场停住。也就是说「一遍 rebase 过去」确实做不成，必须人工过。

因此主口径改用下面的文件级三方合并。

### 3.3 文件级统计（主口径）

gugu 内核改动共 **35 个文件、+2,215 −65**：

| 类别 | 文件数 | 增/删 | 冲突可能性 |
|---|---|---|---|
| **全新文件**（上游无同名文件） | **9** | **+1,441 / −0** | **结构上为 0** |
| 修改上游既有文件 | **26** | **+774 / −65** | 见下 |
| 合计 | 35 | +2,215 / −65 | |

9 个新文件（占内核新增行 **65.1%**）：

```
+228  agent/plan_mode.py            +222  hermes_cli/web_routers/gugu_auth.py
+220  hermes_cli/gugu_service.py    +200  agent/token_meter.py
+179  tools/delegate_catalog.py     +141  agent/secret_redaction.py
+104  tools/approval_outcome.py     + 87  hermes_cli/version_source.py
+ 60  tools/plan_mode_tool.py
```

26 个修改文件的三方合并结果：

| 结果 | 文件数 | 承载行数 | hunk |
|---|---|---|---|
| **干净合并** | **12** | +557 / −29 | 0 |
| **冲突** | **14** | +217 / −36 | **16** |

冲突文件明细（按 hunk 数）：

| hunk | gugu 改动 | 文件 |
|---|---|---|
| 2 | +10 −1 | `hermes_cli/models.py` |
| 2 | +41 −2 | `tools/mcp_tool_transport.py` |
| 1 | +7 −2 | `agent/context_compressor.py` |
| 1 | +16 −0 | `gateway/run_inbound.py` |
| 1 | +4 −10 | `hermes_cli/_early_recovery.py` |
| 1 | +19 −3 | `hermes_cli/_startup_fast.py` |
| 1 | +23 −2 | `hermes_cli/banner.py` |
| 1 | +26 −11 | `hermes_cli/build_info.py` |
| 1 | +5 −1 | `hermes_cli/cli_commands_mixin.py` |
| 1 | +24 −0 | `hermes_cli/web_routers/oauth.py` |
| 1 | +3 −0 | `hermes_cli/web_server.py` |
| 1 | +15 −0 | `hermes_cli/web_server_oauth.py` |
| 1 | +10 −3 | `tools/approval.py` |
| 1 | +14 −1 | `tui_gateway/methods_tools.py` |

干净合并的 12 个（含最大单文件改动 `tools/mcp_liveness.py` +438/−1，上游近 12 个月只碰了它 6 次）：

```
+438 -1  tools/mcp_liveness.py        +48 -4  agent/credential_persistence.py
+18 -2   agent/turn_context.py        +17 -0  tools/delegate_tool_registry.py
+15 -0   agent/turn_context_compaction.py  +6 -3  hermes_cli/config_defaults.py
+4  -4   agent/account_usage.py       +3 -7   hermes_cli/main_install_repair.py
+3  -4   hermes_cli/update_cmd_maint.py    +2 -1  agent/usage_pricing.py
+2  -2   hermes_cli/commands.py       +1 -1   hermes_cli/uninstall.py
```

### 3.4 数据一致性说明

任务书给的「41 提交 / 179 文件 / +11,790 −11,116」与实测略有出入，实测：

| 快照 | 提交数 | shortstat |
|---|---|---|
| `6737fff0`（`gugu-v0.8.0` tag） | 38 | 175 files, +10,375 −11,116 |
| `3eb9c630`（调研开始时 HEAD） | 42 | 179 files, +11,804 −11,116 |
| `22f6cbe9`（**本报告口径**，调研中 HEAD 漂移至此） | 42 | **179 files, +11,809 −11,116** |

差异来自 v0.8.0 之后 4 个 `arch/` 提交（只动 `scripts/arch/` 与 docs，内核 0 行）。**内核 2,215 行在三种快照下完全相同**，不影响任何结论。

### 3.5 编译与语义

- **编译**：9 个新文件 + 12 个干净合并结果，`py_compile` **21/21 通过**，0 失败
- **符号漂移**（AST 解析 import，判定「在分叉基点存在、在 main 已消失」）：

| 文件 | 消失的符号 | 上游发生的事 |
|---|---|---|
| `hermes_cli/cli_commands_mixin.py` | `tools.browser_tool_lifecycle.cleanup_all_browsers` | 模块改名 → `tools/browser_session_lifecycle.py` |
| `hermes_cli/cli_commands_mixin.py` | `tools.browser_tool_cdp._stop_cdp_supervisor` | 同上，模块重组 |
| `tools/approval.py` | `tools.tirith_security.check_command_security`（2 处引用） | `tools/tirith_security.py` **整个文件被删除** |

**共 4 个符号 / 2 个文件**，每个都是 1–2 行的 import 改指。另有 33 处跨文件符号引用是 gugu 自己新模块提供的（合并后自然存在），不构成风险。

### 3.6 典型冲突示例（为什么冲突）

**① 类型 A：import / 注册表并集 —— 机械合并**

`hermes_cli/web_server.py`（gugu 插 gugu_auth 路由，上游同处插了 2 个新路由）：

```python
    dashboard_ui as _dashboard_ui_routes,
<<<<<<< ours(main)
    shared_metrics as _shared_metrics_routes,
    delegation as _delegation_routes,
||||||| base
=======
    gugu_auth as _gugu_auth_routes,
>>>>>>> theirs(gugu)
)
```

原因：**上游在同一个 import 列表的同一位置新增了路由**（`web_server.py:818-819`），gugu 也在那里加了一行。解法 = 三方都保留。1 分钟。

`tools/approval.py`（同样形态）：上游加了 `from agent.i18n import t`，gugu 把 `from tools import approval_context` 改成 `approval_context, approval_outcome`。解法 = 并集。

**② 类型 B：同区域重写 —— 需要真改**

`hermes_cli/models.py`（gugu 的「模态收口」撞上游的 catalog 探测重构）：

```python
<<<<<<< ours(main)
        from hermes_cli.chat_catalog import note_catalog_item
        probed = []
        for item in data.get("data", []):
            if isinstance(item, dict) and note_catalog_item(item):
                continue
            probed.append(item.get("id", ""))
||||||| base
=======
        # 模态收口：… 条目带 modality 字段时只保留聊天候选
        _chat_mods = {"chat", "text", "llm", ""}
        _kept = []
        for m in data.get("data", []):
            mod = str(m.get("modality") or "").strip().lower()
            if mod not in _chat_mods:
                continue
            _kept.append(m.get("id", ""))
>>>>>>> theirs(gugu)
```

原因：**上游把这段探测循环整体改写成 `note_catalog_item` + `probed` 两个新概念**，gugu 在旧结构上加了模态过滤。不是「同一行改了两次」，而是**旧函数被拆了**——必须把模态过滤重新表达在上游的新结构上（还要连带改 `return _probe_result(probed|_kept, …)` 那一行，即该文件的第 2 个 hunk）。这是今天唯一一处需要 15 分钟以上真实思考的冲突。

**③ 类型 C：整段替换（品牌/版本）—— 反复复发**

`hermes_cli/banner.py`（ours 28 行 / theirs 9 行）、`hermes_cli/build_info.py`（ours 2 行 / theirs 62 行）、`hermes_cli/_startup_fast.py`：gugu 把版本横幅与版本事实源整体换成 `gugu v… · upstream …` 的实现，上游同期也在改同一批函数（加 channel、local head、release_date）。这类冲突**每次 re-baseline 都会再来一遍**，因为两边都在持续改同一个函数，且语义上不可合并（gugu 要的是自己的品牌文案）。

`hermes_cli/_early_recovery.py` 是反向：`ours=0 行` —— 上游删掉了 gugu 插入点所在的整段。

---

## 4. 扩展点适配性

### 4.1 三大件：两件完全不碰内核

| 功能 | 内核改动 | 证据 |
|---|---|---|
| 三模式壳（工作/设计/编程） | **0 行** | `git show --numstat f8695695` 全部落在 `apps/desktop/src/**`（`modes.ts`、`mode-switcher.tsx`、`layout-presets.ts`）+ 一个 `.zcode/` 计划文档 |
| Design 画布 | **0 行** | `016bb536`（骨架）、`d64af3c8`（M2b 手势/注释）、`f4cbd633`（M2a 后端）三个提交全部落在 `apps/desktop/src/plugins/gugu-design/**` 与 `plugins/gugu-design/**` |
| 网页授权替换 | **4 个文件编辑（+45 行）** + 2 个新文件（442 行） | 见 §4.2 |

Design 之所以能 0 行，是因为上游本来就给了插件后端路由：`plugins/gugu-design/dashboard/plugin_api.py:1` 的 docstring 自己写着「挂载于 `/api/plugins/gugu-design/`」，靠 `_mount_plugin_api_routes()`（`hermes_cli/web_server_dashboard.py:1002`）自动挂载；工具与 hook 由 `plugins/gugu-design/plugin.yaml:6-9` 的 `provides_tools: [design_generate]` / `provides_hooks: [post_tool_call]` 声明。

### 4.2 必须动内核的清单（按机制给原因）

| 功能 | 文件 | 行数 | 为什么非改内核不可 |
|---|---|---|---|
| **网页授权** | `hermes_cli/web_server.py` | **+3 / −0**（`:965` import、`:1007` `include_router`） | 上游 34 个 router 全是**静态** `app.include_router(...)`（`web_server.py:788-827`）；插件路由机制只能挂到 **`/api/plugins/<name>/`** 前缀下（`web_server_dashboard.py:982`），而 gugu 登录页要占 `/login`、`/auth/*` 根路径。**当前扩展点无法表达根路径路由** |
| | `hermes_cli/config_defaults.py` | +6 / −3 | gugu provider 的默认配置项，写在模块级默认表里 |
| | `hermes_cli/web_routers/oauth.py` | +24 | 设备码流程里插 `provider_id == "gugu"` 分支，在既有 flow 函数内部 |
| | `hermes_cli/web_server_oauth.py` | +15 | `_OAUTH_PROVIDER_CATALOG` 元组追加 gugu 条目（模块级常量，无注册接口） |
| **Plan 模式** | `gateway/run_inbound.py` | +16 | 入站分发处需要按 session 查计划状态并短路；`pre_gateway_dispatch` hook 只能 skip/rewrite 文本，不能改状态机 |
| | `tui_gateway/methods_tools.py` | +14 | 斜杠命令表 `_cmd_*` 是模块级静态绑定（`_prompt_builtin`）；插件无命令注册能力 |
| | `hermes_cli/cli_commands_mixin.py` | +5 | CLI `/plan` 入口需 `apply_plan_command()` 前置校验 |
| **审批 fail-closed** | `tools/approval.py` | +10 / −3 | 结果集统一在 `approval.py` 内部；hook 只能观察——`VALID_HOOKS` 注释明写「Approval observers… **plugins cannot veto or pre-answer**」 |
| **密钥脱敏** | `agent/credential_persistence.py` | +48 / −4 | 脱敏必须发生在「落盘」内部；无对应 hook |
| | `agent/context_compressor.py` | +7 / −2 | 压缩摘要出口同样在内核函数体内 |
| **MCP 看门狗** | `tools/mcp_tool_transport.py` | +41 / −2 | 传输生命周期（close/404 重初始化）是传输内部状态，无扩展点 |
| **token 计量** | `agent/turn_context.py` +18、`turn_context_compaction.py` +15、`context_compressor.py` +7、`account_usage.py` +4、`usage_pricing.py` +2 | 46 | 预算**硬拒发**必须在 turn 入口同步判定；hook 是 fail-open 的 |
| **版本/品牌** | `build_info.py` +26/−11、`banner.py` +23/−2、`_startup_fast.py` +19/−3、`_early_recovery.py` +4/−10、`main_install_repair.py` +3/−7、`update_cmd_maint.py` +3/−4、`uninstall.py`、`commands.py`、`config_defaults.py`、`models.py`、`cli_commands_mixin.py` | ~100 | 版本事实源、横幅文案、自更新/卸载文案；属「产品身份」，与上游同函数持续竞争（见 §3.6 类型 C） |

**归并后的结论**：真正「机制上没有扩展点」的只有 **4 处**——根路径 web 路由、审批结果集、MCP 传输内部、turn 入口硬拒发；其余是「虽然能改，但上游也有同类机制，改动量极小」。这 4 处合计 **+3 行**（web_server 三行）到 ~60 行，是**可枚举、不会随上游增长**的固定成本。

---

## 5. 每版本成本模型

### 5.1 基准

- 30 天窗口（`v2026.9.24` → `main`）：16,772 提交、**8 个 release**、14 个文件冲突、**16 个 hunk**、4 个符号漂移
- 摊到每个 release：**2.0 hunk + 0.5 符号**
- 上下限：gugu 只编辑 26 个上游文件，所以**单次 re-baseline 的 hunk 上限 ≈ 26–40**（每个文件 1–2 个 hunk），不会无限恶化

### 5.2 单次 re-baseline（按月、覆盖 ~8 个 release、16 个 hunk）

成本 = hunk 处理 + 固定开销（跑 3,114 行测试、打包 smoke、发版验证）。**固定开销是估算，不是实测**（依赖未装，测试未实跑）。

| 档位 | 触发条件 | hunk 处理 | 固定开销 | 单次合计 |
|---|---|---|---|---|
| **低** | 16 个 hunk 全是 import/注册表并集 | 16 × 5 min ≈ 1.3 h | 2 h | **≈ 0.5 人日** |
| **中** | 掺 1–2 个同区域重写 + 符号改指 | 16 × 20 min ≈ 5.3 h | 8 h | **≈ 1.7 人日** |
| **高** | 上游整段搬走 gugu 依赖的函数，测试要跟着改 | 16 × 60 min ≈ 16 h | 24 h | **≈ 5 人日** |

依据：今天 16 个 hunk 里约 10 个是 import/注册表并集（`web_server.py`、`approval.py`、`context_compressor.py`、`web_server_oauth.py`、`oauth.py`、`cli_commands_mixin.py` 等），每个 1–5 分钟；`models.py` 形态的同区域重写 1 处，15–30 分钟；符号漂移 4 个，各 5 分钟。**高**档的历史样本：`tools/tirith_security.py` 被整文件删除、`browser_tool_lifecycle` 改名——这类落在 gugu 清单内就要重写而非合并。

### 5.3 全年（41 个 release）三种 cadence 对比

单次 hunk 数随间隔近似线性（8 release → 16 hunk，即 **2 hunk/release**），但受「只改 26 个上游文件、每文件 1–2 hunk」的结构上限压制，超过约 24 个 release 后不再线性增长：

| 节奏 | 次数 | 每次 hunk | 全年 hunk | 全年人日（低 / 中 / 高） |
|---|---|---|---|---|
| 每个 stable tag 都跟（~3 天） | 41 | 2 | 82 | 11 / 45 / 133 |
| **每月（推荐）** | 12 | 16 | 192 | **5 / 20 / 60** |
| 每季度 | 4 | ~45（线性外推 48，受上限压制） | ~180 | 3 / 12 / 35 |

读法：**每个 tag 都跟是最差解**——hunk 虽少，但 41 次固定开销（测试 + 打包 + 发版）压死人，全年高达 133 人日。季度跟最省人日，但一次跨 24 个 release、约 5 万个提交，语义漂移窗口太大（30 天就有 4 个符号漂移 → 一季约 12 个，且成片出现），只能靠自动化检查兜。**月度是唯一同时压住「人日」和「漂移窗口」的点**。

**判断「是不是地狱」**：地狱应定义为「单次适配 > 1 周且随版本持续恶化」。实测中位是 **1–2 人日/月**，且有 26 文件的结构上限使成本不会随上游提速而爆炸，**不构成地狱**。

---

## 6. 固定版本候选（若翻案到 B）

若将来触发翻案条件（见 §7.3），钉版本建议如下。**注意：所有晚于 `v2026.9.24` 的 tag 与 gugu 基点之间的适配成本是一样的（都是那 16 个 hunk）**，因此「钉哪个」应优先选**最新**的，白拿安全修复。

| 候选 | 提交 | 日期 | 取舍 |
|---|---|---|---|
| **`v0.22.5`（推荐）** | `bf0203a7` | 2026-10-22 | 距 main 仅 **541** 个提交，安全修复最全；适配成本 = 本报告实测的 16 hunk；后续 backport 需在「几乎等于 main」的基线上做 cherry-pick，冲突概率与本报告同量级 |
| `v0.22.0` | — | 2026-10-13 | 比 `v0.22.5` 旧 9 天、少 5 个 patch 版本；若怀疑 `v0.22.1–.5` 有回归可用它。适配成本相同，但没有白拿的东西 |
| `v2026.9.24`（= 现在的基点） | `f97608f1` | 2026-09-24 | **零适配成本**，但要背着 30 天 / **16,231** 个提交的差距，等于放弃这期间的修复；除非决定「永不动上游」，否则不建议 |

不建议钉在 canary（`v0.22.5+canary.*` 每天一个，无稳定性承诺）或 `rc.*`（存在 `abandoned-rc.*` 先例）。

---

## 7. 决策与翻案条件

### 7.1 决策：**A —— 跟上游（按上游纪律，小改接入）**

量化依据：接触面固定（26 个既有文件 / +774 行）、30 天漂移只产生 16 hunk、65% 的内核改动是零冲突的新文件、4 个符号漂移各 1 行可修、21 个可合并文件全编译通过、三大产品件中两件 0 行内核改动。**没有任何一项指向「灾难性适配地狱」**。

### 7.2 A 方案台账

| 项 | 规定 |
|---|---|
| **跟踪对象** | 只跟 **stable release tag**（`v0.22.x`），**不跟 main**、不跟 `+canary.*`。理由：stable 是人工 `workflow_dispatch` 发布（`stable-release.yml`），canary 每日自动、无稳定性承诺 |
| **re-baseline 周期** | **每月一次**（覆盖约 8 个 release）；安全类 release 单独插队。不要每 tag 都跟——固定开销（测试+打包）比 hunk 数更贵 |
| **补丁栈上限** | 修改上游既有文件 **≤ 30 个 / ≤ 900 行**（当前 26 / 774，余量 +4 文件）；新功能一律走插件，**内核新增行只允许 ≤ 100 行/年** |
| **CI 要求** | ① gugu 测试全绿（`tests/` 18 文件 3,114 行）② 符号漂移检查 **0 未解析**（本报告的 AST 检查脚本可直接产品化）③ 每次 re-baseline 产出「文件级三方合并报告」作为 PR artifact ④ 桌面端打包 smoke（`desktop-bundle-smoke.yml` 同款）⑤ 21 文件 `py_compile` 门 |
| **实现形态** | vendor 分支 + 补丁队列：`upstream/main` 只读镜像 → `gugu-base`（分叉点）→ 每个 gugu 提交保持「可单独 cherry-pick」粒度。已实测：16 个内核提交中 5 个可独立干净落地，其余需按顺序 + 人工合并 |
| **禁止** | 不许深改名上游文件、不许把产品逻辑塞进 `gateway/run.py` / `hermes_cli/main.py` 这类 top-churn 文件（前 4 名 churn 文件 gugu 目前 0 改动，这是优势，要守住） |

### 7.3 何时该翻案到 B（钉 `v0.22.5` 并停跟）

出现**任意两条**即翻案：

1. **成本恶化**：单次 re-baseline 的冲突 hunk > **60**（即 26 个文件平均 2 个以上），或连续 2 次 re-baseline 超过 **3 人日**
2. **接触面扩张**：内核补丁栈突破 **40 个文件 / 1,500 行**，或开始出现 `gateway/run.py`、`hermes_cli/main.py`、`hermes_cli/config.py`、`tui_gateway/server.py` 这四个 top-churn 文件的改动
3. **扩展点承诺破裂**：上游对 `api_version` 做破坏性提升 / 移除 `VALID_HOOKS` 里的 gugu 依赖项 / 插件 manifest v1 不再「supported forever」（`plugins_manifest.py:154`）
4. **语义漂移失控**：单月符号漂移 > **20 个**（当前 4 个），或出现「整文件删除」落在 gugu 修改清单内（`tirith_security.py` 已发生过一次）
5. **节奏失控**：上游持续 > 2 个 stable release/周，导致月度 cadence 覆盖不了安全修复
6. **测试不可修复**：gugu 测试在上游新基线上无法在一个周期内转绿

### 7.4 若翻案，B 的纪律（预置）

- 钉住 `v0.22.5`（`bf0203a7`，见 §6），gugu 仓库打 tag `gugu-base-v0.22.5`，`upstream` remote 改为只读参考、不再合并
- 只做**按需安全 backport**：CVE/凭据泄漏类补丁从上游单 commit `cherry-pick -x`，每个 backport 记一条 `docs/SECURITY-BACKPORTS.md`（上游 commit + 理由 + 测试）
- **每 90 天重新评估一次**：跑一遍本报告的 16-hunk 实测脚本 + 符号漂移检查；若实测成本降到 < 0.5 人日/月且翻案条件已消失，可重新回到 A

---

## 附录：未验证项

| 项 | 原因 |
|---|---|
| **逐 release 的冲突时间序列**（v0.21.6…v0.22.5 各打一次） | 需要一个 tag 的 blob，partial clone 需回源拉取；代理报 `CONNECT tunnel failed, response 502`，`git fetch` 无法完成。已改为用「30 天累积漂移 ÷ 8 个 release」摊薄，并标注为推算 |
| **gugu 测试实跑**（`tests/` 3,114 行） | 依赖未安装（`.venv` 存在但未在本次只读范围内安装/运行）。因此「中/高」两档的人日里，测试修复时间是估计而非实测 |
| **合并后树的运行时行为 / 桌面端构建** | 同上，未启动服务、未打包 |
| **上游对 gugu 的 3,114 行测试的破坏程度** | 需实跑才能给出；这是 A 方案最大的未知项，也是 §7.2 CI 门①要长期兜住的 |
