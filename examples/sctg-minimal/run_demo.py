#!/usr/bin/env python3
"""Minimal SCTG end-to-end demo using the local sctg-kit."""
from __future__ import annotations
import json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "sctg-kit" / "sctg.py"
RUN = ROOT / "examples" / "sctg-minimal" / "_run"
WORK = ROOT / "examples" / "sctg-minimal" / "work"
TASK_ID = "T-001"

def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KIT), *args], cwd=ROOT, capture_output=True, text=True)

def main() -> int:
    shutil.rmtree(RUN, ignore_errors=True)
    shutil.rmtree(WORK, ignore_errors=True)
    (RUN / "sctg" / "tasks").mkdir(parents=True, exist_ok=True)
    (RUN / "sctg" / "gates").mkdir(parents=True, exist_ok=True)
    (RUN / "sctg" / "schemas").mkdir(parents=True, exist_ok=True)
    for src in (ROOT / "sctg-kit" / "gates").glob("*.py"):
        shutil.copy2(src, RUN / "sctg" / "gates" / src.name)
    shutil.copy2(ROOT / "sctg-kit" / "schemas" / "submission.schema.json", RUN / "sctg" / "schemas" / "submission.schema.json")
    (RUN / "sctg" / "pattern.yaml").write_text(
        "pattern: sctg\nmode: shadow\nrun_id: minimal-demo\n", encoding="utf-8"
    )
    (RUN / "sctg" / "tasks" / f"{TASK_ID}.yaml").write_text(
        f"""id: {TASK_ID}
title: Create one artifact inside the declared write scope.
seat: main
inputs: []
write_scope:
  - examples/sctg-minimal/work/**
  - examples/sctg-minimal/_run/sctg/submissions/T-001/attempt-1.json
deliverable:
  schema: sctg/schemas/submission.schema.json
  required: [task_id, card_hash, summary, status]
gates: [g0_schema, g1_scope, g2_evidence, g3_command]
on_pass: END
on_fail: retry
max_attempts: 1
""",
        encoding="utf-8",
    )
    for cmd in (("start", str(RUN), TASK_ID, "1"), ("render", str(RUN), TASK_ID, "--attempt", "1"), ("dispatch", str(RUN), TASK_ID, "1")):
        p = run(*cmd)
        if p.returncode != 0:
            print(p.stdout, p.stderr, sep="\n")
            return p.returncode
    card_path = RUN / "sctg" / "channels" / "main" / f"{TASK_ID}.md"
    card = card_path.read_text(encoding="utf-8")
    m = re.search(r"^card_hash: (sha256:[0-9a-f]+)$", card, re.MULTILINE)
    if not m:
        print("no card_hash in rendered card")
        return 1
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "hello.txt").write_text("hello from sctg\n", encoding="utf-8")
    sub = {
        "task_id": TASK_ID,
        "card_hash": m.group(1),
        "summary": "Create examples/sctg-minimal/work/hello.txt",
        "findings": [],
        "changed_files": [],
        "produced_files": ["examples/sctg-minimal/work/hello.txt"],
        "commands": [{"cmd": "write hello.txt", "exit_code": 0, "expect_exit": 0}],
        "test_command": "python3 -c \"from pathlib import Path; assert Path('examples/sctg-minimal/work/hello.txt').exists()\"",
        "test_expect_exit": 0,
        "evidence_paths": ["examples/sctg-minimal/work/hello.txt"],
        "status": "OK",
    }
    sub_path = RUN / "sctg" / "submissions" / TASK_ID / "attempt-1.json"
    sub_path.parent.mkdir(parents=True, exist_ok=True)
    sub_path.write_text(json.dumps(sub, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    p = run("gate", str(RUN), TASK_ID, "1")
    print(p.stdout.strip())
    if p.stderr.strip():
        print(p.stderr.strip(), file=sys.stderr)
    try:
        result = json.loads(p.stdout)
    except Exception:
        result = {"verdict": "FAIL", "error": "gate output was not JSON"}
    shutil.rmtree(RUN, ignore_errors=True)
    shutil.rmtree(WORK, ignore_errors=True)
    return 0 if result.get("verdict") == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
