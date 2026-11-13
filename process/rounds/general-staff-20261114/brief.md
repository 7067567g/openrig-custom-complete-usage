# SOLO-20261114-09 · 总参谋部与思考类单独轮索引

- 类型：单独轮（STANDALONE）
- 别名：离散轮 / 零散轮
- 主策略：GOVERN + ANALYZE
- Anchor：R15；Rejoin：R16
- 目标：建立总参谋部（头脑风暴中心）第一版；把旧 SOLO 中“思考类”轮次索引化并赋独特 ID；
  不移动/重命名原目录；建立规范考评表和第一轮全量评估。

## 总参谋部定位

- 总参谋部是**思考类任务**的索引、评估、人才选拔和维度复用中心；
- 以单轮 OpenRig 为主；
- 不替代分支/正式轮/命令中心：命令中心登记长运行轮主支，参谋部登记思考类单独轮；
- 不移动旧内容，只在原目录加/镜像 `staff-thinking` 标戳并建立索引。

## 需要索引的旧 SOLO

从 `reports/rounds/STANDALONE-ROUNDS.json` 读取全部 13 条（SOLO-20261026-01、
SOLO-20261113-01..04、SOLO-20261114-01..08）。分类为：

- `primary`：主要工作是思考/分析/设计/治理方案；
- `secondary`：有思考成分但主要交付是运维/实现/审计；
- `none`：纯操作/执行，不纳入思考索引。

## 独特 ID 与标戳

- 思考 ID 格式：`THINK-20261114-NN`
- 在索引中绑定 `sourceSoloId` / `sourcePath` / `thinkingId`
- 在每个入选源目录写 `.staff-thinking.json`（机器标戳；不移动目录）
- 若工作区权限不允许，写 mirror 到 `reports/general-staff/stamps/<THINK-ID>/.staff-thinking.json`，后续宿主复制
- 不修改/删除原 `.solo-round.json`

## 考评表

建立标准模板，至少包含维度（1–5 分）：

- problemFraming
- breadth
- depth
- alternatives
- evidence
- riskEdgeCases
- decisionQuality
- reproducibility
- executionClosure
- transferability

以及：strengths / blindSpots / reusableIdeas / talentCandidate / evidenceRefs / evaluator / notes。
输出总分、等级、是否人才候选。

## 输出

- `docs/general-staff/GENERAL-STAFF.md`
- `reports/general-staff/THINKING-ROUNDS.json` / `.md`
- `reports/general-staff/ROUND-EVALUATION-TEMPLATE.json`
- `reports/general-staff/ROUND-EVALUATIONS.json` / `.md`
- `reports/general-staff/stamps/**`（mirror fallback）
- 更新 `STANDALONE-ROUNDS.json` 的 staffThinkingId/staffClass（不删原字段）

## 约束

- 不移动/重命名源目录；不改产品代码；不读原始截图/聊天正文/token；
- 只写参谋部索引/标戳/考评/报告；不选最终人才结论（下一轮做维度与人才分析）。
