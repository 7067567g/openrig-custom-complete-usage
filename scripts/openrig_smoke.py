#!/usr/bin/env python3
"""Render + validate N OpenRig bundles without launching live seats.

This is the public, CI-friendly smoke used to check the render/bridge/spec layer.
It deliberately does not start a daemon or a rig.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / "templates" / "specialized" / "openrig-workflow-master" / "render_master.py"
BRIDGE = ROOT / "templates" / "specialized" / "openrig-workflow-master" / "tools" / "openrig_bridge.py"

def run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--out", default="reports/openrig_smoke.json")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()
    base = Path(tempfile.mkdtemp(prefix="openrig-smoke-"))
    results = []
    for i in range(1, args.rounds + 1):
        run_id = f"smoke-{i:03d}"
        run_dir = base / run_id
        project = base / f"project-{i:03d}"
        run_dir.mkdir(parents=True)
        project.mkdir()
        port = 47900 + i
        rec = {"round": i, "runId": run_id, "port": port}
        rc, out = run([sys.executable, str(RENDER), "--run-id", run_id,
                       "--project-root", str(project),
                       "--output-dir", str(run_dir / "openrig"),
                       "--daemon-port", str(port),
                       "--opencode-model", "deepseek/deepseek-flash",
                       "--dsh-profile", "headless", "--force", "--json"])
        rec["render"] = rc
        if rc != 0:
            rec["error"] = out[-1000:]
            results.append(rec)
            continue
        rc, out = run([sys.executable, str(BRIDGE), "doctor", "--run-dir", str(run_dir)])
        rec["bridgeDoctor"] = rc
        rec["bridgeDoctorPass"] = ("PASS bridge" in out)
        rc, out = run(["rig", "workflow", "validate", str(run_dir / "openrig" / "workflow.yaml"), "--json"])
        rec["workflowValidateRc"] = rc
        try:
            rec["workflowOk"] = bool(json.loads(out).get("ok"))
        except Exception:
            rec["workflowOk"] = False
        rc, out = run(["rig", "up", str(run_dir / "openrig" / "rig.yaml"),
                       "--cwd", str(project), "--plan", "--json"])
        rec["upPlanRc"] = rc
        try:
            rec["upPlanStatus"] = json.loads(out).get("status")
        except Exception:
            rec["upPlanStatus"] = "unparsed"
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
    summary = {
        "rounds": args.rounds,
        "base": str(base),
        "passed": sum(1 for r in results if r.get("render") == 0 and r.get("bridgeDoctorPass") and r.get("workflowOk") and r.get("upPlanStatus") == "planned"),
        "results": results,
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{summary['passed']}/{summary['rounds']} passed -> {out}")
    if not args.keep:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if summary["passed"] == args.rounds else 1

if __name__ == "__main__":
    raise SystemExit(main())
