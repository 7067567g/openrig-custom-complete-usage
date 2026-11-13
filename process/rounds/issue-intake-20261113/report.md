# 六条真机问题 · 查收与实现分析（2026-11-13）

- 来源：`<WORKSPACE>/discussions/issue-intake-20261113/BRIEF.md`
- 性质：只读查收、分析、定位、排优先级；**本轮不改产品代码**。
- 隐私边界：6 张原始截图未打开、未复制、未提交；未读取或输出任何聊天正文。本报告只使用 Brief 的问题描述、哈希与现有代码。
- 结构化清单：`reports/issues/SIX-ISSUES-INTAKE-20261113.json`
- 相关基线：`docs/FORMAL-30-ROUND-PLAN-20261113.md`、`reports/sctg/FORMAL-RUN-STATE.json`、`docs/MONITORING-DASHBOARD-PLAN.md`、`docs/SESSION-REWIND-REATTACH-PLAN-20261113.md`

## 0. 结论摘要

| ID | 问题 | 类型 | 优先级 | 结论 | 主要落点 | 可同轮实现？ |
|---|---|---|---|---|---|---|
| I1 | 日历无消息日期置灰 | UX + bug | **P1** | 确认；现有是原生 `<input type="date">`，无法按日期禁用，需要自绘日历 + 可用日索引 | `sim/app.js`、`sim/styles.css`、`lib/local-io.mjs` | 可以，但需后端 day 索引 |
| I2 | 指令按来源同色，最近使用保持来源色 | UX | **P2** | 确认；现有 `recent-color-*` 按最近列表下标轮换，不是来源色 | `sim/app.js`、`sim/styles.css`、`sim/app-commands.js` | 可以，低风险 |
| I3 | 移除右上角齿轮，返回直达连接首页 | UX + 原生架构 | **P1** | 确认；“齿轮”是 `bridge-app` 原生 `⚙` 覆盖按钮，不是网页 `Aa` | `../bridge-app` 的 `activity_main.xml`、`MainActivity.java` | **不可以**，需独立 Android 工作区/轮次 |
| I4 | 键盘+指令时指令区压到两行 | UX + 布局 | **P1** | 确认；`.commands-panel` 固定 `38vh/46dvh`，键盘时没有两行上限 | `sim/app.js`、`sim/styles.css` | 可以，CSS 为主 |
| I5 | 记忆管理增加“查看待整理” | UX + 架构 + 隐私 | **P1** | 确认；当前只有待整理计数与“清空”，服务端 `snapshot` 不返回待整理条目 | `vendor/solo-memory/**`、`lib/app-runtime.mjs`、`sim/app.js` | 可以，但需 Swift 服务重建/重启 |
| I6 | 更早 500→更早 200，静默预加载+压力位 | 性能 + UX | **P1** | 确认；当前只有手动按钮，一次 500 条，滚动监听不触发预加载 | `sim/index.html`、`sim/app.js`、`sim/styles.css` | 可以，纯前端为主 |

**优先级口径**

- **P0**：数据丢失、安全泄漏、崩溃、无法发送/无法连接。本批**没有 P0**。
- **P1**：主路径明显受阻、破坏性动作缺少检查、或真机上高频卡住；建议下一批修复。
- **P2**：语义/视觉一致性、低频不便；可在 P1 之后做。

**建议实施顺序**

1. **I4**（键盘+指令区，最小改动，真机收益直接）
2. **I6**（历史预加载，纯前端，回归风险集中在滚动）
3. **I2**（指令来源色，低风险，补测试即可）
4. **I1**（日历可用日，需要后端 day 索引）
5. **I5**（待整理查看，跨 Swift/Node/前端，需隐私复核）
6. **I3**（原生齿轮/返回，独立 `bridge-app` 工作区，不能与主仓同轮）

---

## 1. 查收、去重与相关性

### 1.1 查收状态

- Brief 的 6 条问题都有明确的页面位置、现状和期望，**6 条均确认存在**，没有重复项。
- 图 1–5 是the assistant project 页面；图 6 是 QQ 参考图，用于表达 I6 的“预加载/压力位”目标，不作为the assistant project 缺陷。
- 原始截图仅登记 Brief 给出的 sha256；未打开图片，不判断像素级细节，因此 I3 的“齿轮”按代码定位为原生 `⚙`，见 §3.3 的歧义说明。

| 图 | sha256（来自 Brief） | 用途 |
|---|---|---|
| 1 | `6abfe82835e79e20239c2a44cf677b6dfe41520965a54a6458c9a887364a5045` | I1/I2 页面证据 |
| 2 | `a9113f6ffe239392b817bb3a24e8f0d6a1d8e59ac4f6916272601c22954101de` | I2 页面证据 |
| 3 | `0366d9af3f3b44a0e99b2514ae51e49dacef6b8791986dcec55ed832ed2a2542` | I3/I4 页面证据 |
| 4 | `3fd2a848d454bc9d381dacdcaaccc533ae6c5362db418b88f0b734106b39b066` | I4 页面证据 |
| 5 | `7bb36ea74c2412e1f04131f53e8e2603bef0f333ec84f3c217525fc1568434c8` | I5 记忆管理页 |
| 6 | `b39eb99dbb4419884d8b43f54db8b5fc9412c4e88152edaf4b5135af1ab18f19` | I6 QQ 参考图（非the assistant project） |

### 1.2 去重结论

| 关系 | 判断 | 说明 |
|---|---|---|
| I1 ↔ R14 消息搜索/回忆 | 相关但**不是重复** | R14 已交付原生日期过滤；I1 是“没有消息的日期不可选”的可用性补强 |
| I2 ↔ R05 指令反馈 / R19 设计系统 | 相关但**不是重复** | R05/R19 解决反馈与 token；I2 是来源色语义与最近使用映射 |
| I3 ↔ R21/R22/R23/R28 Android 轮 | 相关但**不是重复** | 原生壳的入口/返回逻辑，属于外部 `bridge-app` 轮次 |
| I4 ↔ R20 键盘/自适应、R06 滚动 | 相关但**不是重复** | R20 已有 `--keyboard-inset` 与 `body.keyboard-open`；I4 是“指令面板两行上限”的具体缺口 |
| I5 ↔ R15 记忆管理 | 相关但**不是重复** | R15 已有待整理计数与清空；I5 是“清空前可查看”的隐私/可用性补强 |
| I6 ↔ R06 滚动、R24 长历史 | 相关但**不是重复** | R06 保证上翻不跳；R24 面向长历史总量；I6 是分页大小、静默预加载、加载圈时机 |

**没有发现两条问题描述同一处代码的同一行为**；I4/I6 都碰 `sim/app.js` 的键盘/滚动区，但一个是指令面板高度，一个是历史分页，建议分轮。

---

## 2. I1 · 日历无消息日期置灰

### 2.1 确认与类型

- **确认**：是。位置为“搜索消息 → 回忆 → 日期选择器”。
- **类型**：UX + bug（日期可用性没有数据支撑）。
- **影响面**：移动端回忆；桌面浏览器同样受影响。用户会点到没有消息的日期，得到空结果，误以为“记录丢了”。
- **优先级**：**P1**（不是数据丢失，但直接影响回忆主路径）。

### 2.2 现状与代码落点

| 文件/函数 | 现状 |
|---|---|
| `sim/app.js:5907-5929` `buildMessageSearchSheet` 的 `recallRow` | 直接创建 `<input type="date" id="message-search-day">`，只有 `max=今天`，没有逐日禁用 |
| `sim/app.js:936-951` `messageSearchDayKey` / `messageSearchDayRange` | 只做日期 key 与本地日范围；没有“这一天有没有消息”的判断 |
| `sim/app.js:953-966` `messageSearchFilter` | 按 `day` 范围过滤已加载的消息；空结果只影响结果区 |
| `sim/app.js:5797-5813` 搜索常量/状态/`messageSearchCorpus` | 语料按页加载（500/页，最多 8 页/4000 条），`partial` 表示只覆盖最近加载范围 |
| `sim/app.js:6041-6072` `loadMessageSearchCorpus` | 通过 `/api/history` 翻页拼语料；没有 day 索引 |
| `lib/local-io.mjs:1495-1505` `/api/history` | 支持 `before/after/limit`，`limit` 上限 500；没有 `/api/history/days` |
| `lib/archive.mjs:202-212` `listDays` | 只列出有日档的日期；不等于“当前会话有消息的全部日期” |
| `lib/local-io.mjs:722-727` `archiveMessages` | 用 `listDays` 逐日读档；可作为 day 索引的归档侧来源 |

### 2.3 根因

1. 原生 `<input type="date">` **没有逐日禁用 API**；`min/max` 只能限制整段范围，不能把某几天置灰。
2. 后端没有“这个会话哪些天有消息”的轻量接口；现有 `/api/history` 只返回消息分页，前端只能靠已加载语料推断。
3. 现有语料最多 4000 条，`partial=true` 时无法代表全量日期；如果仅用 `messageSearchCorpus`，会错误地把“未加载”标成“无消息”。

### 2.4 实现建议

**推荐方案：自绘月历 + 后端 day 索引（方案 A）**

1. **后端**新增 `GET /api/history/days?from=<from>&month=YYYY-MM`：
   - 归档侧：`listDays` 后只取该月日期，逐日 `readDay`/`parseDayDetailed` 统计；沿用 `fixedFrom` 归属过滤，避免跨联系人泄漏。
   - journal/live 侧：按 `m.from === from` 与本地日 key 过滤 `journalEvents`/`messages`，补齐未归档的当天消息。
   - 返回 `{ month, days: [{ day: "YYYY-MM-DD", count, sources: ["archive","journal","live"] }], hasMore: false }`；只返回计数，不返回正文。
   - 对没有 `from` 的本地 I/O 模式，按当前 `from` 或全量（沿用现有权限）处理。
2. **前端**把 `input[type=date]` 换成月历 popover/面板：
   - 头部：上一月/下一月、`YYYY 年 MM 月`、回到今天；不晚于今天。
   - 7 列网格；有消息的日期用可点击按钮，无消息日期 `disabled` + `aria-label="2026-11-05，无消息"`；选中态、今天态、月份外日期明确区分。
   - 切换月份时请求 day 索引；缓存按月（TTL 同语料 60s）；请求失败显示“可用日期读取失败，仍可按日期搜索”并退回“全部日期可点”的降级模式。
   - 保留“今天”快捷键；`messageSearchState.day` 仍是 `YYYY-MM-DD`，`messageSearchDayRange`/`runMessageSearch` 不改语义。
3. **移动/桌面一致**：同一月历 DOM；移动端 7 列、44px 触控目标；桌面 hover/focus 只做增强，不依赖 hover。

**降级方案 B（不新增后端，先做 UI）**

- 用 `messageSearchCorpus` 的 `messages` 构造 `day -> count`，把没有命中的日期置灰；同时在状态行明确“仅基于最近加载的 N 条，未加载日期可能仍有消息”。
- 优点是零后端；缺点是不能满足“切月后状态正确”的完整验收，只适合作为过渡。**不建议作为最终方案**。

### 2.5 风险

- 归档与 journal/live 的归属过滤规则复杂，day 索引必须复用 `archiveBelongsToFixed`/`from` 规则，否则可能把其他联系人的日期暴露出来。
- 逐日读档的 IO 成本：按月只读 28–31 天，可接受；必须缓存并按月取消。
- 时区/跨日：沿用 `messageSearchDayKey` 的本地日语义；不要用 UTC 切日。
- 已有 R14 测试对 `input#message-search-day` 有断言；改自绘日历需同步更新测试，不能删断言。
- 原生日期输入的可访问性较好；自绘日历必须补键盘（方向键/Enter/Esc）、焦点环、`aria-disabled`。

### 2.6 验收清单

- [ ] 打开“回忆”，默认选中今天；今天有消息则可点，无消息则灰。
- [ ] 有消息日期可点，点击后结果与 `messageSearchDayRange` 一致；无消息日期灰且点击/键盘不可选。
- [ ] 切到上一个月，灰/可选状态正确；切回本月不丢选中。
- [ ] 未来日期不可选（不超过今天）。
- [ ] day 索引请求失败时，页面有明确降级提示，仍能按已加载日期搜索。
- [ ] 不会返回/显示其他联系人的日期或正文。
- [ ] 移动端 390px、桌面 1280px 布局正常；键盘可操作；亮/暗色可读。
- [ ] 新增纯函数测试（月历矩阵、可用日判断、跨月/闰年）与 `runMessageSearch` 回归。

### 2.7 拆轮与 write scope

- **建议 1 轮**（若后端 day 接口与自绘日历一起做）；若需要缩小，拆为 I1a（自绘日历 + 语料降级）与 I1b（后端 day 索引）。
- **write scope**：`sim/app.js`、`sim/styles.css`、`lib/local-io.mjs`、`lib/archive.mjs`（如需 helper）、`test/recent.test.mjs`、`test/local-io-app.test.mjs`。
- 不改 `sim/index.html`（日历动态挂载）；不碰聊天/治理主流程。

---

## 3. I2 · 指令按来源同色，最近使用保持来源色

### 3.1 确认与类型

- **确认**：是。位置为输入法上方的本地指令面板 / 最近使用。
- **类型**：UX（颜色语义/可识别性），不是功能 bug。
- **影响面**：所有本地指令面板；移动端最明显。最近使用跨来源混排时，颜色随位置轮换，用户无法建立“颜色=来源”的稳定记忆。
- **优先级**：**P2**（不影响发送/命令执行，属于一致性与可访问性）。

### 3.2 现状与代码落点

| 文件/函数 | 现状 |
|---|---|
| `sim/app.js:4640-4680` `DEFAULT_COMMAND_GROUPS` | legacy 分组：常用、任务与状态、模式、记忆、会话、文件与图、后台、连接与排障 |
| `sim/app.js:4730-4759` `APP_COMMAND_GROUPS` | App 分组：常用、会话、DSH 会话、记忆、任务、控制 |
| `sim/app-commands.js:225-254` `APP_COMMAND_GROUPS` | app-runtime 真值镜像；与 `sim/app.js` 有测试一致性约束 |
| `sim/app.js:4956-4979` `makeCommandButton` | `recentColor` 由调用方传入，`recent-color-${idx % 10}` 只是最近列表下标 |
| `sim/app.js:5010-5052` `renderCommands` | 把 `["最近使用", recentItems]` 插到“常用”后；`items.forEach((cmd, idx) => makeCommandButton(cmd, { recentColor: idx }))` |
| `sim/styles.css:700-726` | `.commands-list button` 默认色 + `.recent-color-0..9` 固定浅色 `!important`；没有来源 token，也没有暗色映射 |

**根因**：颜色是“最近使用列表的位置色”，不是“指令所属来源色”。`recent-color-*` 只在“最近使用”组内按 `idx` 轮换，离开该组就丢失；同一来源在不同组也没有统一色。

### 3.3 实现建议

1. **建立来源主映射（canonical source）**
   - 遍历 `defaultCommandGroupsFor(appMode)`，按组顺序给每个命令记录**第一次出现的组**作为主来源；同一命令出现在多个组（如“状态”“记忆”“/mode 对话”）时，以“常用”优先，其次按分组声明顺序。
   - “自定义”单独来源；“最近使用”不是来源，只是视图。
   - 输出 `commandSource = Map<cmd, {id, label, tone}>`，并暴露纯函数 `commandSourceFor(cmd)` 供测试。
2. **固定来源色 token**
   - 在 `sim/styles.css` 的 `:root` 定义 `--command-source-common/task/mode/memory/session/file/bg/ops/custom`（背景/边框/文字三件套），暗色块覆盖同名 token。
   - 用 `.command-source-<id>` 代替 `.recent-color-<idx>`；去掉 `!important`，用选择器优先级或 CSS 变量。
   - 颜色只作辅助：chip 增加 `title`/`aria-label` 含“来源：记忆”，或在最近使用列表加小圆点 + 来源短标签；不能只靠颜色。
3. **渲染规则**
   - 普通分组：组内所有 chip 使用该组来源色。
   - 最近使用：每个 chip 用其主来源色；不再按下标轮换。
   - 自定义：neutral；无来源映射的旧命令：neutral + `title` 说明。
   - 保留 `selected` 的 outline，不覆盖来源色。
4. **对比度**：亮/暗色都满足 4.5:1；不要沿用当前固定的浅色 hex 直接塞进暗色主题。

### 3.4 风险

- 同一命令多组出现时，“主来源”是产品决策；需在卡里写死优先级，避免实现者各选一套。
- `sim/app-commands.js` 与 `sim/app.js` 的 `APP_COMMAND_GROUPS` 有测试一致性约束；改分组要同步两处，否则 `test/app-commands.test.mjs` 会失败。
- 现有 `recent-color-*` 可能被其他样式/测试引用；替换时保留一个兼容别名或同步更新测试。
- 颜色数量多（8–10 组）时，色相区分有限；必须用文本/来源标签补足。

### 3.5 验收清单

- [ ] 同一分组内所有 chip 颜色一致；不同来源颜色不同。
- [ ] `最近使用` 中同一命令与它在主分组中的颜色一致；跨来源混排仍能区分。
- [ ] 同一命令出现在多个分组时，按卡内声明的“主来源”取色。
- [ ] 亮/暗色下文字对比度 ≥4.5:1；不只用颜色表达来源（title/aria-label 至少一项）。
- [ ] 自定义命令有 neutral 来源色；未知命令不报错。
- [ ] `test/app-commands.test.mjs` 的分组一致性仍通过；新增来源映射纯函数测试。

### 3.6 拆轮与 write scope

- **建议 1 轮**，低风险，可在 I4/I6 之后。
- **write scope**：`sim/app.js`、`sim/styles.css`、`sim/app-commands.js`（仅当分组真值需要同步）、`test/app-commands.test.mjs`、`test/app-ui-fixes.test.mjs`。

---

## 4. I3 · 去掉右上角圆形齿轮，返回直达连接首页

### 4.1 确认与类型

- **确认**：是，但“齿轮”有两个候选，代码定位如下：
  - **原生 `bridge-app` 的 `settings_button`**：`activity_main.xml` 中 40dp、`layout_gravity="top|end"`、`text="⚙"`、`alpha=0.42`，悬浮在 WebView 右上角；键盘弹出时隐藏。它与 Brief 的“圆形齿轮 / 更早上方”一致，**高置信度是这条**。
  - **网页 `#display-button`**：`sim/index.html:125` 的 `Aa` 按钮，打开显示设置 sheet；它是文字按钮，不是齿轮。
- **类型**：UX + 原生架构（`bridge-app` 不在主仓）。
- **影响面**：Android WebView 顶栏；设置入口与系统返回路径。
- **优先级**：**P1**（导航/设置入口），但**阻塞于独立 Android 工作区**。

### 4.2 现状与代码落点

| 文件/函数 | 现状 |
|---|---|
| `../bridge-app/app/src/main/res/layout/activity_main.xml:14-31` | `settings_button`：40dp、top|end、`⚙`、半透明、elevation 6 |
| `../bridge-app/app/src/main/java/com/example/bridge/MainActivity.java:145,163-164` | `settings_button` 与 `overlay_settings_button` 都绑定 `showSetup()` |
| `MainActivity.java:133-136` | 键盘弹出时隐藏 `settings_button` |
| `MainActivity.java:748-772` | `onBackPressed()`：状态覆盖层 → 关；WebView 可见 → 先收 IME；`webView.canGoBack()` 则 `goBack()`；否则 `showSetup()` |
| `MainActivity.java:774-790` | 设置页返回：有保存入口/曾加载成功 → 回 WebView，否则退出 |
| `sim/index.html:125` | 网页 `Aa` 显示设置按钮（不是齿轮） |
| `sim/app.js:5176-5226` | `displayButton` 打开 `display-sheet`；`displayClose`/遮罩关闭 |

**根因**：原生 `settings_button` 是常驻悬浮入口；`onBackPressed` 优先 `webView.canGoBack()`，而 WebView 可能因为重定向/历史记录而“可后退”，导致返回不是直接回连接首页。移除齿轮后，如果不同时改返回逻辑，设置入口会只剩“系统返回”这一条，且可能被 WebView 历史劫持。

### 4.3 实现建议

1. **移除原生悬浮齿轮**
   - `activity_main.xml` 删除 `settings_button`（或 `visibility="gone"` 且不再引用）；同步删除 `MainActivity` 中的 `findViewById`、可见性切换、点击绑定。
   - 保留 `overlay_settings_button`（离线/错误覆盖层的“打开设置”），以及设置页本身；设置入口不会彻底丢失。
2. **返回直达连接首页**
   - `onBackPressed()` 在 WebView 可见且 IME 已收起时，直接 `showSetup()`，不再走 `webView.canGoBack()`。
   - 如果未来 WebView 内部有真正的多页导航（当前链接走外部浏览器），再引入显式 `pageStack`/`doUpdateVisitedHistory` 判断；v1 用“聊天根 → 设置页”单层语义最稳。
   - 首次加载完成后可 `webView.clearHistory()`，避免重定向留下的历史把返回带偏。
3. **设置入口 discoverability**
   - 因为齿轮移除，建议在连接首页/设置页保留说明“聊天页按返回可回到这里”；或在聊天页首次进入时给一次性提示（原生 Toast/网页提示），不要恢复常驻齿轮。
4. **网页 `Aa`**
   - 本问题不要求移除 `Aa`；它是显示设置，不是“齿轮”。若产品实际想移除 `Aa`，需要另开卡，并把 `display-sheet` 入口迁到设置页/长按菜单，否则显示设置会丢失。

### 4.4 风险

- `bridge-app` 不在主仓；按 `docs/FORMAL-30-ROUND-PLAN-20261113.md` 的约束，R21/R22/R23/R28 是外部 Android 轮，**没有独立工作区不得跨仓写入**。I3 不能塞进主仓 UI 轮。
- 移除 `settings_button` 后，设置入口只剩系统返回；若用户不知道返回，会降低可发现性。需要一次性提示或设置页说明。
- `onBackPressed` 直接 `showSetup()` 会改变“WebView 可后退”的语义；当前链接都走外部浏览器，风险低；若未来有内嵌导航，需要 pageStack。
- 需要真机验证手势返回、IME 优先级、状态覆盖层优先级；headless 不能替代。

### 4.5 验收清单

- [ ] 聊天页右上角不再有原生 `⚙`；键盘弹出/收起不再出现。
- [ ] 系统返回/手势：先关状态覆盖层，再收 IME，然后直接到连接首页（设置页），不经过 WebView 历史页。
- [ ] 设置页仍可打开、保存 URL/token、检查连接、回到聊天。
- [ ] 离线/错误覆盖层的“打开设置”仍可用。
- [ ] 网页 `Aa` 显示设置仍可用（除非另卡明确移除）。
- [ ] 真机 Android 16（<DEVICE>）与至少一个旧 WebView 验证。

### 4.6 拆轮与 write scope

- **不能与主仓同轮**；建议作为独立 `bridge-app` 卡，挂在 R21/R22/R23/R28 或单独 Android run。
- **write scope**：`../bridge-app/app/src/main/res/layout/activity_main.xml`、`../bridge-app/app/src/main/java/com/example/bridge/MainActivity.java`，必要时 `app/build.gradle`/版本号。
- 主仓不改；如果只改主仓 `sim/index.html` 的 `Aa`，那不是这条问题的正确修复。

---

## 5. I4 · 键盘 + 指令同时出现时，指令区压到两行

### 5.1 确认与类型

- **确认**：是。位置为输入法弹起 + 本地指令面板展开。
- **类型**：UX + 布局 bug。
- **影响面**：移动端键盘打开时；第三行指令（如 `/session-delete`）不可见或挤压聊天区/composer。
- **优先级**：**P1**（键盘是高频路径，指令区被挤压会直接影响操作）。

### 5.2 现状与代码落点

| 文件/函数 | 现状 |
|---|---|
| `sim/index.html:149-168` `#command-tray` | 指令托盘在 `composer-wrap` 之前；含分组栏、`#commands-panel`、编辑区 |
| `sim/index.html:170-187` `.composer-wrap` | 输入区在托盘之后；键盘 inset 只作用于 composer-wrap |
| `sim/app.js:1192-1200` `syncKeyboardInset` | 用 `innerHeight - visualViewport.height - offsetTop` 算 inset，`inset > 80` 才加 `body.keyboard-open` |
| `sim/app.js:1423-1440` `onViewportResize` | `visualViewport` resize/scroll + `window.resize` 时重算 inset |
| `sim/styles.css:695` `.commands-panel` | `max-height: 38vh; overflow-y:auto` |
| `sim/styles.css:1638` 移动端 | `.commands-panel { max-height: 46dvh; }` |
| `sim/styles.css:613-617` `.command-tray` | 固定 padding/背景，不参与键盘高度预算 |
| `sim/styles.css:835-837` `.composer-wrap` | `padding-bottom: var(--keyboard-inset)`；`body.keyboard-open` 只加阴影/减 composer padding |

**根因**：指令面板的 `max-height` 是视口百分比，不是“两行 chip”的固定预算；键盘打开时 `command-tray` 仍在 composer 上方，面板高度不收缩，composer 只能靠 `--keyboard-inset` 上移，整体高度超限。另一个隐患：Android WebView 若自己缩布局视口，`inset` 可能为 0，`body.keyboard-open` 不会置位，CSS 两行规则也不会生效。

### 5.3 实现建议

1. **两行高度 token**
   - 在 `:root` 增加 `--command-row-h: 30px`、`--command-panel-two-rows: calc(2 * var(--command-row-h) + var(--space-2) * 2)`（约 76–84px，按真机实测微调）。
   - `body.keyboard-open .commands-panel { max-height: var(--command-panel-two-rows); overflow-y: auto; overscroll-behavior: contain; -webkit-overflow-scrolling: touch; }`
   - 移动端覆盖 `46dvh`，只在键盘打开时启用；关键盘恢复 `38vh/46dvh`。
2. **键盘检测兜底**
   - 保留 `--keyboard-inset`；另加 `keyboardOpen` 判定：`inset > 80` **或** `visualViewport.height < screen.height * 0.72` **且** `document.activeElement` 是 `textarea/input`。
   - 在 `focusin`/`focusout` 上做即时 class 切换，`resize` 只做校正；避免 Android 缩布局视口时 class 不置位。
   - 不要用 `window.innerHeight` 与自身比较（Android 会一起缩）；用 `screen.height`/`outerHeight` 作为参照。
3. **滚动边界**
   - `.commands-panel` 自身滚动，第三行可滚动到达；不要让整个 `.phone` 滚动。
   - 给 `.commands-panel` 加 `scroll-padding-bottom`，确保最后一行不被 composer 遮住。
   - `command-tray` 保持 `flex: 0 0 auto`，不参与 `1fr` 聊天区压缩；聊天区 `minmax(0,1fr)` 继续吸收剩余高度。
4. **可发现性**
   - 面板底部可加渐隐/“向下滚动查看更多”提示（可选）；不要用 hover。
   - 编辑模式（`#command-editor`）不是“指令行”，可不受两行限制，或单独给 `max-height`；卡里要明确。

### 5.4 风险

- “两行”是视觉行还是分组行？按 chip 行实现；分组标题/筛选框仍占高度，需在真机确认红线位置。
- 键盘检测阈值可能在小屏/横屏误判；用 `activeElement` + `screen.height` 双条件，并保留 `inset` 主路径。
- 现有 `test/app-ui-fixes.test.mjs:897-902` 有 `--keyboard-inset`/`body.keyboard-open` 静态断言；新增规则不能删旧断言。
- 不同 Android WebView 的 `visualViewport` 行为差异大；必须真机验证，不能只靠 headless。
- 编辑模式/附件托盘/任务条同时打开时高度竞争；建议限制同时展开的浮层，或在卡里定义优先级。

### 5.5 验收清单

- [ ] 键盘打开 + 展开指令组：指令面板最多显示两行 chip，第三行可向下滚动到达。
- [ ] composer 始终可见，不被指令面板/键盘遮挡；发送按钮可点。
- [ ] 关闭键盘：面板恢复原高度/滚动位置，不跳。
- [ ] 编辑模式打开时布局不破；附件托盘/任务条同时出现时不互相覆盖。
- [ ] Android 16 真机 + 至少一个旧 WebView；横屏/小屏各一次。
- [ ] 键盘弹出时 `body.keyboard-open` 确实置位（可在真机 console 或调试页确认）。

### 5.6 拆轮与 write scope

- **建议 1 轮**，先于 I6（同一区域，先稳定高度再改历史滚动）。
- **write scope**：`sim/app.js`（键盘检测）、`sim/styles.css`（token/两行规则）、`test/app-ui-fixes.test.mjs`；不改 `sim/index.html`。
- 与 R20 键盘/自适应、R06 滚动回归共用测试文件，需串行写入。

---

## 6. I5 · 记忆管理：清空待整理前必须可查看待整理

### 6.1 确认与类型

- **确认**：是。位置为记忆管理 → “清空待整理”。
- **类型**：UX + 架构 + 隐私（破坏性动作缺少检查；服务端未暴露待整理条目）。
- **影响面**：所有长期记忆用户；清空不可恢复，用户看不到将删除什么。
- **优先级**：**P1**（破坏性动作 + 隐私边界）。

### 6.2 现状与代码落点

| 文件/函数 | 现状 |
|---|---|
| `sim/app.js:6371-6385` | `pending` 盒子只有 `memoryPendingText(view.pending)` + “清空待整理”按钮 |
| `sim/app.js:6645-6657` | 只根据 `view.pending` 显示数量/禁用清空；没有列表 |
| `lib/app-runtime.mjs:122-164` `buildMemoryView` | 只返回 `pending` 计数；`rows` 是长期记忆摘要，不含待整理 |
| `lib/app-runtime.mjs:378-405` `publishMemoryView` | 广播 `memory/state` 视图 |
| `lib/solo-memory.mjs:477` `snapshot` | 调用 Swift service 的 `snapshot`，原样返回 |
| `vendor/solo-memory/Sources/SoloMemoryService/main.swift:44-53` `SnapshotResponse` | 只有 `pendingCount`、`recentCount`、`items`；没有 pending 条目 |
| `main.swift:160-170` `case "snapshot"` | 只映射 `snap.pending.count` |
| `SoloMemoryEngine.swift:28-32` `SoloMemorySnapshot` | 内部有 `pending: [SoloMemoryEvent]`，但 service 没暴露 |
| `SoloMemoryEvent.swift` | 事件含 `id/role/text/at`；`text` 已由 `SoloMemoryRedaction` 处理，但仍可能较长 |

**根因**：服务端 DTO 只给计数，UI 无法列出待整理；前端即使想显示也不能凭空生成，否则会绕过 owner/隐私边界。

### 6.3 实现建议

**推荐：服务端增加只读 pending 摘要，前端加“查看待整理”入口。**

1. **Swift service**
   - `SnapshotResponse` 增加 `pendingEvents: [PendingEvent]`（或 `pendingRows`）：
     ```swift
     struct PendingEvent: Encodable {
       let at: Date
       let role: String       // user/assistant
       let summary: String    // 60–80 字，复用 SoloMemoryRedaction + 截断
     }
     ```
   - `case "snapshot"` 映射 `snap.pending.prefix(50)`；**不返回 `text` 全文、不返回事件 id**（v1 只需查看，不需要逐条删除；逐条删除另卡）。
   - 保持 `pendingCount` 不变，新增字段是向后兼容的加法；旧前端忽略。
2. **`lib/app-runtime.mjs`**
   - `buildMemoryView` 增加 `pendingRows`（数组，`{at, role, summary}`），`pending` 计数仍保留。
   - `memoryErrorView` 的 `pendingRows: []`；`enabled:false` 同样空数组。
   - 不把 pending 全文写日志、不写 SSE 以外的持久层。
3. **`sim/app.js` UI**
   - 在待整理盒子旁增加“查看待整理”按钮，或把待整理做成 tab（推荐按钮 + 二级视图，避免主列表被 tab 切走）。
   - 二级视图：只读列表，显示时间、角色（我/the assistant）、摘要；顶部“共 N 条”；空态“没有待整理”；错误态“读取失败，稍后重试”。
   - “清空待整理”仍只作用于 pending；二次确认保留；查看动作不发命令、不改状态。
   - 隐私：摘要截断 60–80 字，不回显完整正文；不复制到剪贴板；不写 console。
4. **方案对比**
   - **按钮 + 二级视图（推荐）**：改动小，保留长期记忆列表焦点；待整理是低频检查。
   - **Tab（记忆 / 待整理）**：发现性更好，但要多一套 tab 状态/键盘/空态；适合后续条目多时。
   - **仅显示“查看”链接到聊天 `/memory pending`**：不推荐，回执只有计数，仍看不到条目。

### 6.4 风险

- Swift service 需要重建/重启；`tools/build-solo-memory-service.sh` 与 `systemd` 服务窗口要安排，不能在用户聊天高峰做。
- `SoloMemoryEvent.text` 可能含敏感内容；摘要必须服务端生成，不能把全文传到前端再截断。
- `pendingRows` 是 `v:1` 视图的加法；旧 App/旧前端忽略即可，但要确认没有严格 schema 校验。
- 待整理条目可能很多（`maxPendingEvents`），只返回前 50 条并显示“还有 N 条”，避免大响应。
- 不能把“查看待整理”做成“清空”的确认替代；清空仍需二次确认。
- 现有 `test/app-runtime-memory.test.mjs` 可能对 `memory/state` 字段做深比较；新增字段需更新断言，不能删旧断言。

### 6.5 验收清单

- [ ] 记忆管理能看到“查看待整理”入口；点击后列出 pending 摘要（时间/角色/摘要），不显示全文。
- [ ] 列表只读；不会触发整理/写入；关闭后回到记忆管理原状态。
- [ ] “清空待整理”仍只清 pending，不动长期记忆；二次确认仍有效。
- [ ] 空态“没有待整理”；读取失败有错误态和重试；`pendingCount` 与列表条数一致（或明确“仅显示前 50”）。
- [ ] 不返回事件 id/全文；日志无 pending 正文；SSE 只含摘要。
- [ ] Swift 服务重建后旧前端仍能工作（忽略新字段）。
- [ ] 真机/浏览器验证亮暗色、键盘、滚动。

### 6.6 拆轮与 write scope

- **建议 1 轮**，放在 I1/I4/I6 之后；需要 Swift 构建 + 服务重启窗口。
- **write scope**：`vendor/solo-memory/Sources/SoloMemoryService/main.swift`（必要时 `SoloMemoryEngine.swift` 只读）、`lib/app-runtime.mjs`、`sim/app.js`、`sim/styles.css`、`test/app-runtime-memory.test.mjs`、`test/app-ui-fixes.test.mjs`。
- 不改 `lib/panel/**`、监控台、治理主流程。

---

## 7. I6 · “更早 500” → “更早 200”，静默预加载 + 压力位

> **2026-11-14 修订**：手动“更早”按钮移除，改为纯静默预加载；最近 200 条消息必须本地持久化，断网/重启后仍可查可搜。以 §12 为准。

### 7.1 确认与类型

- **确认**：是。位置为聊天历史顶部“更早 500”。
- **类型**：性能 + UX（长历史加载策略）。
- **影响面**：长会话、弱网、快速上翻；当前一次 500 条偏重，加载圈只在点击后出现。
- **优先级**：**P1**（长历史是主路径；影响滚动流畅与等待感）。

### 7.2 现状与代码落点

| 文件/函数 | 现状 |
|---|---|
| `sim/index.html:126` | `<button id="load-older" ...>更早 500</button>`，title“加载更早的 500 条消息” |
| `sim/app.js:1178-1180` | `oldestAt`、`historyHasMore`、`loadingHistory` |
| `sim/app.js:2548-2554` | `renderHistory` 后按 `historyHasMore` 显示/隐藏按钮 |
| `sim/app.js:2554-2585` `loadHistory` | 首屏 `limit=500`；无分页大小常量 |
| `sim/app.js:2587-2605` `loadOlder` | 手动 `limit=500&before=oldestAt`；`loadingHistory` 防重入；失败 `showHistoryError("older")` |
| `sim/app.js:2513-2516` `rememberHistoryMessages` | 历史快照上限 1000 条；超出丢最旧 |
| `sim/app.js:1413` | `chat.addEventListener("scroll", updateStickyFromScroll)`；没有近顶预加载 |
| `sim/app.js:1320-1345` | sticky/上翻逻辑；预加载必须不影响 scrollTop |
| `lib/local-io.mjs:1495-1504` | `/api/history` `limit` 上限 500；200 完全支持，无需后端改 |
| `test/app-ui-fixes.test.mjs:157-159` | 已有 `loadHistory/loadOlder` 错误处理断言 |

**根因**：分页只有手动按钮；`loadOlder` 没有滚动触发、没有预取/并发去重/取消；加载指示只有按钮显隐，没有“真实等待”阈值。

### 7.3 实现建议

1. **常量与文案**
   - `const OLDER_PAGE_SIZE = 200;`，`loadOlder` 使用它；`loadHistory` 是否也改 200？建议首屏仍 500（首屏体验），更早 200；卡里写清。
   - `sim/index.html` 按钮文案/标题改为“更早 200”“加载更早的 200 条消息”。
2. **预加载触发**
   - `maybePreloadOlder()` 在 `chat` scroll 上节流（`requestAnimationFrame` 或 100ms）调用。
   - **压力位**：`chat.scrollTop < chat.clientHeight * 1.5`（约 1.5 屏）且 `historyHasMore`。
   - **快速上滑**：记录最近 3–5 个 scroll 采样（`scrollTop`+时间），估算“每秒上翻行数”；超过约 40 行/秒时提前到 2.5 屏触发。行高可用平均消息高度或固定 56px 估算；卡里给公式。
   - 也可用“剩余可滚动距离 < 100 条消息 * 估算行高”作为压力位，避免不同字号/气泡宽度误差。
3. **并发、取消、去重**
   - `let loadingOlder = false; let olderRequestSeq = 0;`；每次请求 `seq`，会话切换/新请求时 `seq++`，旧响应丢弃。
   - 如果 `fetch` 支持 `AbortController`，在会话切换/`loadHistory` 重置时 abort；不支持则靠 seq。
   - `loadOlder` 同时被按钮和预加载调用时，共享同一个 in-flight Promise，不重复追页。
   - `oldestAt` 只在成功且 `data.oldestAt` 有效时更新；`hasMore` 以服务端为准。
4. **加载圈时机**
   - 新增顶部小 spinner（`#history-loading`，可动态挂载或放 index），默认隐藏。
   - 请求开始后 350ms 仍未返回 → 显示；或用户已到绝对顶部（`scrollTop<=0`）且没有新内容 → 立即显示。
   - 成功/失败/取消后隐藏；失败仍用现有 `history-error` 重试，不把 spinner 当错误。
   - 正常网络下预加载在 1.5–2.5 屏内完成，用户不应看到 spinner（“静默”）。
5. **滚动锚定与内存**
   - 复用 `renderHistory(..., {prepend:true})` 的 `prevHeight/prevTop` 补偿；预加载不能改 `stickyBottom`。
   - `historyMessages` 上限 1000：预加载 200 条后可能丢最旧快照，但 DOM 仍保留；需确认 `renderHistory` 的 dedupe/重连不因此重复。建议把上限提高到 2000 或按 DOM 上限裁剪，并在卡里明确。
   - 页面切后台/会话切换：取消预加载，避免旧会话数据混入。

### 7.4 风险

- 预加载触发太早会浪费流量/内存；太晚则用户看到 spinner。需要真机调阈值（1.5/2.5 屏、40 行/秒）。
- `historyMessages` 1000 上限与 DOM 增长不一致；预加载多页后重连 diff 可能丢旧消息。必须在测试里覆盖“加载 3 页后切会话/重连”。
- `loadingHistory` 同时用于首屏和更早；拆成 `loadingOlder` 时不要破坏首屏防重入。
- 上翻时插入内容容易跳；现有 `renderHistory(prepend)` 已有补偿，但快速滑动/图片解码仍可能抖；需要 `ResizeObserver` 兜底。
- 按钮文案/测试静态断言可能引用“更早 500”；需同步更新，不删断言。
- 后端 `limit` 上限 500，200 无需改；如果未来改 100/300，确认服务端仍接受。

### 7.5 验收清单

- [ ] 按钮文案/title 为“更早 200”；点击一次最多追加 200 条。
- [ ] 快速上滑（约 40 条/秒）或到达压力位（约 1.5 屏/100 条）自动预加载；正常网络无感。
- [ ] 连续上滑不重复请求同一 `before`；不重复插入消息；`oldestAt` 单调前进。
- [ ] 加载圈只在请求 >350ms 或已到绝对顶部时出现；成功/失败后消失。
- [ ] 预加载插入后当前阅读位置不跳；`stickyBottom` 不被误改；图片解码后仍锚定。
- [ ] 会话切换/退出时取消旧请求；旧响应不落到新会话。
- [ ] 弱网/失败：显示 `history-error`，可重试；不清空已加载消息。
- [ ] 加载 3 页后切会话/重连，不出现重复/丢消息；内存上限行为明确。
- [ ] 与 R06/R20 的滚动/键盘回归通过。

### 7.6 拆轮与 write scope

- **建议 1 轮**；若风险大，拆 I6a（200 + 预加载 + 去重）与 I6b（spinner/速度阈值/长历史内存）。
- **write scope**：`sim/index.html`、`sim/app.js`、`sim/styles.css`、`test/app-ui-fixes.test.mjs`（或新增 `test/history-preload.test.mjs`）。
- 不改后端；与 R06/R24 串行，避免同一 `sim/app.js` 并发写。

---

## 8. 与正式 30 轮 / 监控台 / 会话治理的冲突与依赖

### 8.1 正式 30 轮

- `reports/sctg/FORMAL-RUN-STATE.json` 当前 `active_round=R16`、`blocked_rounds=["R16"]`、`last_error="manual checkpoint NEED_MAIN"`；`ROUND-MAP.md` 把 R17–R20 标为 pending product，但工作区已有 R17–R20 报告。**以 RUN-STATE 的 R16 人工检查点为准**，新问题不应覆盖 R16 的 NEED_MAIN 结论。
- 六条问题都发生在 `sim/app.js`/`sim/styles.css` 或其依赖；正式轮次对 `sim/**` 是单写者。建议作为 **R16 之后的新 remediation 卡**（或独立 issue-fix run），不要插进正在收口的轮次。
- **I3** 属于 `bridge-app` 外部轮（R21/R22/R23/R28）；按合同“没有独立工作区不得跨仓写入”，必须独立 run/人工窗口。
- **I5** 涉及 `vendor/solo-memory` Swift 服务；正式轮的 `tools/build-solo-memory-service.sh` 与 systemd 重启窗口要协调。

### 8.2 监控台（本轮新增）

- 监控台新增 `lib/panel/monitor-*`、`/monitor*` 静态路由、`lib/panel/index.html` 入口；与本批六条问题的产品面不同。
- **文件级交叉**：`lib/local-io.mjs` 的 `STATIC` map（监控台已改）与 I1 可能要加的 `/api/history/days` 路由，同文件不同区域；建议 I1 卡先合并/确认当前未提交的监控台改动，避免覆盖。
- 监控台的 `lib/panel` 不涉及 `sim/app.js`，I2/I4/I6 无冲突；I1/I5 若改 `lib/local-io.mjs`/`lib/app-runtime.mjs`，需与监控台路由改动串行。
- 监控台设计文档 `docs/MONITORING-DASHBOARD-PLAN.md` 已记录 Round 2 落地；不要把六条问题塞进监控台组件库。

### 8.3 会话治理 / 回退

- `docs/SESSION-REWIND-REATTACH-PLAN-20261113.md` 主要改 DSH 上下文映射，不改聊天 UI 的滚动/键盘；I4/I6 与其无直接冲突。
- I3 的“返回直达连接首页”是原生 WebView 导航，不是 DSH 回退；不要混用“撤回/回退”语义。
- I1 的“回忆”是消息搜索，不是上下文回退；测试和文案要区分。

### 8.4 依赖/冲突矩阵

| 问题 | 依赖 | 冲突/串行要求 |
|---|---|---|
| I1 | `/api/history`、`listDays`、`archiveMessages`、`messageSearchCorpus` | 与 R14 测试、`lib/local-io.mjs` 监控台路由改动串行 |
| I2 | `DEFAULT_COMMAND_GROUPS`/`APP_COMMAND_GROUPS` 真值 | 与 `sim/app-commands.js` 测试一致性；与 R05/R19 串行 |
| I3 | `../bridge-app` 独立工作区 | 与主仓完全隔离；不能同轮 |
| I4 | `visualViewport`/`--keyboard-inset`/`.commands-panel` | 与 R20 键盘、R06 滚动、I6 同文件串行 |
| I5 | Swift `snapshot` DTO、`buildMemoryView`、memory SSE | 与 R15 测试、服务重启窗口；隐私复核 |
| I6 | `/api/history` 200、`renderHistory(prepend)`、`historyMessages` 上限 | 与 R06/R24、I4 同文件串行 |

---

## 9. 建议拆轮与 write scope 汇总

| 轮次建议 | 内容 | write scope | 预估风险 |
|---|---|---|---|
| **U1** | I4 键盘+指令两行 | `sim/app.js`、`sim/styles.css`、`test/app-ui-fixes.test.mjs` | 中（真机键盘差异） |
| **U2** | I6 更早 200 + 静默预加载 + spinner | `sim/index.html`、`sim/app.js`、`sim/styles.css`、`test/app-ui-fixes.test.mjs` 或新测试 | 中高（滚动锚定/并发） |
| **U3** | I2 指令来源色 | `sim/app.js`、`sim/styles.css`、`sim/app-commands.js`、测试 | 低 |
| **U4** | I1 日历可用日 | `sim/app.js`、`sim/styles.css`、`lib/local-io.mjs`、`lib/archive.mjs`、测试 | 中（归属/时区） |
| **U5** | I5 待整理查看 | `vendor/solo-memory/**`、`lib/app-runtime.mjs`、`sim/app.js`、`sim/styles.css`、测试 | 高（Swift/隐私/重启） |
| **U6** | I3 原生齿轮/返回 | `../bridge-app/**` | 高（独立仓/真机） |

**不建议**把 I4+I6 合并成一轮：都改 `sim/app.js` 滚动/键盘，但验收复杂，容易互相掩盖回归。若排期紧，可先 U1（I4）再 U2（I6）。

---

## 10. 未验证项与不提交清单

- 原始 6 张截图：**未打开、未复制、未提交**；仅按 Brief 哈希登记。
- 聊天正文：**未读取、未输出**；所有代码引用只到函数/样式/路由层。
- 未在真机执行；I3/I4/I5/I6 的真机行为仍需 Android 16（<DEVICE>）与旧 WebView 验收。
- 未运行 `tools/sctg/check_round.py`；本轮不是 SCTG 产品轮，不写 submission/gate。
- 未修改任何产品代码；本轮只新增两个 `reports/issues/` 文件。
- `bridge-app` 的 `MainActivity.java`/`activity_main.xml` 只读检查；未构建 APK、未安装、未改原生代码。

---

## 11. 代码索引（只读）

| 主题 | 路径 |
|---|---|
| 搜索/回忆面板 | `sim/app.js:5794-5970`、`936-1010`、`6041-6072` |
| 历史分页 | `sim/app.js:1178-1180`、`2513-2516`、`2548-2605`、`1413` |
| 指令分组/颜色 | `sim/app.js:4640-4680`、`4730-4759`、`4956-5072`、`sim/styles.css:700-726`、`sim/app-commands.js:225-254` |
| 键盘/布局 | `sim/app.js:1192-1200`、`1423-1440`；`sim/styles.css:613-617`、`695`、`835-837`、`1638` |
| 记忆管理 | `sim/app.js:6283-6754`；`lib/app-runtime.mjs:122-164`、`378-405`；`vendor/solo-memory/Sources/SoloMemoryService/main.swift:44-53,160-170` |
| 原生齿轮/返回 | `../bridge-app/app/src/main/res/layout/activity_main.xml:14-31`；`../bridge-app/app/src/main/java/com/example/bridge/MainActivity.java:748-790` |
| 正式轮次 | `docs/FORMAL-30-ROUND-PLAN-20261113.md`、`reports/sctg/FORMAL-RUN-STATE.json`、`reports/sctg/ROUND-MAP.md` |
| 监控台 | `docs/MONITORING-DASHBOARD-PLAN.md`、`lib/panel/monitor-*.js`、`lib/local-io.mjs` 的 `STATIC` map |


---

## 12. I6 修订：无按钮静默预加载 + 最近 200 条离线持久化

> 维护者补充原话：
> “如果静默预加载，按钮就可以直接回收不要了，而且最近两百条消息需要持久化，也就是就算断网了，关闭前的最后200条消息也需要可查”

### 12.1 决策

1. **删除手动按钮**
   - 移除 `sim/index.html` 的 `#load-older` 按钮及“更早 500/200”文案。
   - `renderHistory` 不再根据 `historyHasMore` 显示按钮。
   - 历史加载只由滚动压力位/速度触发。
2. **静默预加载**
   - `OLDER_PAGE_SIZE=200`。
   - 压力位：距顶部约 1.5 屏；快速上滑：约 40 条/秒时提前到约 2.5 屏。
   - 单飞 + `seq`/`AbortController`；同一 `before` 不重复请求。
   - 小 spinner 只在请求 >350ms 或已到绝对顶部时出现；正常网络无感。
   - 无更多历史时只在顶部显示轻量“已到最早”，不做按钮。
3. **最近 200 条本地持久化**
   - 新模块：`sim/message-cache.js`。
   - 存储：IndexedDB；不可用/配额失败时降级为内存，并明确提示“本次会话可查”。
   - 作用域：按 `chatId + mode` 隔离。
   - 上限：每个会话最近 200 条；全局建议上限 2000 条，LRU 淘汰。
   - 内容：消息 id/role/text/ts/附件元数据；不缓存大二进制。
   - 写入：首屏历史、新消息、SSE 更新后 debounce 写入；`message id` 去重。
   - 启动：先 hydrate 本地 200 条并渲染，再请求服务端；离线时保留缓存并显示“离线缓存 · 最近 200 条”。
   - 搜索：离线只搜本地 200 条，必须显示范围提示；在线仍走服务端全量。
   - 重连：本地缓存与服务端历史按 `message id` 合并去重，不重复、不跳位。
4. **隐私边界**
   - 缓存只在本机 origin storage；不上传、不写日志、不提交原始缓存/截图/正文。
   - 清除 App 数据/缓存时一并清除；建议后续增加“清除离线缓存”入口。

### 12.2 代码落点

| 文件 | 作用 |
|---|---|
| `sim/index.html` | 删除 `#load-older` 按钮 |
| `sim/app.js` | 移除按钮逻辑；滚动预加载；hydrate/写入/合并缓存；离线搜索 fallback |
| `sim/styles.css` | 顶部 spinner、离线缓存标识、无按钮后的历史顶部状态 |
| `sim/message-cache.js` | IndexedDB 适配器、200 条裁剪、合并去重、搜索、LRU |
| `test/history-preload.test.mjs` | 压力位/速度/单飞/去重/滚动锚定 |
| `test/offline-cache.test.mjs` | 200 条上限、淘汰、断网 hydrate、离线搜索、重连合并、IndexedDB 降级 |

### 12.3 建议拆轮

- **U2a**：删除手动按钮 + 静默预加载 + 单飞去重 + spinner 阈值 + 滚动锚定。
- **U2b**：IndexedDB 最近 200 条 + 启动 hydrate + 离线查看/搜索 + 重连去重合并 + 降级策略。
- 两轮都写 `sim/app.js`，必须串行；U2b 依赖 U2a 的滚动/历史状态模型。

### 12.4 验收清单

- [ ] 聊天页不再出现“更早 200/更早 500”手动按钮。
- [ ] 快速上滑/压力位自动静默预加载；正常网络无 spinner。
- [ ] spinner 只在请求 >350ms 或绝对顶部出现；失败可重试。
- [ ] 关闭页面/断网后重新打开，最近 200 条消息仍可查看。
- [ ] 离线搜索只查缓存 200 条，并显示“离线缓存 · 最近 200 条”范围提示。
- [ ] 新消息超过 200 条时淘汰最旧；缓存总量有上限。
- [ ] 重连后本地缓存与服务端历史按 id 去重合并，无重复/无跳位。
- [ ] 会话切换隔离缓存；旧响应/旧缓存不串会话。
- [ ] IndexedDB 不可用/写失败时降级内存可见，不阻塞聊天。
- [ ] R06/R20 滚动/键盘回归通过。
