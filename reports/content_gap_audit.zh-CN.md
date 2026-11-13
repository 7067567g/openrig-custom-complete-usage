# 内容缺口审计 — 2026-11-13

范围：对比已发布仓库与本地完整用法（`workflow-group` + `openrig-workflow-master`
+ SCTG-public），列出缺失、委托或有意排除的内容。

## 已上传

- 中英双语的 README、quickstart、architecture、multi-round、OpenRig、
  publishing、versioning、environment、reproducibility、limitations、
  validation、cases、reference、concepts、benchmark、examples 和 validation 文档。
- 可运行的 SCTG 示例：`minimal`、`multi-card`、`decision`、`rollback`、
  `two-seat-handoff`。
- 脱敏控制面样例（`examples/sanitized-run/`）。
- 脱敏后的 OpenRig 生成 bundle 和证据样例。
- 一次**真实单步 OpenRig workflow run** 的 `rig ps`、workflow state、trace
  证据（`examples/live-run/`）。
- benchmark 机制 harness + 合成 task pack + 冒烟结果（`benchmark/`）；还不是
  模型 benchmark。
- 三个完整、合成但真实的 12 轮 workflow-group 案例（`examples/round-cases/`）。
- CI、仓库卫生、内容审计、脱敏门禁、release notes、tag、GitHub release。

## 仍缺失 / 有意拆分

### P0 — 完整模型 benchmark harness 和结果

机制 harness 已有，但完整 raw-vs-SCTG 模型 harness 和真实模型结果仍缺失：

- 模型 arm / launcher
- local judge、oracle/generator 示例、sandbox/preflight audit
- 真实 raw-vs-SCTG 结果

### P1 — 5-seat live OpenRig 证据

`examples/live-run/` 证明真实单步 OpenRig workflow 和 packet 交接。仍缺：
脱敏 5-seat hybrid run 的 `rig ps --nodes`、transcripts、archive manifest、
close/teardown 证据。

### P1 — 多轮深度

现在有三个 12 轮合成案例。仍缺：真实项目、10 轮以上、带模型产物的案例研究。

### P2 — SCTG 核心参考文档

protocol、ledger、decision model、mode policy、security model、glossary、FAQ、
performance、provenance、status 保留在 `SCTG-public`，通过
`docs/REFERENCE.zh-CN.md` / `docs/CONCEPTS.zh-CN.md` 链接；有意不重复。

### P2 — 案例

只有一篇冒烟案例（`docs/cases/01-render-smoke.zh-CN.md`）。缺真实多轮案例。

### P2 — 专用模板

只包含 `openrig-workflow-master`。领域专用模板有意不公开。

### P2 — 内部资产

- `burner/` 队列和计费自动化：有意排除。
- archive/teardown/link-check 工具：有引用，未包含。
- 截图和视觉资产：没有；使用 ASCII 图。

### P3 — 双语覆盖

已覆盖 19 对中英文文档。仍为英文的：`SECURITY.md`、`CONTRIBUTING.md`、
`CODE_OF_CONDUCT.md`、`THIRD_PARTY_NOTICES.md`、`AGENTS.md`、
`CHANGELOG.md` 和 release notes。

### P3 — 打包

`pyproject.toml` 只是元数据；仓库不是 pip 可安装包。它是使用例仓库，不是库分发。

## 脱敏状态

- `.agents/` seat 产物已删除并 gitignore。
- `scripts/check_sanitization.py` 在 CI 中检查作者路径、凭证、私钥。
- `templates/ISSUES.xlsx` 元数据已检查：中性（`creator=openpyxl`）。
- 公开 git history 在 v0.1.4 以干净单提交发布。

## 建议下一步

1. 补完整模型 benchmark harness 和真实结果（P0）。
2. 捕获一次脱敏 5-seat OpenRig run（P1）。
3. 给脱敏多轮样例补 Round 2/3（P1）。
4. 有真实案例后补一篇 case study（P2）。
5. 如需，补治理文件的中文版（P3）。
