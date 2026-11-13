#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless CLI delegation adapter for opencode v2 and DSH.

The canonical workflow used to depend on opencode v1's synchronous HTTP API.
opencode 2.x removed that endpoint. This module keeps a small, testable adapter
surface for the two supported headless CLIs:

- opencode: ``opencode run --format json --auto ... <brief>``
- dsh:      ``dsh --profile headless --json -`` with brief on stdin

It intentionally does NOT start a server or write workflow documents. It only
builds the command, runs it, parses the JSONL event stream into the same result
shape used by ``wf.py``'s v1 delegation path, and returns it to the caller.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

BACKENDS = ("v2-cli", "dsh")


def _binary(explicit: str | None, default: str) -> str:
    if explicit:
        return explicit
    return shutil.which(default) or default


def build_command(
    backend: str,
    brief: str,
    model: str = "",
    session_id: str = "",
    binary: str | None = None,
) -> tuple[list[str], str | None]:
    """Return (argv, stdin_text). ``stdin_text`` is None for argv prompts."""
    if backend == "v2-cli":
        exe = _binary(binary or os.environ.get("OPENCODE_BIN"), "opencode")
        cmd = [exe, "run", "--format", "json", "--auto"]
        if model:
            cmd += ["--model", model]
        if session_id:
            cmd += ["--session", session_id]
        cmd.append(brief)
        return cmd, None
    if backend == "dsh":
        exe = _binary(binary or os.environ.get("DSH_BIN"), "dsh")
        cmd = [exe, "--profile", "headless", "--json"]
        if session_id:
            cmd += ["--session-id", session_id]
        cmd.append("-")
        return cmd, brief
    raise ValueError(f"unknown headless backend: {backend}")


def _empty_summary() -> dict[str, Any]:
    return {
        "session_id": "",
        "final": "",
        "turns": 0,
        "steps": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "total_tokens": 0,
        "event_count": 0,
        "event_types": {},
        "error": "",
    }


def parse_opencode_events(raw: str) -> dict[str, Any]:
    """Parse ``opencode run --format json`` JSONL events."""
    out = _empty_summary()
    texts: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        out["event_count"] += 1
        kind = str(event.get("type") or "unknown")
        out["event_types"][kind] = out["event_types"].get(kind, 0) + 1
        part = event.get("part") if isinstance(event.get("part"), dict) else {}
        if not out["session_id"]:
            out["session_id"] = str(event.get("sessionID") or part.get("sessionID") or "")
        if kind == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                texts.append(text)
        if kind in ("step_start", "step_finish"):
            out["steps"] += 1
        usage = event.get("tokens") or part.get("tokens") or event.get("usage")
        if isinstance(usage, dict):
            out["input_tokens"] += int(usage.get("input") or usage.get("inputTokens") or 0)
            out["output_tokens"] += int(usage.get("output") or usage.get("outputTokens") or 0)
            cache = usage.get("cache")
            if isinstance(cache, dict):
                out["cache_read_tokens"] += int(cache.get("read") or 0)
            elif usage.get("cacheReadTokens"):
                out["cache_read_tokens"] += int(usage["cacheReadTokens"])
        if kind == "error":
            detail = event.get("error") or part.get("error") or event
            out["error"] = (out["error"] + "\n" + str(detail))[:2000]
    out["final"] = "\n".join(texts).strip()
    out["turns"] = 1 if out["final"] else 0
    out["total_tokens"] = out["input_tokens"] + out["output_tokens"] + out["cache_read_tokens"]
    return out


def parse_dsh_events(raw: str) -> dict[str, Any]:
    """Parse ``dsh --profile headless --json`` JSONL events."""
    out = _empty_summary()
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            out["error"] = (out["error"] + " | " if out["error"] else "") + line[:200]
            continue
        if not isinstance(event, dict):
            continue
        out["event_count"] += 1
        kind = str(event.get("type") or "unknown")
        out["event_types"][kind] = out["event_types"].get(kind, 0) + 1
        if kind == "session":
            out["session_id"] = str(event.get("sessionId") or event.get("sessionID") or "")
        elif kind == "final":
            out["final"] = str(event.get("text") or "")
        elif kind == "status":
            phase = event.get("phase")
            if phase == "turn_end":
                out["turns"] += 1
            elif phase == "step_end":
                out["steps"] += 1
                usage = event.get("usage") or {}
                out["input_tokens"] += int(usage.get("inputTokens") or 0)
                out["output_tokens"] += int(usage.get("outputTokens") or 0)
                out["cache_read_tokens"] += int(usage.get("cacheReadTokens") or 0)
                out["total_tokens"] += int(usage.get("totalTokens") or 0)
    if not out["total_tokens"]:
        out["total_tokens"] = out["input_tokens"] + out["output_tokens"] + out["cache_read_tokens"]
    return out


def parse_events(backend: str, raw: str) -> dict[str, Any]:
    if backend == "v2-cli":
        return parse_opencode_events(raw)
    if backend == "dsh":
        return parse_dsh_events(raw)
    raise ValueError(f"unknown headless backend: {backend}")


def run(
    backend: str,
    brief: str,
    model: str = "",
    session_id: str = "",
    timeout: int = 900,
    cwd: Path | str | None = None,
    heartbeat: int = 0,
    binary: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Execute one headless delegation and return a wf-compatible result dict."""
    cmd, stdin_text = build_command(backend, brief, model, session_id, binary)
    started = time.time()
    box: dict[str, Any] = {}

    def _run() -> None:
        try:
            box["proc"] = subprocess.run(
                cmd,
                input=stdin_text,
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=str(cwd) if cwd else None,
                env={**os.environ, **(env or {})},
            )
        except subprocess.TimeoutExpired as exc:
            box["timeout"] = exc
        except BaseException as exc:  # noqa: BLE001
            box["error"] = exc

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    interval = heartbeat if isinstance(heartbeat, (int, float)) and heartbeat > 0 else 0
    while th.is_alive():
        th.join(timeout=interval or None)
        if interval and th.is_alive():
            print(f"[HEARTBEAT] headless {backend} 已等待 {int(time.time() - started)}s", flush=True)
    if "error" in box:
        raise box["error"]
    timed_out = "timeout" in box
    proc = box.get("proc")
    raw = ""
    err = ""
    code = 124
    if timed_out:
        exc = box["timeout"]
        raw = exc.stdout if isinstance(exc.stdout, str) else ""
        err = exc.stderr if isinstance(exc.stderr, str) else ""
    elif proc is not None:
        raw, err, code = proc.stdout or "", proc.stderr or "", proc.returncode
    parsed = parse_events(backend, raw)
    if err and not parsed.get("error"):
        parsed["error"] = err[-2000:]
    result = {
        "backend": backend,
        "sid": parsed.get("session_id") or session_id or "-",
        "text": parsed.get("final") or "",
        "tokens": {
            "input": parsed.get("input_tokens", 0),
            "output": parsed.get("output_tokens", 0),
            "cache": {"read": parsed.get("cache_read_tokens", 0)},
            "total": parsed.get("total_tokens", 0),
        },
        "cost": None,
        "dt": time.time() - started,
        "model": model if backend == "v2-cli" else "dsh/default",
        "oc_agent": "",
        "exit_code": code,
        "timed_out": timed_out,
        "stderr_tail": "\n".join(err.splitlines()[-5:]),
        "raw_events": parsed,
        "command": cmd[:-1] + ["<BRIEF>"] if backend == "v2-cli" else cmd,
    }
    return result
