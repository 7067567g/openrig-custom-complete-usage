[English](README.md) | **简体中文**

# SCTG 最小示例

参考 kit 位于 `sctg-kit/`，包含 task-card runner、四个 gate、submission schema、
decision helper 和 ledger helper。

```bash
python3 sctg-kit/sctg.py --help
```

完整公开 kit 文档和最小 demo 见
[`SCTG-public`](https://github.com/7067567g/SCTG-public)。

## 可运行 demo

```bash
python3 examples/sctg-minimal/run_demo.py
```

它会创建临时 card、submission、evidence，并跑四个 gate。
