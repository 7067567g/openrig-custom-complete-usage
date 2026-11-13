#!/usr/bin/env bash
# 运行 workflow-group 测试。优先使用 .venv；离线环境可回退到系统 pytest。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "缺少 $PY；请先创建 venv 并安装 requirements-dev.txt" >&2
  exit 2
fi
if ! "$PY" -c 'import pytest' >/dev/null 2>&1; then
  export PYTHONPATH="/usr/lib/python3/dist-packages:${PYTHONPATH:-}"
fi
exec "$PY" -m pytest "$ROOT/tests" "$@"
