# -*- coding: utf-8 -*-
"""WS-2：`scripts/wf.py` opencode v1 HTTP 版本守卫单测。

背景：本机 opencode 为 v2.x，v1 端点 `POST /session` 返回 405；旧实现
`serve_start` 会把预热失败吞成 `[WARN]` 并 rc=0，`delegate` 则可能进入
405 重试/失败循环。守卫要求：真正走 HTTP 前探测版本，2.x/未知版本
**rc=1 + 一行可执行提示**；`--dry-run` 不经过 HTTP，不受影响。

本文件按 conftest.py 的边界说明**不依赖** WS-1 的夹具；所有用例离线，
用临时 shell stub 模拟 `opencode --version` 输出，不启动真实服务。
"""

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import wf  # noqa: E402


# ------------------------------------------------------------------ helpers
def _stub(tmp_path, body, name="opencode"):
    p = tmp_path / name
    p.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    p.chmod(0o755)
    return p


def _version_stub(tmp_path, text, rc=0):
    return _stub(tmp_path, f"echo '{text}'\nexit {rc}\n")


# ================================================================ 版本探测
@pytest.mark.parametrize(
    "raw,major",
    [
        ("1.18.4", 1),
        ("opencode v1.0.0", 1),
        ("2.0.32", 2),
        ("opencode v2.0.32", 2),
        ("10.1.2", 10),
    ],
)
def test_parse_major(tmp_path, raw, major):
    binary = _version_stub(tmp_path, raw)
    got, detail = wf._oc_cli_version(binary)
    assert got == major
    assert raw in detail


def test_parse_missing_binary(tmp_path):
    got, detail = wf._oc_cli_version(tmp_path / "definitely-missing")
    assert got is None
    assert "未找到可执行文件" in detail


def test_parse_nonzero_exit(tmp_path):
    binary = _version_stub(tmp_path, "boom", rc=3)
    got, detail = wf._oc_cli_version(binary)
    assert got is None
    assert "退出码 3" in detail


def test_parse_unrecognized_output(tmp_path):
    binary = _version_stub(tmp_path, "not-a-version")
    got, detail = wf._oc_cli_version(binary)
    assert got is None
    assert "无法识别版本输出" in detail


# ================================================================ 快速失败
def test_v1_passes_guard(tmp_path):
    binary = _version_stub(tmp_path, "1.18.4")
    # 不抛 SystemExit 即通过
    assert wf.require_v1_http("unit", binary=binary) is None


def test_v2_fails_guard_with_actionable_hint(tmp_path, capsys):
    binary = _version_stub(tmp_path, "2.0.32")
    with pytest.raises(SystemExit) as exc:
        wf.require_v1_http("serve start", binary=binary)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "不支持 v1 HTTP API（serve start）" in err
    assert "opencode run" in err
    assert "OPENCODE_BIN" in err
    # 一行提示：只输出一行 [ERROR]
    assert len([ln for ln in err.splitlines() if ln.strip()]) == 1


def test_unknown_version_fails_closed(tmp_path, capsys):
    binary = _version_stub(tmp_path, "not-a-version")
    with pytest.raises(SystemExit) as exc:
        wf.require_v1_http("delegate/squad", binary=binary)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "版本守卫失败（delegate/squad）" in err
    assert "OPENCODE_BIN" in err


# ================================================================ 入口接线
def test_serve_start_blocks_before_writing_state(tmp_path, monkeypatch, capsys):
    """v2 时 serve_start 必须在启动/写 state 之前退出（不进入 405 预热）。"""
    binary = _version_stub(tmp_path, "2.0.32")
    monkeypatch.setattr(wf, "OC_BIN", str(binary))
    state = tmp_path / ".opencode-server.json"
    log = tmp_path / ".opencode-server.log"
    monkeypatch.setattr(wf, "SERVER_STATE", state)
    monkeypatch.setattr(wf, "SERVER_LOG", log)

    with pytest.raises(SystemExit) as exc:
        wf.serve_start(port=0)
    assert exc.value.code == 1
    assert not state.exists(), "守卫失败时不应写 server state"
    assert not log.exists(), "守卫失败时不应创建 server log"
    assert "不支持 v1 HTTP API（serve start）" in capsys.readouterr().err


def test_resolve_base_default_path_fails_via_serve_start(tmp_path, monkeypatch, capsys):
    """delegate/squad 默认自动拉起服务 → 仍经 serve_start 守卫失败（不另加守卫）。"""
    binary = _version_stub(tmp_path, "2.0.32")
    monkeypatch.setattr(wf, "OC_BIN", str(binary))
    with pytest.raises(SystemExit) as exc:
        wf._resolve_base("", 0)
    assert exc.value.code == 1
    assert "不支持 v1 HTTP API（serve start）" in capsys.readouterr().err


def test_serve_start_launches_configured_opencode_bin(tmp_path, monkeypatch, capsys):
    """OPENCODE_BIN 必须同时用于版本探测和实际 serve launch，不能只影响探测。"""
    binary = _version_stub(tmp_path, "1.18.4")
    monkeypatch.setattr(wf, "OC_BIN", str(binary))
    # 先隔离版本探测，专注验证实际 launch 是否使用同一个可配置二进制。
    monkeypatch.setattr(wf, "require_v1_http", lambda *args, **kwargs: None)
    monkeypatch.setattr(wf, "SERVER_STATE", tmp_path / ".opencode-server.json")
    monkeypatch.setattr(wf, "SERVER_LOG", tmp_path / ".opencode-server.log")
    called = []

    class FakeProc:
        pid = 424242

        def poll(self):
            return None

    def fake_popen(cmd, **kwargs):
        called.append(list(cmd))
        Path(wf.SERVER_LOG).write_text(
            "server listening on http://127.0.0.1:54321\n", encoding="utf-8"
        )
        return FakeProc()

    monkeypatch.setattr(wf.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(wf, "api", lambda *args, **kwargs: {})

    state = wf.serve_start(port=0, wait=1)

    assert called, "serve_start should launch a process after a v1 version probe"
    assert called[0][0] == str(binary), "serve launch ignored OPENCODE_BIN"
    assert called[0][1:4] == ["serve", "--port", "0"]
    assert state["url"] == "http://127.0.0.1:54321"
