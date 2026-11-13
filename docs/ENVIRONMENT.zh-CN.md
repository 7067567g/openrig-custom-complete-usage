[English](ENVIRONMENT.md) | **简体中文**

# 环境

## local-only 需要

- Python 3.11+
- `pip install -r requirements-dev.txt`
- Git

## hybrid OpenRig 需要

- Node.js 24
- OpenRig CLI（`rig`）
- 已配置的 OpenCode 和/或 DSH seat
- 每个 run 独立的 `OPENRIG_HOME` 和 daemon 端口

## 可选

- `bwrap` / 容器用于 benchmark 隔离
- `gh` CLI 用于发布自动化

## 冒烟

```bash
make check
make doc
make test
make render-dry
```

`make smoke` 需要 `rig`，会渲染三个临时 bundle。
