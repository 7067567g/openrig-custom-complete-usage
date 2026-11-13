[English](README.md) | **简体中文**

# Benchmark 模块

这是**机制冒烟 harness**，不是模型 benchmark。它的作用是让仓库先有一个真实、
可运行的 benchmark 接口，完整 raw-vs-SCTG 模型 harness 后续再补。

```text
benchmark/
  harness/run_benchmark.py   复制 task workspace -> 跑 arm -> verify -> JSON/MD
  arms.example.yaml          替换成真实 workflow launcher
  tasks/synthetic-v1/        合成、可再分发的 task pack
  results/                   生成的冒烟结果
```

运行：

```bash
python3 benchmark/harness/run_benchmark.py
```

它证明：任务隔离、arm 执行、验证、结果采集。
它不证明：模型质量、token/成本、raw-vs-SCTG 性能。

完整 harness（模型 arm、local judge、sandbox、preflight audit）仍列在
`reports/content_gap_audit.zh-CN.md` 的 P0 缺口。
