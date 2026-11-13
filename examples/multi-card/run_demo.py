#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
"""Run three cards sequentially through all four gates."""
from __future__ import annotations
import json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "sctg-kit" / "sctg.py"
RUN = ROOT / "examples" / "multi-card" / "_run"
WORK = ROOT / "examples" / "multi-card" / "work"

def call(*args: str):
    return subprocess.run([sys.executable, str(KIT), *args], cwd=ROOT, capture_output=True, text=True)

def run_card(i: int) -> dict:
    tid = f"T-{i:03d}"
    out = WORK / f"card-{i}.txt"
    task = RUN / "sctg" / "tasks" / f"{tid}.yaml"
    task.write_text(f"""id: {tid}
title: Create multi-card artifact {i}.
seat: main
inputs: []
write_scope:
  - examples/multi-card/work/**
  - examples/multi-card/_run/sctg/submissions/{tid}/attempt-1.json
deliverable:
  schema: sctg/schemas/submission.schema.json
  required: [task_id, card_hash, summary, status]
gates: [g0_schema, g1_scope, g2_evidence, g3_command]
on_pass: END
on_fail: retry
max_attempts: 1
""", encoding="utf-8")
    for cmd in (("start", str(RUN), tid, "1"), ("render", str(RUN), tid, "--attempt", "1"), ("dispatch", str(RUN), tid, "1")):
        p = call(*cmd)
        if p.returncode != 0:
            raise RuntimeError(p.stdout + p.stderr)
    card = (RUN / "sctg" / "channels" / "main" / f"{tid}.md").read_text(encoding="utf-8")
    m = re.search(r"^card_hash: (sha256:[0-9a-f]+)$", card, re.MULTILINE)
    if not m:
        raise RuntimeError("no card hash")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"card {i}\n", encoding="utf-8")
    sub = {
        "task_id": tid, "card_hash": m.group(1), "summary": f"create card-{i}.txt",
        "findings": [], "changed_files": [], "produced_files": [str(out.relative_to(ROOT))],
        "commands": [{"cmd": f"write card-{i}.txt", "exit_code": 0, "expect_exit": 0}],
        "test_command": f"python3 -c \"from pathlib import Path; assert Path('{out.relative_to(ROOT)}').exists()\"",
        "test_expect_exit": 0, "evidence_paths": [str(out.relative_to(ROOT))], "status": "OK",
    }
    sp = RUN / "sctg" / "submissions" / tid / "attempt-1.json"
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(sub, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    p = call("gate", str(RUN), tid, "1")
    result = json.loads(p.stdout) if p.stdout.strip() else {"verdict": "FAIL"}
    result["task_id"] = tid
    return result

def main() -> int:
    shutil.rmtree(RUN, ignore_errors=True); shutil.rmtree(WORK, ignore_errors=True)
    (RUN / "sctg" / "tasks").mkdir(parents=True, exist_ok=True)
    (RUN / "sctg" / "gates").mkdir(parents=True, exist_ok=True)
    (RUN / "sctg" / "schemas").mkdir(parents=True, exist_ok=True)
    for src in (ROOT / "sctg-kit" / "gates").glob("*.py"):
        shutil.copy2(src, RUN / "sctg" / "gates" / src.name)
    shutil.copy2(ROOT / "sctg-kit" / "schemas" / "submission.schema.json", RUN / "sctg" / "schemas" / "submission.schema.json")
    (RUN / "sctg" / "pattern.yaml").write_text("pattern: sctg\nmode: shadow\nrun_id: multi-card-demo\n", encoding="utf-8")
    results = [run_card(i) for i in (1, 2, 3)]
    print(json.dumps({"verdict": "PASS" if all(r.get("verdict") == "PASS" for r in results) else "FAIL", "cards": results}, ensure_ascii=False))
    shutil.rmtree(RUN, ignore_errors=True); shutil.rmtree(WORK, ignore_errors=True)
    return 0 if all(r.get("verdict") == "PASS" for r in results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
