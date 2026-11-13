# the assistant project 监控台 · Round 2 构建报告

- 日期：2026-11-13
- 状态：PASS（demo/组件库/路由/测试）
- 轮次：`example-monitor-round2-20261113`
- 设计依据：`docs/MONITORING-DASHBOARD-PLAN.md`

## 1. 交付文件

新增：

- `lib/panel/monitor-components.js`
- `lib/panel/monitor-data.js`
- `lib/panel/monitor.html`
- `lib/panel/monitor.css`
- `lib/panel/monitor.js`
- `test/monitor-components.test.mjs`

修改：

- `lib/local-io.mjs`：新增 `/monitor*` 静态路由
- `lib/panel/index.html`：新增“打开监控台”入口
- `docs/MONITORING-DASHBOARD-PLAN.md`：补充 Round 2 落地记录/接入示例/残余项

## 2. 接口

固定数据契约：`example-monitor/v1`。

```text
{
  schema, title, meta,
  sections: [{ id, title, layout, widgets: [...] }]
}
```

固定浏览器接缝：

```js
ExampleMonitor.render(container, model, options?)
ExampleMonitor.registerWidget(type, renderer)
ExampleMonitor.registerDataSource(name, factory)
ExampleMonitor.updateWidget(id, patch, container?)
```

数据源固定接口：

```js
{ load(): Promise<model>, subscribe?(cb): unsubscribe }
```

内置适配器：`createStaticSource`、`createHttpSource`。

## 3. 组件

stat/KPI、status badge、progress、gauge、sparkline、line、area、bar、donut、table、
key-value、timeline、alert、heatmap、text（纯文字框）、empty、error、loading。

实现原则：

- 无 CDN / 无第三方图表库
- 用户可见文本一律 `textContent`，不接受 HTML
- 未知 widget 渲染安全占位，不 throw
- 自定义 renderer 抛错降级为 error 卡
- 固定 `monitor-*` class 与 `--monitor-*` CSS token
- 移动优先，表格横向滚动，无 hover 依赖

## 4. 测试结果

| 命令 | 结果 |
|---|---|
| `node --test test/monitor-components.test.mjs` | 18/18 PASS |
| `node --test test/local-io-app.test.mjs` | 5/5 PASS |
| `node --test test/graft-ui/panel.test.mjs` | 2/2 PASS |
| `node --check lib/panel/monitor.js lib/panel/monitor-components.js lib/panel/monitor-data.js` | PASS |
| 临时静态服务 `GET /monitor.html` | 200 |
| headless Chrome 渲染 `monitor.html` | 成功，全部 demo 组件可见 |

测试覆盖：

- 模型结构校验与非法结构拒绝
- 未知 widget 安全降级
- 全内置类型渲染不抛错
- 自定义 widget 注册/替换/非法注册
- 自定义 renderer 抛错降级
- 文本转义、危险 href 拒绝
- `updateWidget` id/type 不可篡改
- static/HTTP data source
- 不内置后端地址、不读 token
- `/monitor*` route、HTML、面板入口源契约

## 5. 残余项

- 未接真实监控后端，demo 使用示例数据。
- 未重启 live `dsh-app.service` 做线上 route 验证。
- 未做真机滚动/手势验收。
- 后续接入只需替换 data source；固定组件库和样式不需要改。

## 6. 证据

- `reports/monitor/previews/`（demo 页 headless Chrome 预览图，示例数据，无真实监控数据）
- `docs/MONITORING-DASHBOARD-PLAN.md`

## 7. OpenRig 轻量运行记录

- Rig：`monitor-lite`（1 个 builder seat，`main-builder@monitor-lite`；dsh runtime）
- Round 1 instance：`01M7AHVWAZAT649RD2BQRG39HD`（completed）
- Round 2 instance：`01M7AJAF5G7Q04E77PZV86BNMP`（completed）
- 收口快照：`01M7AJRN8Y9KHTFFCNAVQCTWEE`
- 工作完成后已 `rig down monitor-lite --snapshot`，seat 进程已退出，释放约 0.6GB RSS；需要继续时用 `rig up monitor-lite --existing` 恢复。

运行备注：seat 在写出文件后 turn 长时间未收口，Lead 按已完成文件 + 本地测试 + headless Chrome 渲染结果人工收口；代码/测试由 seat 产出，收口结论已复验。
