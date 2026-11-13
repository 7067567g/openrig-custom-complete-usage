#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
import json, hashlib, sys
from pathlib import Path
import yaml

def is_allowed(path: str, scope) -> bool:
    for s in scope:
        if s.endswith('/**'):
            base=s[:-3]
            if path == base or path.startswith(base + '/'):
                return True
        elif path == s:
            return True
    return False

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def check(sub_path: Path, task_path: Path, root: Path):
    sub=json.loads(sub_path.read_text(encoding='utf-8'))
    task=yaml.safe_load(task_path.read_text(encoding='utf-8'))
    allowed=set(task.get('write_scope', []))
    problems=[]
    produced=sub.get('produced_files', [])
    if not produced:
        problems.append('no produced_files')
    for p in produced:
        if not is_allowed(p, task.get('write_scope', [])):
            problems.append(f'produced outside write_scope: {p}')
        q=root/p
        if not q.exists():
            problems.append(f'missing produced file: {p}')
    cmds=sub.get('commands', [])
    if not cmds:
        problems.append('no commands recorded')
    for c in cmds:
        if not isinstance(c, dict) or 'cmd' not in c or 'exit_code' not in c:
            problems.append('bad command record')
        else:
            expected = c.get('expect_exit', 0)
            if c.get('exit_code') != expected:
                problems.append(f"command exit {c.get('exit_code')}, expected {expected}: {c.get('cmd')}")
    ev=[]
    for p in sub.get('evidence_paths', []):
        q=root/p
        if not q.exists():
            problems.append(f'missing evidence: {p}')
        else:
            ev.append({"path":p,"sha256":sha(q)})
    if problems:
        return {"verdict":"FAIL","reason":"; ".join(problems)}
    return {"verdict":"PASS","reason":"evidence ok","evidence":ev}

if __name__ == '__main__':
    r=check(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r['verdict']=='PASS' else 1)
