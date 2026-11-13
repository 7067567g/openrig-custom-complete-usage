[English](VERSIONING.md) | **简体中文**

# 版本管理

## 规则

语义化版本：`MAJOR.MINOR.PATCH`。

- `MAJOR`：不兼容的 workflow/contract 变更；
- `MINOR`：新增模板、示例、adapter 或非破坏性工具；
- `PATCH`：文档、修复、测试、兼容性更新。

当前版本：`0.1.7`。

## 发布清单

1. `make check`
2. `make doc`
3. `make test`
4. `make render-dry`
5. `python3 scripts/openrig_smoke.py --rounds 12`
6. 更新 `CHANGELOG.md` 和 `docs/releases/<version>.md`
7. 同步修改 `VERSION` 和 `pyproject.toml`
8. 提交、打 tag `v<version>`、push tag
9. 从 tag 创建 GitHub release

## 两仓兼容

| 仓库 | 角色 |
|---|---|
| `SCTG-public` | 稳定 reference kit |
| `openrig-custom-complete-usage` | 完整操作层使用例 |

两个版本独立演进；发布说明中记录验证过的版本组合。
