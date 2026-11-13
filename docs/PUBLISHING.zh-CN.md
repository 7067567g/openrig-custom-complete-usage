[English](PUBLISHING.md) | **简体中文**

# 发布策略

本仓库是**脱敏后的完整使用例**，不是内部运行数据导出。

## 包含

- workflow 合同、roles、templates、scripts；
- OpenRig render/preflight/bridge 工具；
- 最小示例、多轮示例、脱敏样例；
- 测试和文档。

## 不包含

- 真实 `runs/` 数据和 transcript；
- API key、token、cookie、`.dsh` 凭证；
- 个人绝对路径；
- 内部 dashboard、monitor target、systemd unit；
- 内部项目名和 snapshot；
- 不可再分发的 benchmark 题面。

## 发布前检查

```bash
python3 scripts/check_repo.py
python3 scripts/check_content.py
make doc
make test
make render-dry
```
