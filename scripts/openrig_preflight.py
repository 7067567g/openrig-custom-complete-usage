#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenRig / workflow-group agent preflight.

Usage (agent reads JSON; human can read markdown):
  python3 scripts/openrig_preflight.py --json
  python3 scripts/openrig_preflight.py --run-id X --rig Y --seat a@Y \
    --run-dir .../runs/X --gov-dir .../workspace --job <jobId> --workspace .../workspace --json

It prints the curated preflight, lists reference templates, injects a managed
block into <workspace>/AGENTS.md, and registers the run in the read-only monitor
target file (optional; configure OPENRIG_MONITOR_TARGETS).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "templates" / "specialized" / "openrig-workflow-master" / "PREFLIGHT.md"
TARGET_RAW = os.environ.get("OPENRIG_MONITOR_TARGETS", "")
TARGET_FILE = Path(TARGET_RAW) if TARGET_RAW else None
MONITOR_URL = os.environ.get("OPENRIG_MONITOR_URL", "")

KNOWN_TEMPLATES = [
    ("双平面母版", "templates/specialized/openrig-workflow-master/", "workflow-group 控制面 + OpenRig 多 seat 执行"),
    ("fix-wave", "templates/baseline/fix-wave/BASELINE.md", "缺陷票批量修复，先红后绿"),
    ("ops-hardening", "templates/baseline/ops-hardening/BASELINE.md", "分发/调度/入口可靠性加固"),
    ("refactor-decompose", "templates/baseline/refactor-decompose/BASELINE.md", "先归属冻结，再行为不变重整"),
    ("product-redesign-live", "templates/baseline/product-redesign-live/BASELINE.md", "反目标→设计→staging→live/回滚"),
    ("two-plane-orchestration", "templates/baseline/two-plane-orchestration/BASELINE.md", "双权威、隔离 home/port、QA+join+有界回边"),
    ("原子契约", "templates/contracts/", "strategy/research/diff/architecture/optimize/verify/audit"),
]


def templates() -> list[dict]:
    out = []
    for name, rel, why in KNOWN_TEMPLATES:
        p = ROOT / rel
        out.append({"name": name, "path": str(p), "rel": rel, "why": why, "exists": p.exists()})
    return out


def preflight_text() -> str:
    try:
        return PREFLIGHT.read_text(encoding="utf-8")
    except Exception as e:
        return f"# PREFLIGHT MISSING\n{PREFLIGHT}\n{e}"


def inject_agents(workspace: str, run_id: str = "", monitor_url: str = MONITOR_URL) -> dict:
    if not workspace:
        return {"ok": False, "reason": "no --workspace"}
    root = Path(workspace).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    f = root / "AGENTS.md"
    old = f.read_text(encoding="utf-8") if f.exists() else ""
    block = f"""<!-- BEGIN OPENRIG-PREFLIGHT (managed) -->
## OpenRig preflight — AI 必须先读

- 必读：`{PREFLIGHT}`
- 工作流规则：`{ROOT / 'WORKFLOW.md'}` §1–§7；角色：`{ROOT / 'roles'}/`
- 选型：先查 `{ROOT / 'templates/baseline/REGISTRY.md'}` 和 `{ROOT / 'templates/contracts/README.md'}`；SPEC §0 必须声明 baseline/contracts。
- 机器可读 preflight：`python3 {ROOT / 'scripts/openrig_preflight.py'} --json --run-id {run_id or '<run-id>'}`
- 硬规则：唯一 rig 名 / 一个写权限一个 owner / 先快照 / 不直改 OpenRig DB / 先归档后 teardown / DONE 后必须 stop watchdog。
- 监控台：`{monitor_url}`（新 run 自动注册 target；只读 sidecar，不写治理状态）。
<!-- END OPENRIG-PREFLIGHT (managed) -->"""
    if re.search(r"<!-- BEGIN OPENRIG-PREFLIGHT \(managed\) -->.*?<!-- END OPENRIG-PREFLIGHT \(managed\) -->", old, re.S):
        new = re.sub(r"<!-- BEGIN OPENRIG-PREFLIGHT \(managed\) -->.*?<!-- END OPENRIG-PREFLIGHT \(managed\) -->", block, old, flags=re.S)
    else:
        new = (old.rstrip() + "\n\n" + block + "\n") if old.strip() else block + "\n"
    f.write_text(new, encoding="utf-8")
    return {"ok": True, "file": str(f), "bytes": len(new)}


def register_monitor(args, run_dir: str, gov_dir: str) -> dict:
    if args.no_monitor or TARGET_FILE is None or not MONITOR_URL:
        return {"ok": False, "skipped": "monitor-not-configured"}
    run_id = args.run_id or (Path(run_dir).name if run_dir else "")
    if not run_id:
        return {"ok": False, "reason": "no --run-id"}
    target = {
        "runId": run_id,
        "label": args.label or run_id,
        "rig": args.rig or "",
        "seat": args.seat or "",
        "job": args.job or "",
        "govDir": str(Path(gov_dir).expanduser().resolve()) if gov_dir else "",
        "runDir": str(Path(run_dir).expanduser().resolve()) if run_dir else "",
    }
    try:
        conf = json.loads(TARGET_FILE.read_text(encoding="utf-8")) if TARGET_FILE.exists() else {}
    except Exception:
        conf = {}
    conf.setdefault("targets", {})
    conf["targets"][run_id] = target
    conf["active"] = run_id
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = TARGET_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(conf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, TARGET_FILE)
    started = None
    try:
        started = subprocess.run(
            ["systemctl", "--user", "start", os.environ.get("OPENRIG_MONITOR_SERVICE", "openrig-monitor.service")],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as e:
        started = type("R", (), {"returncode": 1, "stdout": "", "stderr": str(e)})
    return {
        "ok": started.returncode == 0 if started else False,
        "targetFile": str(TARGET_FILE),
        "active": run_id,
        "target": target,
        "monitorUrl": MONITOR_URL,
        "service": os.environ.get("OPENRIG_MONITOR_SERVICE", "openrig-monitor.service"),
        "serviceStartRc": getattr(started, "returncode", None),
        "serviceError": (getattr(started, "stderr", "") or "").strip()[:300],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="")
    ap.add_argument("--rig", default="")
    ap.add_argument("--seat", default="")
    ap.add_argument("--job", default="")
    ap.add_argument("--run-dir", default="")
    ap.add_argument("--gov-dir", default="")
    ap.add_argument("--workspace", default="", help="inject managed AGENTS.md block here")
    ap.add_argument("--label", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--full", action="store_true", help="include full preflight text in JSON")
    ap.add_argument("--no-monitor", action="store_true")
    args = ap.parse_args()

    run_dir = args.run_dir or (str(ROOT / "runs" / args.run_id) if args.run_id else "")
    gov_dir = args.gov_dir or args.workspace
    injected = inject_agents(args.workspace, args.run_id, MONITOR_URL) if args.workspace else None
    monitor = register_monitor(args, run_dir, gov_dir) if (run_dir or args.no_monitor) else None
    text = preflight_text()
    payload = {
        "ok": True,
        "role": "openrig-agent-preflight",
        "runId": args.run_id,
        "rig": args.rig,
        "seat": args.seat,
        "job": args.job,
        "preflightPath": str(PREFLIGHT),
        "workflowPath": str(ROOT / "WORKFLOW.md"),
        "rolesPath": str(ROOT / "roles"),
        "docsContract": ["PROJECT.md", "DECISIONS.md", "STATUS-Round-n.md", "ISSUES.xlsx"],
        "templates": templates(),
        "injectedAgents": injected,
        "monitor": monitor,
        "mandatory": [
            "SPEC.md §0 must declare baseline + contracts",
            "unique rig name / unique workflow id / isolated OPENRIG_HOME",
            "one writer per write scope; no concurrent edits on same file",
            "snapshot and rollback before changing live",
            "do not modify OpenRig SQLite or queue tables directly",
            "workflow progress only through rig workflow project",
            "archive before rig down / daemon stop",
            "write DONE/BLOCKED and stop watchdog when terminal",
        ],
    }
    if args.full:
        payload["preflight"] = text

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(text)
        print("\n## Templates")
        for t in payload["templates"]:
            mark = "OK" if t["exists"] else "MISSING"
            print(f"- [{mark}] {t['name']}: {t['path']}\n  {t['why']}")
        if injected:
            print(f"\nAGENTS injected: {injected.get('file')}")
        if monitor:
            print(f"\nMonitor: {monitor.get('monitorUrl')} active={monitor.get('active')} rc={monitor.get('serviceStartRc')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
