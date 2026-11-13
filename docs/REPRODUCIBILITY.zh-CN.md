[English](REPRODUCIBILITY.md) | **简体中文**

# 可复现性

## 确定性

- 相同输入和 master 版本下的模板渲染；
- `OPENRIG-BRIDGE.json` schema 和 bundle 相对路径；
- `doc_consistency.py --check`；
- workflow/adapter 测试；
- 仓库卫生检查。

## 非确定性

- 真实模型输出和 token/成本；
- seat 就绪时间和时序；
- OpenRig daemon/session 状态。

SCTG 不承诺模型输出确定；它承诺事务可复现：card、submission、gate result、
evidence hashes、decision records，以及控制面到执行面的 bridge。
