#!/usr/bin/env python3
"""Minimal benchmark harness smoke.

This is a mechanics harness, not a model benchmark. It copies a task workspace,
runs each arm command in an isolated temp dir, runs the task verifier, and
writes a JSON/Markdown result. Real model arms can be plugged in later.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, tempfile, time
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]

def run(cmd, cwd, timeout):
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return time.perf_counter() - t0, p

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=str(ROOT / "benchmark" / "tasks" / "synthetic-v1"))
    ap.add_argument("--arms", default=str(ROOT / "benchmark" / "arms.example.yaml"))
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--out", default=str(ROOT / "benchmark" / "results" / "synthetic-smoke.json"))
    args = ap.parse_args()
    arms = yaml.safe_load(Path(args.arms).read_text(encoding="utf-8"))["arms"]
    task_dirs = sorted(p.parent for p in Path(args.tasks).glob("*/task.yaml"))
    rows = []
    for task_dir in task_dirs:
        task = yaml.safe_load((task_dir / "task.yaml").read_text(encoding="utf-8"))
        for arm in arms:
            for rep in range(1, args.reps + 1):
                tmp = Path(tempfile.mkdtemp(prefix=f"bench-{task['id']}-{arm['name']}-"))
                try:
                    work = tmp / "workspace"
                    shutil.copytree(task_dir / "workspace", work)
                    cmd = [str(x) for x in arm["command"]]
                    wall, p = run(cmd, work, args.timeout)
                    verify = subprocess.run([sys.executable, str(task_dir / "verify.py")], cwd=work, capture_output=True, text=True, timeout=args.timeout)
                    rows.append({
                        "task": task["id"],
                        "arm": arm["name"],
                        "rep": rep,
                        "exit": p.returncode,
                        "verify_exit": verify.returncode,
                        "wall_s": round(wall, 4),
                        "stdout": p.stdout[-500:],
                        "stderr": p.stderr[-500:],
                    })
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    summary = {"schema": "openrig-benchmark-smoke/v1", "note": "mechanics smoke; not a model benchmark", "rows": rows}
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# Benchmark smoke", "", "Mechanics only; not a model benchmark.", "", "| task | arm | rep | exit | verify | wall_s |", "|---|---|---:|---:|---:|---:|"]
    for r in rows:
        md.append(f"| {r['task']} | {r['arm']} | {r['rep']} | {r['exit']} | {r['verify_exit']} | {r['wall_s']} |")
    (out.with_suffix(".md")).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "out": str(out), "passed": sum(1 for r in rows if r["exit"] == 0 and r["verify_exit"] == 0)}, ensure_ascii=False))
    return 0 if all(r["exit"] == 0 and r["verify_exit"] == 0 for r in rows) else 1

if __name__ == "__main__":
    raise SystemExit(main())
