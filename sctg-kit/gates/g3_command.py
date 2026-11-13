#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
import json, subprocess, sys
from pathlib import Path

def check(sub_path: Path, root: Path, evidence_dir: Path):
    sub=json.loads(sub_path.read_text(encoding='utf-8'))
    cmd=sub.get('test_command','').strip()
    if not cmd:
        return {"verdict":"FAIL","reason":"no test_command"}
    try:
        expected=int(sub.get("test_expect_exit", 0))
    except Exception:
        expected=0
    p=subprocess.run(cmd, shell=True, cwd=str(root), capture_output=True, text=True, timeout=300)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir/'test-command.log').write_text(
        f"$ {cmd}\nexpected_exit={expected}\nactual_exit={p.returncode}\n--- stdout ---\n{p.stdout}\n--- stderr ---\n{p.stderr}\n",
        encoding='utf-8')
    if p.returncode != expected:
        return {"verdict":"FAIL","reason":f"test_command exit {p.returncode}, expected {expected}","stdout":p.stdout[-1000:],"stderr":p.stderr[-1000:]}
    return {"verdict":"PASS","reason":f"test_command exit {p.returncode} as expected","stdout":p.stdout[-1000:]}

if __name__ == '__main__':
    r=check(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r['verdict']=='PASS' else 1)
