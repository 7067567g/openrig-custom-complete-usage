# openrig-local 0.1.4 分享包 —— 打包与脱敏报告

- 日期：2026-10-25
- 源仓库：`<OPENRIG_SRC>`（只读；未改动）
- 源版本：`openrig-local` **0.1.4**，HEAD `1ee477a`（docs(release): record the 0.1.4 gate results）
- 产物目录：`<WORKSPACE>/dist/openrig-local-0.1.4-share-20261025/`
- 压缩包：`<WORKSPACE>/dist/openrig-local-0.1.4-share-20261025.tar.gz`
- 压缩包 SHA-256：`885026e8a6ab370c18ea2a8c4c1007b8e13e5dbb7b2e72045237cd99b4f1f090`
- 压缩包大小：**19,525,781 字节**（约 18.6 MiB）；tar 内条目 **4302**（3830 文件 + 467 目录 + 5 符号链接）
- 源工作树状态：`git status --porcelain` = 0 行（干净）；源 `node_modules` 未被构建触碰（mtime 检查 0 个变更文件）

## 1. 交付物

| # | 交付物 | 路径 | 大小 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | 源码分享目录 | `dist/openrig-local-0.1.4-share-20261025/` | 48,729,927 B（46.5 MiB），3830 文件 | 代码 + 文档 + 构建说明 + workflow + 已构建 tarball |
| 2 | 分享压缩包 | `dist/openrig-local-0.1.4-share-20261025.tar.gz` | 19,525,781 B（18.6 MiB），4302 条目 | 上方 SHA-256 |
| 3 | npm 安装包 | `.../artifacts/openrig-local-cli-0.1.4.tgz` | 7,620,093 B（7.3 MiB），4474 文件 | `npm i -g` 可装；SHA-256 `0ba15217…cab5bd`（完整值见 §6） |
| 4 | 本报告 | `the assistant project/openrig-local-share-20261025-REPORT.md` | — | 与包同级，不在压缩包内 |

压缩包不含 `.git`，因此没有附带 `git bundle`。取舍：源码包是“可构建、可安装”的快照；历史留在源仓库，
避免把内部提交元数据带进分享物。如果确实要历史，建议在源仓库执行 `git bundle create openrig-local-0.1.4.bundle --all`
后单独传递，而不是塞进这个包。

## 2. 文件清单

### 2.1 顶层

| 路径 | 文件数 | 大小 | 说明 |
| --- | --- | --- | --- |
| `README-SHARE.md` | 1 | 13 KB | 本包专用说明（新增） |
| `README.md` / `ARCHITECTURE.md` / `ROADMAP.md` / `CHANGELOG.md` / `CONTRIBUTING.md` / `SECURITY.md` / `CODE_OF_CONDUCT.md` | 7 | 421 KB | 项目文档；README 顶部加了一段指向 README-SHARE 的说明 |
| `LICENSE` | 1 | 10.5 KB | Apache-2.0，未改 |
| `UPSTREAM-BASE` | 1 | 4.4 KB | 上游血缘与 fork 政策（权威） |
| `package.json` / `package-lock.json` / `tsconfig.base.json` / `vitest.config.ts` / `.gitignore` / `context7.json` | 6 | 258 KB | 根配置 |
| `packages/` | 3460 | 43 MB | daemon / cli / tui / ui / test-system 源码与测试 |
| `scripts/` | 81 | 784 KB | 构建、打包、校验、门禁、归档/teardown |
| `skills/` | 55 | 784 KB | 随包 skills（含 `_canonical`） |
| `docs/` | 164 | 2.0 MB | as-built / reference / releases |
| `assets/` | 5 | 1.7 MB | README GIF 与截图 |
| `demo/` | 16 | 104 KB | 演示 rig 与脚本 |
| `docker/` | 16 | 112 KB | 测试床 Dockerfile/runbooks |
| `test/` | 2 | 20 KB | 跨包测试脚手架（hermetic env / stub runtimes） |
| `.github/` | 7 | 44 KB | CI 与 issue/PR 模板 |
| `workflow/` | 7 | 60 KB | 长任务工作流（新增，见 §5） |
| `artifacts/` | 1 | 7.3 MB | `openrig-local-cli-0.1.4.tgz` |

### 2.2 `workflow/` 明细

| 文件 | 作用 |
| --- | --- |
| `README-WORKFLOW.md` | 使用说明：为什么、分工、生命周期、心跳/恢复、控制面、最小示例、注意事项 |
| `loop_supervisor.py` | 监护器（watch/init/list/status/dry-run/run-next/mark-blocked） |
| `plan.json` | 示例计划：2 个回环 × 2 轮，`loops[].rounds[]` 含 `run_id/type/goal/inputs/budget_sec` |
| `ROUND-SPEC.md` | 每轮通用契约（通用化后的版本） |
| `openrig-loop.service` | systemd user unit 模板（路径全占位符） |
| `templates/PROJECT.md`、`templates/SPEC.md` | run 契约面 / 单轮产出清单模板 |

### 2.3 npm tarball（`artifacts/`）

`npm pack` 结果：包名 `@openrig-local/cli`、版本 `0.1.4`、4474 文件、解包 27.9 MB。
内容为 `LICENSE`、`README.md`、`dist/`、`daemon/{dist,assets,specs,policies,docs,context-packs}`、`ui/dist`、`tui/dist`、`scripts/`。
已单独解包扫描：无本机身份串、无密钥形状、无 `node_modules`/日志/数据库/`.env*`。

完整清单可复现：`tar -tzf openrig-local-0.1.4-share-20261025.tar.gz | sort`（4302 条）。

## 3. 排除清单

| 排除项 | 原因 | 证据 |
| --- | --- | --- |
| `node_modules/`（根与各 workspace） | 依赖产物，可由 `npm ci` 重建；体积大且含本机安装状态 | 包内 `find . -name node_modules` 为空 |
| `.git/` | 分享包只要源码快照；避免内部提交元数据 | 包内无 `.git`；tar 头 owner 归一为 `0/0` |
| `packages/*/dist/` | 构建产物，README-SHARE 给出构建命令 | 包内无 `dist` 目录；tarball 由构建副本产出 |
| `var/`（含已跟踪的 `var/openrig-archive/*.md`） | run 归档/历史数据；3 个 tracked 文档也引用具体 run，按“不带 runs/历史数据”处理 | 包内无 `var/` |
| `.claude/`、`.agents/` | 开发用 agent 脚手架（各含 1 个 tracked skill） | 已移除 |
| `.codegraph`（符号链接） | 指向 `<HOME>/...` 的本机工具路径 | 已移除；包内无悬空链接 |
| `AGENTS.md` | 本机 run 的作业书，含 3 处本机绝对路径与内部 run 目录 | 已移除（未改写，避免留下半截 run 上下文） |
| `*.log` | 运行日志 | 包内 0 个 |
| `*.tgz`（除 `artifacts/` 自产） | 构建产物 | 包内只有 `artifacts/openrig-local-cli-0.1.4.tgz` |
| `*.sqlite*` | 本机数据库/会话数据 | 包内 0 个 |
| `.env*` | 凭据 | 包内 0 个 |
| `runs/`、会话/历史数据 | 不分享运行记录 | 包内无 `runs/`；无 `web-sessions.json`/`weixin-auth.json`/session 清单 |
| `.DS_Store` | macOS 垃圾 | 包内 0 个 |
| `scripts/__pycache__/`、`workflow/__pycache__/` | Python 字节码 | 已清理；包内 0 个 |
| `var.7z`、`.evidence/` | 源仓库根部的本机归档/内部证据，未进入 `git archive`，也不在分享包内 | 包内无 |

## 4. 脱敏逐项证据

### 4.1 模式 → 处理 → 结果

在**源树**（`git archive HEAD` 解出的 pristine 副本）上统计“处理前”，在**最终包**（tar 解包）上统计“处理后”：

| 模式 | 处理前 | 处理动作 | 处理后 |
| --- | --- | --- | --- |
| `<HOME>` | **3**（全部在 `AGENTS.md:33/36/70`） | 删除 `AGENTS.md`（本机 run 作业书，非产品文档） | **0** |
| 主机名 `<HOST>` | 0 | 无需处理（全树未出现） | **0** |
| `<HOME>` 所在的用户名串 `<USER>` | 3 | 同上 | **0** |
| `sk-[A-Za-z0-9]{18,}` | **15**（`restore-packet.test.ts` 10、`agent-starter-resolver.test.ts` 3、`transcript-routes.test.ts` 2） | 12 处改为 `sk-test-…` 假 token；3 处改为运行时拼接 `["sk","fake".repeat(8)].join("-")`；语义不变，测试全绿 | **0** |
| `DEEPSEEK_API_KEY\s*=` | 0 | 无需处理；文档/代码只出现变量名，不出现赋值 | **0** |
| `OPENCODE_*_KEY` 赋值形状 | 0 | 无 | **0** |
| 本机路径 `下载/deepseek/...` | **4**（`AGENTS.md` 3、`path-headers.test.ts:22` 1） | 删除 `AGENTS.md`；测试路径改为通用非 ASCII 路径 `/home/用户/项目/示例仓库`（保留百分号编码测试意图） | **0** |
| `http-path-headers.test.ts` 的本地中文路径 | 1 处（`/home/下载/项目` + 硬编码百分号编码） | 改为 `/home/用户/项目`，同步更新 `%E7%94%A8%E6%88%B7/%E9%A1%B9%E7%9B%AE` | **0** |
| `packages/daemon/assets/dsh/dsh-web-shim.py` 的「the control plane」注释 | 1 处 | 改成英文通用注释（“browse from an existing workspace”） | **0** |
| `<HOME>/.nvm/...`（`opencode-dsh/README.md` 示例） | 2 处 | 改为 `$HOME/.nvm/...` | **0** |
| `web-sessions.json`、`weixin-auth.json`、`session-*` 清单 | 0 个数据文件 | 无需处理；`session-*` 命中的都是源码/测试文件名 | **0** |
| `runs/` 引用 | 文档里有内部 run-id 作为证据标签（如 `runs/openrig-r23-deps/reports/`） | **不打包 run 数据**；保留文字标签，报告中说明它们指向未随包分发的内部报告 | 无数据文件 |

> 许可证说明：任务描述里写的是 MIT，但仓库 `LICENSE` 实际是 **Apache-2.0**（与上游一致）。本包**未改许可**，
> `README-SHARE.md` 也按 Apache-2.0 声明。如果确实需要 MIT，得先由仓库所有者改许可，不能在打包时替换。

### 4.2 相对源树的改动（`diff -rq` 结果）

内容修改 9 个 tracked 文件：

1. `README.md`（顶部加指向 `README-SHARE.md` 的说明）
2. `scripts/build-package.sh`（无 `.git` 时可构建：commit 戳留空，不伪造 SHA）
3. `packages/cli/test/http-path-headers.test.ts`（中文测试路径通用化）
4. `packages/cli/test/restore-packet.test.ts`（假 token 加 `test-` 前缀）
5. `packages/daemon/test/agent-starter-resolver.test.ts`（假 token 运行时拼接）
6. `packages/daemon/test/path-headers.test.ts`（本机路径通用化）
7. `packages/daemon/test/transcript-routes.test.ts`（假 token 加 `test-` 前缀）
8. `packages/daemon/assets/dsh/dsh-web-shim.py`（注释通用化；`DSH_BRIDGE_DIR` 可覆盖，默认值不变）
9. `packages/daemon/specs/rigs/focused/opencode-dsh/README.md`（`/home/dev` → `$HOME`）

删除 5 项：`AGENTS.md`、`var/`、`.agents/`、`.claude/`、`.codegraph`。
新增 3 项：`README-SHARE.md`、`workflow/`、`artifacts/`。

### 4.3 改动后的测试证据

在构建副本里跑受影响的测试（不是只看 grep）：

```text
packages/cli:    npx vitest run test/restore-packet.test.ts test/http-path-headers.test.ts
                 → Test Files 2 passed (2), Tests 113 passed (113)
packages/daemon: npx vitest run test/transcript-routes.test.ts test/agent-starter-resolver.test.ts \
                                test/path-headers.test.ts test/dsh-web-shim.test.ts
                 → Test Files 4 passed (4), Tests 46 passed (46)
```

`agent-starter-resolver` 的凭据扫描仍按原语义拒绝 token 形状；`restore-packet` / `transcript-routes` 的
redaction 仍把 `sk-test-…` 识别为 `[REDACTED]`（`sk-[A-Za-z0-9_-]{16,}` 允许连字符）。改的是“fixture 字面量”，
不是被测逻辑。

## 5. `workflow/` 收录与改动

### 5.1 来源 → 落点

| 源 | 落点 | 处理 |
| --- | --- | --- |
| `60-外部仓库/workflow-group/openrig-pipeline/loop_supervisor.py` | `workflow/loop_supervisor.py` | 去本机路径/凭据文件；路径改环境变量；`ensure_run` 改为本地模板渲染 |
| 同目录 `ROUND-SPEC.md` | `workflow/ROUND-SPEC.md` | 本机路径/仓库名/版本/“3080/the bridge”改通用边界与占位符 |
| 同目录 `loop-plan.json` | `workflow/plan.json` | 重写为示例：2 回环 × 2 轮，run-id 通用，goal/inputs 用 `<YOUR_*>`，保留结构字段 |
| `templates/specialized/openrig-loop-round/{PROJECT,SPEC}.md` | `workflow/templates/{PROJECT,SPEC}.md` | 本机路径/项目名/版本改占位符 |
| `openrig-pipeline/openrig-loop.service` | `workflow/openrig-loop.service` | 全部路径改占位符；key 走 `EnvironmentFile`；补 `ExecStartPre` 建日志目录 |

### 5.2 为“可直接复用”做的适配

- **路径全部可配**：`OPENRIG_LOOP_PROJECT` / `OPENRIG_LOOP_RUNS` / `OPENRIG_LOOP_ROOT` /
  `OPENRIG_LOOP_TEMPLATES` / `OPENRIG_LOOP_PLAN` / `DSH_BIN`；默认值依次为目标仓库（本目录父级）、
  `workflow/runs`、父级、`workflow/templates`、`workflow/plan.json`、PATH 上的 `dsh`。
- **凭据只读环境变量**：删掉了原来读 `<DSH_HOME>/.credentials.yaml` 的 `load_key()`；
  缺 `DEEPSEEK_API_KEY` 时直接失败并写 `worker-result.json`（exit 4），不会读任何凭据文件。
- **不再依赖外部 `wf.py`**：`ensure_run()` 直接读 `templates/`，渲染 `<RUN-ID>/<GOAL>/<PROJECT-ROOT>/
  <WRITE-SCOPE>/<TDO-N>/<DATE>` 后写 `runs/<id>/{PROJECT,SPEC}.md` 和 `reports/`。
- **心跳语义落地**：worker 每 60s 写 `worker.json`；监护器默认每 120s tick；心跳停更超过
  `OPENRIG_LOOP_HEARTBEAT_TIMEOUT`（默认 180s）先 SIGTERM，两倍阈值后 SIGKILL；缺 `DONE`/`VERDICT.md`
  → nudge，6 次 → `BLOCKED`；全部完成/阻塞 → `LOOPS-DONE`；`VERDICT=STOP` → `LOOPS-STOPPED`。
- **控制面**：`--init` / `--list` / `--status` / `--dry-run` / `--run-next` / `--watch` /
  `--mark-blocked`；`PAUSED` / `STOP` / `LOOPS-DONE` / `LOOPS-STOPPED` 文件语义与原文一致。
- **文档**：`README-WORKFLOW.md` 覆盖：为什么用监护器、三文件分工、一轮生命周期、
  心跳/恢复、控制面、最小示例（改 2 轮 → 起 unit → 看 `logs/supervisor.log`）、
  `dsh --profile headless` + key 只走环境变量的注意事项。

### 5.3 workflow 自检

在 `/tmp/wf-selftest` 的副本里跑（不污染分享目录）：

```text
python3 -m py_compile loop_supervisor.py                → OK
python3 loop_supervisor.py --init                       → 建 4 个 run（PROJECT.md/SPEC.md/reports/）
python3 loop_supervisor.py --list                       → 4 行 pending
python3 loop_supervisor.py --dry-run                    → 打出完整本轮 prompt
4 轮全部 --mark-blocked 后 --watch --interval 30         → 写 LOOPS-DONE，exit 0
touch PAUSED && --run-next                              → “PAUSED 存在；拒绝启动”
env -u DEEPSEEK_API_KEY --worker loop1-r1-audit          → exit 4，worker-result.json = no_key
```

脱敏自检：

```text
$ grep -rInE '<USER>|<HOST>|sk-[A-Za-z0-9]{18,}|DEEPSEEK_API_KEY\s*=|<HOME>' workflow/
（0 行）
```

## 6. 构建与试装

### 6.1 环境

- 源仓库 Node `v24.22.1`，npm `11.19.1`，Python `3.14.4`
- 构建在副本 `dist/.build-openrig-local-0.1.4/` 里做，源目录只读；依赖用硬链接复用源 `node_modules`
  （含各 workspace 的 `node_modules`），**全程无网络安装**。

### 6.2 构建命令与结果

```bash
npm run build            # daemon/ui/tui/cli（tsc + vite）
npm run build:package    # 组装 packages/cli/{daemon,ui,tui}、生成 context-packs、重写 import
cd packages/cli && npm pack --pack-destination ../../artifacts
```

关键输出：

```text
No git metadata in ...: building without a commit stamp.
Build identity: 0.1.4 () dirty=false at 2026-10-24T20:43:45Z
[generate-context-packs] wrote 57 pack(s)
Rewrote 33 @openrig-local/daemon import(s) in 20 file(s)
CLI dist: 183 JS files | Daemon dist: 727 JS files | Daemon assets: 65 | specs: 138
Daemon policies: 6 | docs: 85 | UI dist: 68 | TUI dist: 284
npm notice name: @openrig-local/cli / version: 0.1.4
npm notice package size: 7.6 MB / unpacked: 27.9 MB / total files: 4474
```

`build:package` 的两处改动（均在副本里，分享包内也生效）：

1. 无 `.git` 时不再 `git rev-parse` 失败：commit 戳留空 → `rig --version` 干净输出 `openrig-local 0.1.4`
   （不伪造 SHA；有 `.git` 的 clone 仍正常打戳）。
2. `STAMP_DIRTY` 只在有 commit 时才跑 git status。

### 6.3 tarball 校验

- 文件：`artifacts/openrig-local-cli-0.1.4.tgz`，7,620,093 B，4474 文件。
- SHA-256：`0ba15217b8c9d6d03c842ad427b005128188dd7a8e43edf6139a9f1db2cab5bd`
- 解包扫描：`<USER>`/主机名/`<HOME>`/`sk-[A-Za-z0-9]{18,}`/`DEEPSEEK_API_KEY (redacted) 均 0；
  `node_modules`/`*.log`/`*.sqlite*`/`.env*` 均无。

### 6.4 安装与 `rig --version`

```bash
npm install -g --prefix /tmp/openrig-install --offline \
  ./artifacts/openrig-local-cli-0.1.4.tgz
# added 115 packages in 7s
/tmp/openrig-install/bin/rig --version
# openrig-local 0.1.4
/tmp/openrig-install/bin/rig --help | head
# Usage: rig [options] [command]
```

说明：npm 11 会提示 `install-scripts ... not yet covered by allowScripts`，只是跳过 postinstall 的
Node/SQLite 自检；加 `--allow-scripts=@openrig-local/cli` 或手动跑 `check-abi.mjs` 即可。
`README-SHARE.md` 已写明。

## 7. 打包命令（可复现）

```bash
SRC=<OPENRIG_SRC>
DEST=<WORKSPACE>/dist/openrig-local-0.1.4-share-20261025

# 1) 只导出 tracked 文件（自动排除 node_modules/var/.evidence/dist 等未跟踪物）
mkdir -p "$DEST"
git -C "$SRC" archive --format=tar HEAD | tar -x -C "$DEST"

# 2) 删除排除项
rm -rf "$DEST"/AGENTS.md "$DEST"/var "$DEST"/.agents "$DEST"/.claude "$DEST"/.codegraph

# 3) 脱敏（9 个 tracked 文件）+ 放入 workflow/、README-SHARE.md、artifacts/*.tgz
#    具体改动见 §4.2；workflow 来源见 §5.1

# 4) 打包（owner/group 归一，避免 tar 头带本机用户名）
cd <WORKSPACE>/dist
tar --owner=0 --group=0 --numeric-owner -czf openrig-local-0.1.4-share-20261025.tar.gz \
    openrig-local-0.1.4-share-20261025
```

构建 tarball 的可复现步骤：把 `$DEST` 复制到构建目录 → 硬链接/安装 `node_modules`（含各 workspace）→
`npm run build && npm run build:package` → `cd packages/cli && npm pack --pack-destination ../../artifacts`。

## 8. 自检结果

对**最终 tar 解包后的目录**执行（不是只看源目录）：

```text
$ grep -rInE '<USER>|<HOST>|sk-[A-Za-z0-9]{18,}|DEEPSEEK_API_KEY\s*=|<HOME>' .
（0 行；grep_lines=0）

$ find . -name node_modules -o -name '*.log' -o -name '*.sqlite*' -o -name '.env*'
（空；find_lines=0）

$ grep -rInE '<USER>|<HOST>|sk-[A-Za-z0-9]{18,}|DEEPSEEK_API_KEY\s*=|<HOME>' workflow/
（0 行；workflow_grep_lines=0）
```

附加检查：

- `find . \( -name .git -o -name runs -o -name var -o -name node_modules \)` → 空。
- `find . -type l ! -exec test -e {} \; -print` → 空（5 个符号链接均指向包内）。
- `tar -tvzf … | awk '{print $2}' | sort -u` → `0/0`（tar 头不带本机用户名）。
- 包内文件数 3830、目录 467、符号链接 5；`du -sb` = 48,729,927。
- 源仓库 `git status --porcelain` = 0；源 `node_modules` 构建前后 mtime 变更文件数 = 0。

## 9. 已知限制 / 未打包项

- **无历史**：压缩包不含 `.git`；要历史请用源仓库单独 `git bundle`。
- **文档里的内部 run-id**：`CHANGELOG.md`、`docs/releases/v0.1.*`、`docs/reference/fork-and-upstream.md`
  等保留了 `runs/openrig-rNN-*/reports/` 这样的**文字标签**，作为“上游取舍/验证证据”的出处；
  对应的 run 数据没有进包。它们是内部项目名，不含本机路径或个人信息。
- **测试里的短 `sk-` fixture**：如 `<REDACTED_TOKEN>`、`sk-test-…` 仍存在于测试中，
  它们是明显假的、且不匹配 `sk-[A-Za-z0-9]{18,}`；未匹配要求的扫描模式。没有真实凭据。
- **`npm test` 需要 git**：`test:repo` 的 docs guard 用 `git ls-files`，无 `.git` 会失败；
  README-SHARE 已写明先 `git init` 或只跑 `npm run test:workspaces` / 单文件 vitest。
- **`@openrig-local/cli` 未发布到 npm registry**：只能从 `artifacts/` 的 tarball 或 `npm link` 安装。
- **上游跟进范围**：只吸收到 v0.7.0 级 P0/P1 + 若干安全 backport；0.7.0 之后的 upstream 没有自动合并，
  P2–P4（cgroup 级 CPU/内存限制等）未实现。
- **环境相关测试**：`packages/test-system/ci`、`docker/testbed/*` 需要 Docker；macOS 进程探测、
  真实 tmux server、headless Chrome 类测试在无相应环境的机器上会跳过或失败。本次只跑了受影响包的
  定向测试，没有跑全量 `npm test`。
- **构建戳**：分享包构建出的版本没有 commit 戳（`openrig-local 0.1.4`）；这是无 `.git` 时的预期行为，
  不是构建错误。
- **许可证**：实际是 Apache-2.0（任务文本里的 MIT 与仓库不符）；已按仓库原文保留。

## 10. 结论与试装建议

包已可分享：源码、文档、构建说明、workflow 机制、可安装 tarball 齐备；5 条要求的脱敏扫描 0 命中，
排除项扫描为空，tar 头不带本机身份。

建议接收方按这个顺序试：

```bash
tar -xzf openrig-local-0.1.4-share-20261025.tar.gz
cd openrig-local-0.1.4-share-20261025
npm install -g ./artifacts/openrig-local-cli-0.1.4.tgz
rig --version                 # openrig-local 0.1.4
read README-SHARE.md          # 构建/开关/限制
# 需要从源码构建时：
npm ci && npm run build && npm run build:package
# 想跑长任务工作流时：
sed -i 's/<YOUR_PROJECT>/\/path\/to\/your\/repo/' workflow/plan.json   # 先改占位符
python3 workflow/loop_supervisor.py --init && python3 workflow/loop_supervisor.py --dry-run
```
