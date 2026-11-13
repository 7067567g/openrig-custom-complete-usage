# -*- coding: utf-8 -*-
"""Canonical headless delegation adapter regression (opencode v2 / DSH)."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import wf  # noqa: E402
from adapters import headless  # noqa: E402


def test_opencode_command_shape_without_server():
    cmd, stdin = headless.build_command(
        "v2-cli", "BRIEF", model="opencode-go/deepseek-flash", session_id="ses_1"
    )
    assert cmd[1:4] == ["run", "--format", "json"]
    assert "--auto" in cmd
    assert "--model" in cmd and "opencode-go/deepseek-flash" in cmd
    assert "--session" in cmd and cmd[cmd.index("--session") + 1] == "ses_1"
    assert cmd[-1] == "BRIEF"
    assert stdin is None


def test_dsh_command_shape_uses_stdin():
    cmd, stdin = headless.build_command("dsh", "BRIEF", session_id="ses_2")
    assert cmd[1:4] == ["--profile", "headless", "--json"]
    assert cmd[-1] == "-"
    assert "--session-id" in cmd and cmd[cmd.index("--session-id") + 1] == "ses_2"
    assert stdin == "BRIEF"


def test_parse_opencode_jsonl_events():
    raw = "\n".join(
        [
            json.dumps({"type": "step_start", "sessionID": "ses_1"}),
            json.dumps({"type": "text", "part": {"text": "OK"}}),
            json.dumps(
                {
                    "type": "step_finish",
                    "tokens": {"input": 10, "output": 2, "cache": {"read": 3}},
                }
            ),
        ]
    )
    s = headless.parse_events("v2-cli", raw)
    assert s["session_id"] == "ses_1"
    assert s["final"] == "OK"
    assert s["steps"] == 2
    assert (s["input_tokens"], s["output_tokens"], s["cache_read_tokens"]) == (10, 2, 3)


def test_parse_dsh_jsonl_events():
    raw = "\n".join(
        [
            json.dumps({"type": "session", "sessionId": "ses_d"}),
            json.dumps({"type": "final", "text": "DONE"}),
            json.dumps(
                {
                    "type": "status",
                    "phase": "step_end",
                    "usage": {"inputTokens": 5, "outputTokens": 4, "totalTokens": 9},
                }
            ),
        ]
    )
    s = headless.parse_events("dsh", raw)
    assert s["session_id"] == "ses_d"
    assert s["final"] == "DONE"
    assert s["steps"] == 1
    assert s["input_tokens"] == 5 and s["output_tokens"] == 4


def _fake_cli(tmp_path: Path, backend: str) -> Path:
    p = tmp_path / ("fake-oc" if backend == "v2-cli" else "fake-dsh")
    if backend == "v2-cli":
        body = r'''#!/usr/bin/env python3
import json
print(json.dumps({"type":"step_start","sessionID":"sess-cli"}))
print(json.dumps({"type":"text","part":{"text":"CLI-OK"}}))
print(json.dumps({"type":"step_finish","tokens":{"input":7,"output":2,"cache":{"read":1}}}))
'''
    else:
        body = r'''#!/usr/bin/env python3
import json,sys
_ = sys.stdin.read()
print(json.dumps({"type":"session","sessionId":"sess-dsh"}))
print(json.dumps({"type":"final","text":"DSH-OK"}))
print(json.dumps({"type":"status","phase":"step_end","usage":{"inputTokens":3,"outputTokens":2,"totalTokens":5}}))
'''
    p.write_text(body, encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return p


@pytest.mark.parametrize("backend", ["v2-cli", "dsh"])
def test_adapter_run_executes_and_returns_wf_shape(tmp_path, backend):
    exe = _fake_cli(tmp_path, backend)
    res = headless.run(backend, "hello", timeout=10, binary=str(exe), cwd=tmp_path)
    assert res["backend"] == backend
    assert res["exit_code"] == 0
    assert res["text"] in ("CLI-OK", "DSH-OK")
    assert res["tokens"]["input"] > 0
    assert res["sid"].startswith("sess-")


def test_resolve_backend_auto_prefers_v2(monkeypatch):
    monkeypatch.setattr(wf, "_oc_cli_version", lambda binary=None: (2, "opencode v2.0.32"))
    assert wf._resolve_delegate_backend("auto") == "v2-cli"
    monkeypatch.setattr(wf, "_oc_cli_version", lambda binary=None: (1, "opencode 1.19.3"))
    assert wf._resolve_delegate_backend("auto") == "v1-http"


def test_delegate_dry_run_headless_never_starts_server(new_run, monkeypatch, capsys):
    rd = new_run(run_id="t-headless-dry")
    wf.write_header_field(rd / "PROJECT.md", "state", "plan-ready")

    def _boom(*a, **k):
        raise AssertionError("dry-run must not start a server")

    monkeypatch.setattr(wf, "serve_start", _boom)
    args = argparse.Namespace(
        run_id="t-headless-dry",
        role="pmo",
        name="pmo",
        ws="",
        model="opencode-go/deepseek-flash",
        oc_agent="minimal",
        backend="v2-cli",
        server="",
        port=0,
        timeout=30,
        heartbeat=1,
        dry_run=True,
        force=False,
    )
    wf.cmd_delegate(args)
    out = capsys.readouterr().out
    assert "backend=v2-cli" in out
    assert "opencode run --format json" in out
    assert "PASS" not in out
