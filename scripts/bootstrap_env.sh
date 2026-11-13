#!/usr/bin/env bash
# 初始化 workflow-group 本地环境：Python 3.12 venv + 开发依赖。
# 有网络时：uv pip install -r requirements-dev.txt
# 离线时：脚本会保留诊断信息；scripts/test.sh 可回退系统 pytest。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"

if [ ! -x "$PY" ]; then
  if command -v uv >/dev/null 2>&1; then
    uv venv --python 3.12 "$ROOT/.venv"
  else
    python3 -m venv "$ROOT/.venv"
  fi
fi

if ! "$PY" -c 'import openpyxl' >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    uv pip install --python "$PY" -r "$ROOT/requirements-dev.txt" || {
      echo "[WARN] 依赖安装失败（可能无网络）；可稍后运行：uv pip install --python $PY -r $ROOT/requirements-dev.txt" >&2
    }
  else
    "$PY" -m ensurepip >/dev/null 2>&1 || true
    "$PY" -m pip install -r "$ROOT/requirements-dev.txt" || {
      echo "[WARN] 依赖安装失败（可能无网络）；请手动安装 requirements-dev.txt" >&2
    }
  fi
fi

echo "[OK] Python: $PY"
"$PY" -c 'import sys; print(sys.version)' || true
"$PY" -c 'import openpyxl; print("openpyxl", openpyxl.__version__)' 2>/dev/null || echo "[WARN] openpyxl 不可用"
"$PY" -m pytest --version 2>/dev/null || echo "[WARN] pytest 不可用；scripts/test.sh 会尝试回退系统 pytest"
