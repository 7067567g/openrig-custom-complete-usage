[English](01-render-smoke.md) | **简体中文**

# 案例 01 — 渲染与 bridge 冒烟（12 轮）

## 问题

完整使用例能否在多轮渲染中稳定生成 OpenRig bundle，且不泄漏测试/oracle 状态、
不手改生成文件？

## 方法

连续 12 轮：

1. 每轮唯一 run id 和 daemon 端口；
2. 跑 `openrig_bridge.py doctor`；
3. 跑 `rig workflow validate`；
4. 跑 `rig up --plan`。

## 结果

```text
12/12 render                 PASS
12/12 bridge doctor          PASS
12/12 workflow validate      ok=true（7 steps，预期 warning）
12/12 rig up --plan          status=planned（5 seats resolved）
```

## 证明了什么

- 相同输入下模板渲染稳定；
- bridge schema 在不同 run id/端口下稳定；
- workflow spec 能被本地 OpenRig CLI 接受；
- 这一层不需要 live seat。

## 没有证明什么

- live 模型质量或 token/成本；
- seat 就绪或 transcript 投递；
- 真实 5-seat E2E 通过。

详见 `VALIDATION.zh-CN.md` 和 `reports/openrig_smoke.md`。
