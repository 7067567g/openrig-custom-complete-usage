# 总参谋部 · 第一轮思考类轮次评估

- 日期：2026-11-14
- 版本：`v1.0.1`
- 模板：`reports/general-staff/ROUND-EVALUATION-TEMPLATE.json`（10 维，1–5，总分 10–50）
- 机器可读：`reports/general-staff/ROUND-EVALUATIONS.json`
- 索引：`reports/general-staff/THINKING-ROUNDS.json`
- 性质：**first-pass**；不是最终人才结论，下一轮再做维度/人才分析。

## 汇总

| 项 | 数量 |
|---|---|
| 评估条目 | **13** |
| A（40–50） | **9** |
| B（32–39） | **4** |
| C/D | **0** |
| 平均分 | **42.0** |
| 人才候选（暂定） | **8** |

人才候选规则：总分 ≥40 且 evidence ≥4 且 decisionQuality ≥4；仅初评标记，不选最终人才。

## 评估表

| THINK ID | Source SOLO | Class | 总分 | 等级 | 人才候选 | 主要优势 | 主要盲点 |
|---|---|---|---:|---|---|---|---|
| `THINK-20261114-01` | `SOLO-20261026-01` | primary | **45** | A | yes | 完整模拟两对身份/三轮对话; ACCEPTANCE 6/6，明确模拟非实测 | 全部为推演，无真实用户/真机; 部分数值是目标/待校准 |
| `THINK-20261114-02` | `SOLO-20261113-01` | primary | **44** | A | no | 视觉预规划/运行时双路设计; 发送事务/身份锚点/单写者风险识别 | 多为设计/临时 live，缺独立 QA; 单写者锁/R2 身份仍未落地 |
| `THINK-20261114-03` | `SOLO-20261113-02` | primary | **42** | A | yes | 六条问题 6/6 确认、无重复; P0/P1/P2 与推荐顺序清楚 | 未做真机复现; I3 外置依赖未闭环 |
| `THINK-20261114-04` | `SOLO-20261113-03` | secondary | **37** | B | no | 固定契约+18 组件+测试; 路由/预览/报告可复跑 | 设计/实现偏重，思考广度一般; 部分预览与 schema 细节漂移 |
| `THINK-20261114-05` | `SOLO-20261113-04` | primary | **46** | A | yes | 老/新桥能力矩阵与裁决; 建议分级/不建议项清楚 | 只读分析，未做代码验证; 部分能力依赖旧库/微信语义 |
| `THINK-20261114-06` | `SOLO-20261114-01` | primary | **42** | A | yes | 目录职责/must-allow-forbid 清晰; manifest/check/SOP 可复用 | 部分命令未在 CI 跑; staging/dist 差异仍需人工确认 |
| `THINK-20261114-07` | `SOLO-20261114-02` | primary | **47** | A | yes | 停止场景/冻结/禁止动作完整; 三类分类+证据+回滚 | 沙箱无法验证宿主 systemd/PID; 部分命令是草案未执行 |
| `THINK-20261114-08` | `SOLO-20261114-03` | primary | **44** | A | yes | 六类插入/默认排队/硬中止; 记录字段/生命周期完整 | 无真实插入事件演练; INLINE_EXTEND 判定依赖 owner |
| `THINK-20261114-09` | `SOLO-20261114-04` | primary | **44** | A | yes | 单独轮定义/别名/ID/生命周期; 七策略/门禁/防漂移 | 首版 registry 需持续维护; 部分历史条目 retrospective |
| `THINK-20261114-10` | `SOLO-20261114-05` | secondary | **35** | B | no | 全量 disposition/owner/nextAction; fast-response 升级支线理由清楚 | 管理/ops 为主，思考广度有限; 分支计划 base 后有漂移 |
| `THINK-20261114-11` | `SOLO-20261114-06` | secondary | **39** | B | no | worktree/stash/diff 证据完整; B0/SNAP/B1/B2/B3 漂移定位 | 审计为主，非设计; 未读敏感文件正文 |
| `THINK-20261114-12` | `SOLO-20261114-07` | primary | **42** | A | yes | registry/CLI/冲突语义完整; validate/list/show/conflicts 可跑 | resourceKey 设计仍需演进; lastSeenAt 是快照 |
| `THINK-20261114-13` | `SOLO-20261114-08` | secondary | **39** | B | no | stamp schema/主真值/mirror fallback; CLI stamp/collect/verify/find | 12 mirror 未就地; 工具/实现为主，思考广度一般 |

## 评分口径

- 10 维各 1–5：problemFraming / breadth / depth / alternatives / evidence / riskEdgeCases / decisionQuality / reproducibility / executionClosure / transferability。
- A=40–50，B=32–39，C=24–31，D=10–23。
- 评分依据：索引中的 `sourcePath`、各轮 final/acceptance/verification 报告、registry/工具输出；未读原始截图/聊天/token。
- `evaluator=Lead/QA (first-pass)`；未做独立复核，故 `talentCandidate` 只是暂定。

## 主要发现

- 高分集中在：STOP-SWEEP（47）、compare（46）、g3d（45）、fast/insert/solo（44）。
- `fast-response` 总分 44 但 evidence=3（多为 TARGET/UNVERIFIED），不满足人才候选规则；这与 SOLO-06 的“先修 base/QA”一致。
- 低分集中在 ops/management/audit/stamp（35–39）：执行/收口强，但 breadth/depth 不是主交付。
- `monitor` 37：测试/契约强，但思考广度/风险一般。
- 8 个暂定人才候选需要下一轮独立复核，不是最终名单。

## 下一步

- 下一轮：维度索引/人才分析（不在本轮）；可对 A 级条目做独立复核。
- 不因初评改变任何 SOLO 状态/分支/合并结论。
- R16 仍 NEED_MAIN；不跳过。

## 引用

- `docs/general-staff/GENERAL-STAFF.md`
- `reports/general-staff/THINKING-ROUNDS.json` / `.md`
- `reports/general-staff/ROUND-EVALUATION-TEMPLATE.json`
- `reports/general-staff/ROUND-EVALUATIONS.json`
- `reports/rounds/STANDALONE-ROUNDS.json`
