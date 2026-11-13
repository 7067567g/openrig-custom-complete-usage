# SYNC-GUARD · 多文件夹一致性与同步门禁

- 日期：2026-11-14
- 路径基准：下表路径相对 `<WORKSPACE>`；`bridge-app` 使用稳定绝对路径（external）。
- 范围：`bridge repo` 及其相邻目录的 source-of-truth、只读快照、外部仓、生成物与无关备份。
- 性质：治理/检查规则草案；**本轮不改产品代码、不改分支、不写同步脚本**。
- 配套：`reports/branches/SYNC-MANIFEST.json`（机器可读清单）
- 输入：`discussions/sync-guard-20261114/BRIEF.md`、`docs/BRANCHING-PROTOCOL.md`、`docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`、`reports/branches/BRANCH-LEDGER.json`、`reports/issues/*`、`docs/branches/REFERENCE-INDEX.md`

## 0. 结论摘要

| 目录 | 角色 | 可编辑 | 同步策略 |
|---|---|---|---|
| `bridge repo` | **source-of-truth**（Web/Node 主仓） | 是（走分支/卡） | 必须与分支台账/文档一致；合并前工作树可 dirty，但必须申报 |
| `bridge-app` | **external**（原生 Android） | 仅独立 Android 工作区 | 不与 Web 仓库同步；只检查存在/版本/独立分支 |
| `governance-20261110/staging/bridge repo` | **read-only old staging** | 否 | 不参与同步；不得当主线 |
| `governance-20261110/snapshots/**` | **read-only historical snapshots** | 否 | 只校验存在/哈希；不得编辑 |
| `dist/v3 workspace-share-20261025` | **generated distribution** | 否（重新生成） | 允许与 live 差异；不得手改 |
| `the assistant project-备用/**`、`qq-bridge*`、`_migration-backup-*` | **unrelated backups** | 否 | 不同步、不比较、不引用 |
| `discussions/**` | **read-only input** | 否 | 作为 source；不反向覆盖仓库 |
| `reports/**`、`docs/**`（repo 内） | **governance artifacts** | 是（按卡） | 与 ledger/branch docs 双向一致 |

**当前观测**（2026-11-14，见 §6）：`remediation/20261113`、`feat/r15-ux6`、`feat/quiet-200` 三个分支都停在 `280de35`，当前 checkout 是 `feat/quiet-200`，工作树有 77 个 dirty 文件；`dist` 是 3.0.0、live 是 3.2.2；`bridge-app` 0.2.1；staging 是旧副本但版本号同为 3.2.2。**没有发现可自动判定的致命漂移，但“分支无独有 commit + dirty 工作树”必须作为合并前阻断/申报项。**

---

## 1. 多文件夹职责

### 1.1 Source-of-truth

- **`bridge repo`** 是 Web/Node 产品、文档、测试、分支台账的唯一 source-of-truth。
- 分支元数据以 `reports/branches/BRANCH-LEDGER.json` 为机器可读真值；人类可读解释在 `docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`。
- 代码/测试/文档的变更走分支 + 卡；不直接改 staging/snapshot/dist。

### 1.2 外部仓

- `bridge-app` 是独立 Android WebView 壳，不属于 `bridge repo` git；I3 只能在该仓的独立工作区/轮次做。
- 允许与 Web 仓版本不同（当前 `bridge-app 0.2.1`、web `3.2.2`）；不要求文件一致。
- 只检查：目录存在、`applicationId=com.example.bridge`、`versionName` 与发布记录一致、独立分支/tag 可追溯。

### 1.3 只读历史快照

- `governance-20261110/snapshots/**` 是 2026-11-10 治理轮的基线/应用前快照；用于回滚/证据，不是当前代码。
- 只允许读/校验哈希；禁止编辑、禁止 `git checkout` 到快照、禁止把快照内容复制回 live 作为“同步”。
- 基线清单：`governance-20261110/evidence/ws0/SNAPSHOT-pre.sha256`、`BASELINE-pre.sha256`；应用前快照清单：`governance-20261110/snapshots/apply-pre-20261110-015441/SNAPSHOT.sha256`。

### 1.4 旧 staging

- `governance-20261110/staging/bridge repo` 是 2026-11-10 治理轮的 staging 副本；`governance-20261110/STATE.md` 明确 live 是 `<HOME>/bridge repo`，staging 只是副本。
- 版本号可能相同（当前 3.2.2），但代码可能落后；**版本号相同不等于内容一致**。
- 禁止把 staging 当主线或“同步源”；只能作为历史证据/只读对照。

### 1.5 生成分发包

- `dist/v3 workspace-share-20261025` 是 2026-10-25 生成的分享包（当前 3.0.0），不是 live 源。
- 禁止手改；需要更新时从 tagged live 重新生成，并记录生成命令/版本/哈希。
- 允许与 live 差异（版本/文件集/依赖），但必须在发布记录中说明。

### 1.6 无关备份

- `the assistant project-备用/**`、`qq-bridge`、`qq-bridge.新版恢复-*`、`qq-bridge.旧版备份-*`、`_migration-backup-*` 是历史/其他项目备份。
- 不同步、不比较、不作为引用；只允许人工归档/删除，且需独立授权。

### 1.7 讨论输入

- `discussions/**` 是 Brief/任务输入，read-only；可以引用其路径作为 source，但不能把讨论稿当产品真值，也不能用讨论稿覆盖仓库文档。

---

## 2. 必须一致 / 允许差异 / 禁止手改

### 2.1 必须一致（must-match）

| # | 对象 A | 对象 B | 一致项 |
|---|---|---|---|
| M1 | `reports/branches/BRANCH-LEDGER.json` | `docs/branches/UX6-R15.md` | code=`UX6-R15`、branch=`feat/r15-ux6`、base_commit、status、scope、anchor=R15/rejoin=R16 |
| M2 | `reports/branches/BRANCH-LEDGER.json` | `docs/branches/QUIET-200.md` | code=`QUIET-200`、branch=`feat/quiet-200`、parent_code=`UX6-R15`、parent_round=`UX6-R15-02`、base_commit、status、scope |
| M3 | `reports/branches/BRANCH-LEDGER.json` | git | 分支存在；`base_commit` 是分支祖先（`merge-base --is-ancestor`），不要求 head==base |
| M4 | `docs/BRANCHING-PROTOCOL.md` | ledger | 主链锚点 `R15`、回归点 `R16`、active_branch=`remediation/20261113`、final=`main` |
| M5 | `docs/branches/REFERENCE-INDEX.md` | repo | 列出的仓库相对路径存在；planned 项明确标 `planned` |
| M6 | `reports/issues/QUIET-200-FOLLOWUP.md` | `reports/issues/QUIET-200-IMPLEMENTATION-PLAN.json` | 9 个问题 ID/数量一致（Q1–Q9 ↔ `openQuestions`） |
| M7 | `reports/issues/SIX-ISSUES-INTAKE-20261113.md` | `docs/branches/UX6-R15.md` | I1–I6 ↔ `UX6-R15-01..06`；I3 标 external/Android |
| M8 | `reports/branches/SYNC-MANIFEST.json` | 本文件 | 目录角色/`mustMatch`/`allowDiff`/`forbidden`/`checks` 的 policy 一致 |

### 2.2 允许差异（allow-diff）

| 对象 | 允许差异 | 原因 |
|---|---|---|
| staging vs live | 代码/文件/时间可不同 | staging 是旧副本，非源 |
| snapshots vs live | 全部可不同 | 历史快照 |
| dist vs live | 版本/文件集可不同 | 生成物（当前 3.0.0 vs 3.2.2） |
| bridge-app vs web | 代码/版本/构建可不同 | 不同栈/独立仓 |
| backups/qq vs live | 全部可不同 | 无关项目/历史 |
| discussions vs repo docs | 讨论稿可更新/更细 | 输入，不是真值 |
| 分支 head vs base_commit | head 可前进 | base 是分叉点，不是当前 head |
| 工作树 vs HEAD | 可 dirty | 实现中允许，但合并前必须申报/清理 |
| 生成报告时间/哈希 | 可不同 | 每次运行产生新证据 |

### 2.3 禁止手改（forbidden）

- 禁止把 `governance-20261110/staging/**`、`snapshots/**`、`dist/**`、`the assistant project-备用/**`、`qq-bridge*` 作为可编辑主线。
- 禁止在 `docs/branches`/`reports/branches`/`reports/issues` 引用临时目录原始截图、聊天正文、token、`Authorization`、带 token URL、`data:`/blob。
- 禁止无 ledger/doc 同步地修改 `base_commit`/`branched_at`/`status`/`scope`。
- 禁止把 QUIET-200 实现直接 cherry-pick 到 `main` 绕过 `remediation/20261113` 与 R16。
- 禁止手改 `SYNC-MANIFEST.json` 的 `observed` 段当“新事实”；observed 是检查输出，policy 才是手写区。
- 禁止删除/放宽测试断言来让同步门变绿。

---

## 3. 引用链接检查规则

1. **路径形式**：仓库相对路径（如 `docs/branches/QUIET-200.md`）或稳定绝对路径（仅 `bridge-app` 等 external）。不使用临时目录、`file://`、相对 `../` 出仓路径（external 除外）。
2. **存在性**：`REFERENCE-INDEX.md` 中 role 非 `planned` 的路径必须存在；planned 必须标 `planned` 且不得当 evidence。
3. **锚点/文件名**：链接到章节时使用稳定标题（如 `§9`/标题文本）；文件名大小写与仓库一致。
4. **禁止内容**：不引用原始截图、聊天正文、token、日志正文、媒体二进制；只引用问题编号/代码位置/报告路径。
5. **角色**：每个引用必须有 `source/summary/evidence/decision/index/planned` 之一；没有角色的链接视为无效。
6. **单一真值**：branch 元数据只引 `BRANCH-LEDGER.json`；9 个决策只引 `QUIET-200-FOLLOWUP.md`；I1–I6 只引 `SIX-ISSUES-INTAKE-*`；U2a/U2b 只引 `QUIET-200-IMPLEMENTATION-PLAN.*`。

---

## 4. Git 分支/台账/文档一致性

| 检查 | 规则 |
|---|---|
| G1 分支存在 | `feat/r15-ux6`、`feat/quiet-200`、`remediation/20261113`、`main` 必须存在 |
| G2 base 祖先 | `git merge-base --is-ancestor <base_commit> <branch>` 为真；不要求 head==base |
| G3 anchor/rejoin | ledger `mainline.anchor_round=R15`、`rejoin_round=R16`；branch docs 同值 |
| G4 parent/child | QUIET `parent_code=UX6-R15`、`parent_round=UX6-R15-02`；UX6 的 `external_children` 含 `ANDROID-UX6-R15-06/I3` |
| G5 status/scope | ledger 与 branch docs 的 status/scope 一致；scope 不能偷偷扩到 `bridge-app` |
| G6 工作树 | 合并前 `git status --porcelain` 为空或已申报；dirty 只允许在实现中，不允许静默合并 |
| G7 独有 commit | 分支进入 QA 前应有相对 base 的独有 commit；当前三分支同 commit 视为“未开工/未提交”warn |
| G8 tag/合并 | 合并前有 `UX6-R15-done-*`/`quiet-200-done-*` tag 计划；合并不跳过 R16 |

---

## 5. 可复制检查命令/CI 门禁草案

> 以下命令在 `bridge repo` 根执行；只读，不修改仓库。

### 5.1 JSON/路径

```bash
set -u
cd <BRIDGE_REPO>

python3 -m json.tool reports/branches/BRANCH-LEDGER.json >/dev/null
python3 -m json.tool reports/branches/SYNC-MANIFEST.json >/dev/null

for f in \
  docs/BRANCHING-PROTOCOL.md \
  docs/branches/UX6-R15.md \
  docs/branches/QUIET-200.md \
  reports/branches/BRANCH-LEDGER.json \
  reports/branches/SYNC-GUARD.md \
  reports/branches/SYNC-MANIFEST.json \
  reports/issues/SIX-ISSUES-INTAKE-20261113.md \
  reports/issues/SIX-ISSUES-INTAKE-20261113.json \
  reports/issues/QUIET-200-IMPLEMENTATION-PLAN.md \
  reports/issues/QUIET-200-IMPLEMENTATION-PLAN.json \
  reports/issues/QUIET-200-FOLLOWUP.md \
  docs/branches/REFERENCE-INDEX.md; do
  test -f "$f" || echo "MISSING $f"
done
```

### 5.2 Git/ledger 一致性

```bash
python3 - <<'PY'
import json, subprocess, sys
ledger = json.load(open('reports/branches/BRANCH-LEDGER.json', encoding='utf-8'))
errors = []
for b in ledger.get('branches', []):
    branch = b.get('branch', '')
    if not branch or branch == 'TBD':
        continue
    if subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}']).returncode != 0:
        errors.append(f'missing branch: {branch}')
        continue
    base = b.get('base_commit', '')
    if base.startswith('bridge-app'):
        continue
    if subprocess.run(['git', 'merge-base', '--is-ancestor', base, branch]).returncode != 0:
        errors.append(f'base {base[:12]} not ancestor of {branch}')
print('GIT-LEDGER:', 'OK' if not errors else 'FAIL')
for e in errors: print(' -', e)
sys.exit(1 if errors else 0)
PY
```

### 5.3 ledger/doc 字段对比

```bash
python3 - <<'PY'
import json, re, sys
ledger = json.load(open('reports/branches/BRANCH-LEDGER.json', encoding='utf-8'))
by_code = {b['code']: b for b in ledger['branches']}
errors = []

def doc(path):
    return open(path, encoding='utf-8').read()

u = doc('docs/branches/UX6-R15.md')
q = doc('docs/branches/QUIET-200.md')

checks = [
    ('UX6-R15', 'feat/r15-ux6', u),
    ('QUIET-200', 'feat/quiet-200', q),
]
for code, branch, text in checks:
    b = by_code.get(code)
    if not b:
        errors.append(f'ledger missing {code}'); continue
    if f'`{branch}`' not in text:
        errors.append(f'{code} doc missing branch {branch}')
    if b['base_commit'][:7] not in text:
        errors.append(f'{code} doc missing base {b["base_commit"][:7]}')
    if f'`{b["status"]}`' not in text and b['status'] not in text:
        errors.append(f'{code} doc/status mismatch ({b["status"]})')

if 'R15' not in ledger['mainline']['anchor_round'] or 'R16' not in ledger['mainline']['rejoin_round']:
    errors.append('anchor/rejoin mismatch')
print('LEDGER-DOC:', 'OK' if not errors else 'FAIL')
for e in errors: print(' -', e)
sys.exit(1 if errors else 0)
PY
```

### 5.4 禁止引用/工作树

```bash
# 只做提示；命中需人工复核（规则文本本身可能包含关键词）
rg -n "Screenshot_|/tmp/|Authorization:|token=|data:image|base64" docs/branches reports/branches reports/issues || true

# dirty 工作树必须申报；合并前应为空
if [ -n "$(git status --porcelain)" ]; then
  echo "WORKTREE: DIRTY ($(git status --porcelain | wc -l) files) — require declaration before merge"
fi

# 分支当前状态
git branch --show-current
git rev-parse --short HEAD
```

### 5.5 只读快照/分发包

```bash
# 快照基线哈希（历史清单；以清单实际相对路径为准）
( cd governance-20261110/snapshots/pre-20261110 && sha256sum -c ../../evidence/ws0/SNAPSHOT-pre.sha256 ) || true

# 只允许读：检查 staging/snapshot/dist 是否被 git 跟踪（应为 no-git / not in repo）
for d in governance-20261110/staging/bridge repo governance-20261110/snapshots dist/v3 workspace-share-20261025; do
  test -d "$d/.git" && echo "UNEXPECTED GIT: $d" || echo "read-only/no-git: $d"
done
```

**CI 建议**：把 5.1–5.4 作为 `sync-guard` job；5.5 作为 nightly/周检查（哈希较重）。任何 FAIL 阻断合并；WARN 需在 PR/报告中说明。

---

## 6. 当前观测（2026-11-14）

| 项 | 观测 | 判断 |
|---|---|---|
| 当前分支 | `feat/quiet-200` | 已建，符合 ledger |
| 分支 head | `remediation/20261113`=280de35、`feat/r15-ux6`=280de35、`feat/quiet-200`=280de35 | 三分支同 commit；无独有 commit |
| 工作树 | 77 个 dirty 文件（含 sim/app.js、styles.css、local-io.mjs、monitor 等） | 实现中 dirty；合并前必须处理/申报 |
| 主链 | `main`=54b23dc | 不参与支线合并 |
| anchor/rejoin | R15/R16 | 与 protocol/ledger 一致 |
| live 版本 | 3.2.2 | source-of-truth |
| staging 版本 | 3.2.2 | 版本相同但旧副本；不可当源 |
| dist 版本 | 3.0.0 | 生成物；允许差异 |
| bridge-app | 0.2.1，独立目录 | external；允许差异 |
| 引用索引 | `docs/branches/REFERENCE-INDEX.md` 已存在 | s1 产物 |
| s2 产物 | `SYNC-GUARD.md`/`SYNC-MANIFEST.json` | 本文件/配套 JSON；`REFERENCE-INDEX.md` 已回填为 actual（s2 同轮更新） |

**未执行/未验证**：

- 已跑只读快照 `sha256sum -c`：`governance-20261110/snapshots/pre-20261110` 对 `SNAPSHOT-pre.sha256` 全部 OK（1002 文件）；nightly 继续复跑。
- 未构建/安装 `bridge-app` APK；未做 Android 真机。
- 未改任何产品代码/分支/snapshot/staging/dist。
- 未把 s1/followup 的 9 个默认值当成 MAIN 已拍板；Q1/Q2/Q3/Q4/Q7/Q9 仍需 MAIN 确认。

---

## 7. 漂移处理 SOP

1. **发现**：CI/nightly/人工按 §5 报 FAIL/WARN；记录命令、输出、时间、当前 branch/HEAD。
2. **分类**：
   - source-of-truth 仓库漂移（ledger/doc/git 不一致）→ 进入 3；
   - staging/snapshot 被修改 → 进入 4；
   - dist 与 live 差异 → 进入 5；
   - bridge-app 差异 → 进入 6；
   - 备份/qq 差异 → 忽略（除非误引用）。
3. **仓库漂移**：先确认哪边是主源（ledger/MAIN 决策），再：
   - 更新 ledger + branch doc + reference index（同一提交）；
   - 或 `git revert`/回滚错误 commit；
   - 重跑 §5.1–5.4；不允许只改一边。
4. **staging/snapshot 被修改**：立即停止使用该副本；从 `SNAPSHOT-pre.sha256`/`SNAPSHOT.sha256` 校验并恢复；记录事故；不得把修改后的副本当证据。
5. **dist 漂移**：确认 tag/版本；从 tagged live 重新生成，记录命令/哈希；不手改 dist。
6. **bridge-app 漂移**：转到独立 Android 工作区；按 Android 支线流程处理；Web 仓只更新引用/状态，不复制原生代码。
7. **记录**：在 `reports/branches/BRANCH-LEDGER.json` 的 `updatedAt`/branch status、`reports/branches/SYNC-GUARD.md` 观测段、`docs/branches/REFERENCE-INDEX.md` 变更记录中留痕。
8. **回滚**：合并前丢弃分支；合并后 `git revert -m 1 <merge-commit>`；缓存 schema 版本化，旧缓存忽略/清理；快照用 `governance-20261110/rollback/rollback-to-pre.sh`（只读参考，不在本轮执行）。

---

## 8. 本轮不做什么

- 不实现 `sync-guard` 脚本/CI job（只给命令草案）。
- 不修改 `BRANCH-LEDGER.json`、branch docs、产品代码、分支、staging/snapshot/dist。
- 不替 MAIN 决定 Q1–Q9；只引用 `QUIET-200-FOLLOWUP.md` 的推荐值。
- 不构建/安装 bridge-app、不跑真机。
- 不提交原始截图、聊天正文、token、日志正文。
- 不把 staging/snapshot 当源，不把 dist 当 live。

## 9. 引用

- `docs/branches/REFERENCE-INDEX.md`
- `reports/issues/QUIET-200-FOLLOWUP.md`
- `docs/BRANCHING-PROTOCOL.md`
- `docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`
- `reports/branches/BRANCH-LEDGER.json`
- `reports/issues/SIX-ISSUES-INTAKE-20261113.md` / `.json`
- `reports/issues/QUIET-200-IMPLEMENTATION-PLAN.md` / `.json`
- `governance-20261110/STATE.md`、`governance-20261110/DONE`（只读历史证据）
- `discussions/sync-guard-20261114/BRIEF.md`（输入）
