# DOCS-MAP — OpenRig 使用 / 运维仓入口

> **这是使用面的本地地图（`openrig-custom-complete-usage`）。**
> 跨仓总图由团队内部 KB 维护（私有，不随本仓发布）；源码开发文档在独立的源码线仓，同样不随本仓发布。
> 更新时间：2026-11-15

## 0. 一句话边界

**本仓是 sanitized 的使用/运维示例，不是源码事实，也不是产品手册。**
源码行为以 OpenRig 源码线为准；控制面决策由团队内部工作流组维护（均不随本仓发布）。

## 1. 先确定你在做哪类事

| 你在做什么 | 读这个 | 不要从这里开始 |
| --- | --- | --- |
| 第一次上手 OpenRig | [`README.md`](README.md) → [`docs/QUICKSTART.md`](docs/QUICKSTART.md) | `process/` |
| 全量文档索引 | [`docs/INDEX.md`](docs/INDEX.md) | 自己 `ls docs/` |
| 接入项目 / 多轮编排 | [`docs/OPENRIG-WORKFLOW-GUIDE.md`](docs/OPENRIG-WORKFLOW-GUIDE.md) | 源码 `ARCHITECTURE.md` |
| 排查 LLM 误读 | [`docs/LLM-MISREAD-QUICKREF.md`](docs/LLM-MISREAD-QUICKREF.md) | `process/STORY.md` |
| 内存/安全边界 | [`docs/MEMORY-SAFETY.md`](docs/MEMORY-SAFETY.md) | 示例代码 |
| 看一次实践怎么长出来的 | [`process/README.md`](process/README.md)（**档案，非手册**） | 把档案当现行规范 |
| 看两条近期案例 | [`docs/cases/04`](docs/cases/04-multi-repo-docs-governance.md)、[`05`](docs/cases/05-openrig-rework-loops.md) | 只读 `process/STORY.md` |
| 看想法与下一步 | [`process/ideas/2026-11-openrig-ideas.md`](process/ideas/2026-11-openrig-ideas.md) | 把想法当路线图承诺 |
| 跑可复制的例子 | [`examples/`](examples/) | `docs/` 的叙述 |
| 发布/版本口径 | [`docs/VERSIONING.md`](docs/VERSIONING.md) | 根 `README.md` |
| 验证/复现状态 | [`VALIDATION.md`](VALIDATION.md) | `reports/` |

## 2. 目录分工

| 目录 | 是什么 | 权威性 |
| --- | --- | --- |
| `docs/` | 使用文档（29 篇，中英配对） | 使用面权威；`docs/INDEX.md` 受 `make doc` 覆盖检查 |
| `process/` | sanitized 过程档案（50 篇：STORY/DECISIONS/评审记录） | **档案**，解释"为什么这样做"，不是规范 |
| `examples/` | 可运行示例（90 篇） | 示例，不是契约 |
| `roles/` | MAIN/PMO/TDO/QA/SAFETY 契约 | 与 KB `workflow-group/roles/` 同源，冲突以 KB 为准 |
| `templates/` | 四层模板副本 | 实例化用；母版正文在 KB `templates/specialized/openrig-workflow-master/` |
| `tools/` | `lead-guide` 等工具 | 工具文档 |
| `reports/` | 审计/分析报告 | 历史记录，非规范 |
| `sctg-kit/` | SCTG 参考实现 | 稳定 kit 以 `SCTG-public` 为准 |

## 3. 不要从这里开始

- ❌ 把本仓 `docs/ARCHITECTURE.md` 当源码架构 —— 它是示例仓的叙述版本。
- ❌ 把 `process/` 当产品手册 —— 目录自述 "not a product manual"。
- ❌ 把 `templates/` 副本当母版权威 —— 母版在 KB `workflow-group/templates/specialized/openrig-workflow-master/`。
- ❌ 把 `roles/` 当最终契约 —— 冲突时以 KB `roles/` 与 `WORKFLOW.md` 为准。

## 4. 改文档必跑

```bash
make doc    # scripts/doc_consistency.py --check：索引覆盖 + 中英配对 + 脚本路径 + 机制事实
```

- 改 `docs/INDEX.md` 必须**同步**对应 `*.zh-CN.md`，否则 `make doc` 失败；
- 新增 `docs/*.md` 必须进 INDEX 且有中英配对，否则失败；
- 记录**无管道退出码**：`make doc > /tmp/out 2>&1; echo $?`。

## 5. 跨仓

- 跨仓总图：团队内部 KB 的 `docs/openrig/README.md`（私有，不随本仓发布）
- 源码开发面：独立的源码线仓（私有，不随本仓发布）
- 控制面入口：团队内部工作流组（私有，不随本仓发布）

## 6. 本页数字的复跑命令

> 在本仓根目录执行。命令放在围栏块里：表格单元格中的 `|` 会被 GFM 切成列。

```bash
# 29 篇 docs/*.md
ls docs/*.md | wc -l

# 50 篇 process/
find process -name '*.md' | wc -l

# 90 篇 examples/
find examples -name '*.md' | wc -l
```
