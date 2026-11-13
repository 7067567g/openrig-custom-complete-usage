# QUIET-200 后续决策建议（SYNC-GUARD s1）

- 日期：2026-11-14
- 范围：只审阅 `QUIET-200-IMPLEMENTATION-PLAN` 的 9 个未决问题，给出可执行默认值、理由与 MAIN 拍板点。
- 输入：`discussions/sync-guard-20261114/BRIEF.md`、`docs/BRANCHING-PROTOCOL.md`、`docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`、`reports/branches/BRANCH-LEDGER.json`、`reports/issues/SIX-ISSUES-INTAKE-20261113.*`、`reports/issues/QUIET-200-IMPLEMENTATION-PLAN.*`
- 引用索引：`docs/branches/REFERENCE-INDEX.md`
- 约束：本轮不改产品代码、不建/切分支、不写实现、不提交原始截图/聊天正文。

## 0. 决策总表

| # | 问题 | 推荐默认值 | MAIN 拍板 | 影响 |
|---|---|---|---|---|
| Q1 | 分支基线：`280de35` vs 当前 remediation 工作树 | 先冻结/提交当前 remediation 工作树为新的基线 commit，再从该 commit 拉 `feat/quiet-200`；不要从 `280de35` 直接开工 | **必须** | 分支/合并冲突、R17–R20 是否保留 |
| Q2 | IndexedDB 明文缓存是否接受 | v1 接受，origin 隔离、无 token/二进制；删除/清空同步，清屏不清理；文档写明本机风险 | **必须** | 隐私/共享设备 |
| Q3 | 最近 200 条是否包含媒体 | v1 只缓存文本 + 媒体元数据；不缓存二进制；离线媒体显示“媒体需联网”占位 | **必须** | 产品承诺“可查看”的范围 |
| Q4 | 全局 2000 LRU 是否保护当前会话 200 | 保护当前会话最近 200；全局 2000 只淘汰其它会话 | **必须** | 当前会话离线可用性 |
| Q5 | 消息身份 key 优先级 | `id` > `mid` > `clientMessageId`（仅用于回声对账）> 指纹；v1 不缓存纯乐观/未确收消息 | 建议确认 | 去重/删除/迁移 |
| Q6 | 离线文案与范围提示 | 顶部“离线缓存 · 最近 200 条（仅本机）”；搜索“离线缓存：最近 200 条；更早历史需联网”；媒体“媒体需联网查看” | 建议确认 | 用户预期 |
| Q7 | 清屏是否清缓存 | 不清；只有显式删除/清空/`clear` 事件清缓存；以后可加“清除离线缓存” | **必须** | 误删离线数据 |
| Q8 | 预加载阈值 | 压力位 1.5 屏；快速触发 2.5 屏；速度 `rows/s >= 40` 或 `px/s >= 1800`（OR）；采样 400ms/5 点；冷却 400ms；spinner 350ms | 默认即可，真机调参 | 流量/等待感 |
| Q9 | U2a 是否把 `historyMessages` 上限 1000→2000 | U2a 保持 1000；U2b 用测试/内存预算评估后再决定是否提高 | **必须** | 内存/重连补齐 |

**结论**：9 条里 6 条需要 MAIN 明确拍板（Q1/Q2/Q3/Q4/Q7/Q9），Q5/Q6 建议确认，Q8 可按默认值先实现再真机调。没有需要新增产品功能的决策。

---

## 1. Q1 · 分支基线

### 推荐默认值

**先冻结/提交当前 `remediation/20261113` 工作树中与本支线相关的改动，形成新的基线 commit，再从该 commit 拉 `feat/quiet-200`。**

- 不要从 `280de35` 直接开工；`docs/branches/QUIET-200.md` 自己也写明 U2 依赖“当前工作树的历史/滚动/搜索实现”，而当前工作树的 `sim/app.js`、`sim/index.html`、`sim/styles.css` 已有 R17–R20 等未提交修改。
- 如果 MAIN 要求必须以 `280de35` 为 base，则应先在分支上 `merge remediation/20261113`（把当前工作树提交后）再开始 U2a；不能带着旧基线写接入点。
- 新 base commit 确定后，同步更新：
  - `docs/branches/QUIET-200.md` 的 `base_commit`；
  - `docs/branches/UX6-R15.md` 的 `base_commit`（如父支线也需重锚）；
  - `reports/branches/BRANCH-LEDGER.json` 的 `base_commit`/`branched_at`；
  - `docs/branches/REFERENCE-INDEX.md` 的基线说明。

### 理由

- 严格从 `280de35` 拉分支会缺当前 `loadHistory`/`renderHistory`/搜索/键盘实现，U2a/U2b 的接入点对不上；合并回 remediation 时冲突更大。
- 当前工作树还含监控台 `/monitor*` 路由等未提交改动；U2b 要加 `/sim/message-cache.js` 静态路由，必须基于包含现有 STATIC map 的版本。
- 先提交/冻结可以让“支线基线”可审计，符合 `docs/BRANCHING-PROTOCOL.md` 的锚点/回归点要求。

### MAIN 拍板点

- 是否允许先做一次 remediation 基线提交（可能包含 R17–R20、监控台等他人改动）？提交范围/作者/提交信息由谁定？
- 若不允许新 commit，是否接受“从 280de35 拉分支后先 merge 当前 remediation 工作树提交”的替代方案？

---

## 2. Q2 · IndexedDB 明文缓存

### 推荐默认值

**v1 接受明文 IndexedDB，但限定范围与清理边界。**

- 只存最近 200 条文本 + 媒体元数据；不存 token、`path`、URL、HTML、二进制。
- 浏览器 origin 隔离；文档写明“本机缓存、未加密、共享设备可见”的风险。
- 清理规则：
  - SSE `delete`：按 id 删对应缓存；
  - SSE `clear` / 显式“清空聊天”：清该会话缓存；
  - 单条删除：同步删；
  - “清屏”（只清 DOM）：**不**清缓存；
  - 退出/结束本地 I/O：**不**自动清（用户可能还要离线看）；以后可加“清除离线缓存”入口；
  - 卸载 App/清除浏览器数据：由系统处理。
- 如果 MAIN 的安全模型要求“共享设备不可读”，则 v1 需要加开关/加密，不能默认明文。

### 理由

- QUIET-200 的核心价值是断网/重启后可看；如果默认不持久化，需求落空。
- IndexedDB 是浏览器标准 origin 存储，和 localStorage 同信任级别；项目已有 token 明文 localStorage/SharedPreferences 的既存风险，缓存正文属于同一类，但需要明确告知。
- 加密会引入密钥管理/解锁体验，超出 U2a/U2b 范围；v1 先接受 + 文档 + 清理边界，后续再评估。

### MAIN 拍板点

- 接受明文缓存，还是要求 v1 加密/默认关闭/仅内存模式？
- 是否需要“退出登录/结束服务即清缓存”的产品语义？

---

## 3. Q3 · 媒体是否进入最近 200 条

### 推荐默认值

**v1 只缓存文本 + 媒体元数据（caption/name/mime/size/kind/at），不缓存图片/视频/文件二进制，也不缓存媒体 URL。**

- 离线时媒体消息仍显示一条记录/说明；图片/视频内容显示“媒体需联网查看”占位。
- “最近 200 条可查看”在 v1 的解释是：**消息列表、文本、说明、时间可查看**；不是“离线看图/看视频/下载文件”。
- 如果产品要求离线看图，另立“媒体缓存”卡，单独处理配额、加密、淘汰、隐私和 CDN/鉴权。

### 理由

- 二进制缓存会迅速放大存储（200 条 × 图片/视频），触发配额/隐私问题，且与“不缓存大二进制”的已拍板需求冲突。
- 媒体 URL 可能带 token/时效，缓存 URL 会泄漏或失效；不存 URL 更安全。
- 元数据足以让用户知道“这里有一条媒体消息”，不会把消息列表变成空洞。

### MAIN 拍板点

- 是否接受“媒体离线只显示元数据/占位”？
- 如果必须离线看图，是否另开媒体缓存卡，还是 U2b 扩大范围？

---

## 4. Q4 · 全局 2000 LRU 是否保护当前会话 200

### 推荐默认值

**保护当前会话最近 200 条；全局 2000 只淘汰其它会话。**

实现建议：

- `trimGlobal` 时跳过 `from === currentFrom` 的最近 200 个 key；
- 或在 `meta` 记录 `protectedFrom`/`protectedKeys`；
- 切会话后，旧会话不再受保护，可被 LRU 淘汰；
- 当前会话的 200 条始终优先保留。

### 理由

- 用户正在看的会话最需要离线可用；如果全局 LRU 把它挤掉，会出现“刚看完，断网就没了”的荒谬结果。
- 全局上限仍为 2000，只是把“当前会话 200”视为热数据；总内存仍有界。
- 实现成本低（按 from 查询 200 个 key 跳过）。

### MAIN 拍板点

- 是否接受“当前会话保护、其它会话 LRU”？
- 全局 2000 是否要随设备内存/配额调整（例如 1000/3000）？

---

## 5. Q5 · 消息身份 key 优先级

### 推荐默认值

**优先级：`id` > `mid` > `clientMessageId`（仅回声对账）> 指纹。v1 不缓存纯乐观/未确收消息。**

- 服务端 `id` 是主键；archive 的 `mid` 是稳定内容锚；`clientMessageId` 只用于“本地乐观发送 ↔ 服务端回声”对账，不作为长期缓存键。
- 纯乐观消息（`pending/sending/queued/failed`，尚无服务端 id/mid）不写入持久缓存；等服务端回显/成功后，用服务端 id 写入。这样避免“本地一条 + 服务端一条”重复。
- 无 id/mid 的历史行才用指纹：`type|role|at秒|body前200`；指纹只作兜底，不作为首选。
- 建议扩展纯函数 `historyMessageKey`：`id` → `mid` → 指纹；`clientMessageId` 只在 `historyMatchesOptimisticSend`/回声对账中使用。扩展后：
  - 缓存 key 继续加 `from|` 前缀隔离会话；
  - 若首次发布前改算法，DB 仍为 v1；若已发布后改，必须 bump `DB_VERSION` 并清缓存/迁移；
  - 增加 `cacheMessageKey` 与 `historyMessageKey` parity 测试。

### 理由

- `id`/`mid` 稳定、可删除、可去重；`clientMessageId` 是发送幂等键，不保证服务端历史行都带；指纹在同文同秒会碰撞。
- 不缓存纯乐观消息可以显著降低“重连后重复/删不掉”的风险，符合 v1 的保守策略。

### MAIN 拍板点

- 是否接受“纯乐观消息不持久化，成功后再缓存”？
- 若产品要求“离线也能看到自己刚发失败的消息”，需要把 failed/queued 队列与缓存分开设计（现有 localStorage 离线队列已保留，不必进 IndexedDB）。

---

## 6. Q6 · 离线缓存文案与范围提示

### 推荐默认值

| 位置 | 文案 |
|---|---|
| 聊天顶部缓存提示 | `离线缓存 · 最近 200 条（仅本机）` |
| 搜索状态行 | `离线缓存：最近 200 条；更早历史需联网` |
| 搜索空态 | `离线缓存里没有匹配；更早历史需联网后搜索` |
| 媒体占位 | `媒体需联网查看` |
| 有缓存但服务端失败 | 轻量提示 + 重试；**不**显示红色“历史加载失败”作为唯一状态 |
| 无缓存且服务端失败 | 现有 `history-error`“历史加载失败，可重试” |

- 不使用“全部历史”“已同步”“完整缓存”等误导词。
- 如果缓存因 LRU 不完整，可在设置/帮助里说明“仅保留最近 200 条”；v1 不在主界面加复杂容量 UI。

### 理由

- 需求明确要求“明确离线缓存范围”；文案必须让用户知道搜索不是全量。
- 有缓存可读时显示红色错误会让用户以为页面坏了；轻量提示 + 重试更符合离线可用。

### MAIN 拍板点

- 文案是否采用上述默认？是否需要中英/多语言？
- “离线缓存”是否要显示具体条数（200 或实际 less）？

---

## 7. Q7 · 清屏是否清缓存

### 推荐默认值

**“清屏”不清缓存；只有显式删除/清空/`clear` 事件清缓存。**

- `#clear-view` 只清 DOM/`seen`/滚动状态，保留缓存；用户可能只是想清空当前视图。
- 单条删除、SSE `delete`、SSE `clear`、显式“清空聊天”命令：同步删缓存。
- 以后可加“清除离线缓存”独立入口；v1 不做。

### 理由

- 清屏是视图操作，不是数据删除；把它等同删除会造成意外离线数据丢失。
- 用户对“删除/清空”有明确预期，缓存应跟随这些语义；清屏没有。

### MAIN 拍板点

- 是否接受“清屏不清缓存”？
- 是否需要在清屏后提示“离线缓存仍保留”？

---

## 8. Q8 · 预加载阈值

### 推荐默认值

**压力位 1.5 屏；快速触发 2.5 屏；速度用 `rows/s >= 40` 或 `px/s >= 1800`（OR）；采样 400ms/最多 5 点；冷却 400ms；spinner 350ms。**

- `px/s` 作为主速度指标，避免不同字号/气泡宽度导致行高估算偏差；`rows/s` 保留为产品语义/辅助。
- 触发条件：
  - 压力位：`scrollTop <= clientHeight * 1.5`；
  - 快速：`scrollTop <= clientHeight * 2.5` 且（`rowsPerSec >= 40` 或 `pxPerSec >= 1800`）；
  - `hasMore && !loading && now-lastTriggerAt >= 400ms`。
- spinner：请求开始 350ms 仍未回，或 `scrollTop <= 0` 且仍在加载；正常网络不可见。
- 这些是初始值，必须真机调；调参只改一个 `PRELOAD` 常量对象，不改状态机。

### 理由

- 1.5 屏给普通上翻足够的提前量；2.5 屏给快速上滑更多缓冲。
- 40 行/秒对应“快速上滑”的产品描述；px/s 兜底不同行高。
- 350ms 是“用户开始感觉等待”的合理阈值；低于此不闪 spinner。

### MAIN 拍板点

- 是否接受这组初始值？（可后续真机调，不必现在精确）
- 是否允许把阈值做成可配置常量（不暴露给用户）？

---

## 9. Q9 · `historyMessages` 上限 1000→2000

### 推荐默认值

**U2a 保持 1000，不立即提高；U2b 用“3 页预加载 + 切会话/重连”测试和内存预算评估后，再决定是否 2000。**

- `historyMessages` 是“当前会话已上屏历史快照”，用于重连 diff；不是 DOM 上限，也不是缓存上限。
- 预加载每页 200，1000 条约 5 页；超过后丢最旧快照，可能影响重连补齐的完整性，但 `seen`/DOM 仍保留。
- 若 R24 长历史或真机测试证明 1000 不够，再把常量提高到 2000，并补内存/长稳测试；不要在没有数据时直接翻倍。

### 理由

- 提高上限会增加 JS 内存（消息对象 + 文本），在低端 WebView 上可能抵消预加载收益。
- U2b 的 IndexedDB 缓存是独立 200/2000，不应和 `historyMessages` 混为一谈。
- 先测量再调，符合“不做无证据优化”。

### MAIN 拍板点

- 是否接受 U2a 暂不改 1000？
- 若 R24/真机要求 2000，内存预算上限由谁批准？

---

## 10. 后续行动顺序

1. **MAIN 拍板** Q1/Q2/Q3/Q4/Q7/Q9；Q5/Q6 确认；Q8 接受初始值。
2. 按 Q1 冻结/提交 remediation 基线；更新 `QUIET-200.md`、`UX6-R15.md`、`BRANCH-LEDGER.json` 的 `base_commit`/`branched_at`。
3. 在 `feat/quiet-200` 做 **U2a**（`UX6-R15-02a`）：删按钮、预加载状态机、spinner、锚定；跑 `test/history-preload.test.mjs` + `app-ui-fixes` 回归。
4. 做 **U2b**（`UX6-R15-02b`）：`sim/message-cache.js`、IndexedDB schema/trim/LRU、hydrate/merge/search/降级；加 `/sim/message-cache.js` 路由；跑 `test/offline-cache.test.mjs` + `recent` 回归。
5. 真机验收：断网/关闭重开、离线搜索范围、重连去重、切会话隔离、200/2000 淘汰。
6. QUIET-200 子支线 QA → 合并回 `feat/r15-ux6`；父支线 QA/收敛门 → `remediation/20261113`；打 tag；R16 继续，不跳过。
7. s2_sync_manifest：生成本 brief 要求的 `reports/branches/SYNC-GUARD.md` 与 `reports/branches/SYNC-MANIFEST.json`，并把本文件/索引纳入多文件夹一致性检查。

## 11. 本轮不做什么

- 不改产品代码、不建/切分支、不写 IndexedDB/预加载实现。
- 不改 `sim/app.js`、`sim/styles.css`、`sim/index.html`、`lib/local-io.mjs`。
- 不提交原始截图、不读取/输出聊天正文、不引用临时目录中的原始图片。
- 不把 staging/历史快照当可编辑主线；不改 `bridge-app`。
- 不实现同步检查脚本（s2 负责 manifest/check 规则）。
- 不替 MAIN 做隐私/基线/内存预算的最终决定；本文件只给推荐默认值。

## 12. 引用

- `docs/branches/REFERENCE-INDEX.md`（本轮的跨文档索引）
- `docs/branches/UX6-R15.md`、`docs/branches/QUIET-200.md`
- `docs/BRANCHING-PROTOCOL.md`
- `reports/branches/BRANCH-LEDGER.json`
- `reports/issues/SIX-ISSUES-INTAKE-20261113.md` / `.json`
- `reports/issues/QUIET-200-IMPLEMENTATION-PLAN.md` / `.json`
- `discussions/sync-guard-20261114/BRIEF.md`（外部讨论输入）


---

## 13. Q1 已收尾（2026-11-14）

- 全量安全快照：`e8a62bfa90377412b201bc8e40f64a3401c3f46e`
- curated 基线 B1：`f973b3f3e8e14184312f4e9e9f0085873f8c621e`
- 基线元数据提交 B2：`7680b1d39d27cb92fe6832c375adf4644c5306ec`
- `remediation/20261113`、`feat/r15-ux6`、`feat/quiet-200` 已指向 B2；工作树 clean。
- `feat/fast-response` 已 rebase 到 B2，当前提交 `7ad2c24`；ADB 27/27 + debug 24/24 PASS。
- 拆分策略：`reports/branches/BASELINE-SPLIT-STRATEGY.md`
- deck issue `#01` 可收尾。
