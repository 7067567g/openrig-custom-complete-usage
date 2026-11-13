[English](LIMITATIONS.md) | **简体中文**

# 限制

- 本仓库是**使用例**，不是生产控制面。
- 默认验证不声称完成真实 5-seat E2E。
- `rig workflow validate` 和 `rig up --plan` 验证 spec，不验证模型质量。
- live run 需要配置好的 OpenCode/DSH seat 和独立 OpenRig home。
- SCTG gate 检查结构、范围、证据和可复现性，不检查语义正确性。
- 跨仓库混用不同版本模板/roles 不受支持，除非发布说明明确列出。
