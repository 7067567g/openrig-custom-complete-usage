# QUIET-200 · 实现形式分析 Brief

- 代号：QUIET-200
- 分支：`feat/quiet-200`
- 分叉自：`remediation/20261113` @ `280de358eecc9444af697d83aadb04ad60c58478`
- 分叉时间：2026-11-13T23:52:50+08:00
- 最终主链：`main`
- 短期收敛目标：`remediation/20261113`
- 当前轮：只分析实现形式，不写产品代码。

## 需求（已拍板）

1. 删除聊天历史“更早 200/500”手动按钮。
2. 滚动压力位/快速上滑静默预加载更早历史；spinner 只在预加载跟不上时出现。
3. 按会话本地持久化最近 200 条消息（IndexedDB；不可用降级内存）。
4. 断网/关闭/重启后最近 200 条可查看、可搜索；明确“离线缓存”范围。
5. 重连后本地缓存与服务端历史按 message id 去重合并。
6. 缓存每会话 200 条，全局建议 2000 条 LRU；不缓存大二进制。

## 现有代码与文档

- `bridge repo/docs/branches/QUIET-200.md`（支线元数据/收敛门）
- `bridge repo/reports/issues/SIX-ISSUES-INTAKE-20261113.md` §12
- `bridge repo/reports/issues/SIX-ISSUES-INTAKE-20261113.json` 的 I6/U2
- `bridge repo/sim/app.js`（loadHistory/loadOlder/renderHistory/scroll/search）
- `bridge repo/sim/index.html`（load-older 按钮）
- `bridge repo/sim/styles.css`
- `bridge repo/test/app-ui-fixes.test.mjs`

## 本轮必须回答

1. U2a/U2b 的实现形态：新增模块、函数签名、状态机、数据流；
2. 静默预加载的滚动采样、压力位、速度阈值、单飞/seq/取消、滚动锚定；
3. IndexedDB schema/version/key/index、200 条裁剪、全局 LRU、hydrate/merge/search/降级；
4. 与现有 `loadHistory/renderHistory/SSE/搜索/会话切换` 的接入点；
5. 测试策略：纯函数、fake storage、DOM/滚动模拟、真机验收；
6. U2a/U2b 拆轮、write scope、依赖与冲突；
7. QUIET-200 收敛回 remediation 的门禁与合并步骤；
8. 未决问题/风险，明确哪些需要 MAIN 拍板。

## 输出

- `bridge repo/reports/issues/QUIET-200-IMPLEMENTATION-PLAN.md`
- `bridge repo/reports/issues/QUIET-200-IMPLEMENTATION-PLAN.json`

约束：只读代码，不改产品代码；不提交原始截图/聊天正文；不改变分支。
