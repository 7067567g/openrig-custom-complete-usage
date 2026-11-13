#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
import json, hashlib, subprocess, sys
from pathlib import Path
import yaml

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def is_cache_path(path: str) -> bool:
    parts = path.replace('\\', '/').split('/')
    return ('__pycache__' in parts or '.pytest_cache' in parts or '.mypy_cache' in parts or '.ruff_cache' in parts or path.endswith('.pyc'))

def git_status_paths(root: Path):
    p=subprocess.run(["git","-C",str(root),"status","--porcelain=v1","-uall"],capture_output=True,text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    paths=[]
    for line in p.stdout.splitlines():
        if len(line)<4: continue
        rest=line[3:]
        if " -> " in rest: rest=rest.split(" -> ")[-1]
        paths.append(rest.strip().strip('"'))
    return sorted(set(paths))

def expand(root: Path, scope):
    out=[]
    for s in scope:
        if s.endswith("/**"):
            base=root/s[:-3]
            if base.exists():
                out += [p for p in base.rglob("*") if p.is_file()]
        else:
            p=root/s
            if p.exists() and p.is_file(): out.append(p)
    return sorted(set(out))

def is_allowed(path: str, scope) -> bool:
    for s in scope:
        if s.endswith('/**'):
            base=s[:-3]
            if path == base or path.startswith(base + '/'):
                return True
        elif path == s:
            return True
    return False

def current_hashes(root: Path, scope):
    return {str(p.relative_to(root)): sha(p) for p in expand(root, scope)}

def check(sub_path: Path, task_path: Path, baseline_path: Path):
    sub=json.loads(sub_path.read_text(encoding='utf-8'))
    task=yaml.safe_load(task_path.read_text(encoding='utf-8'))
    baseline=json.loads(baseline_path.read_text(encoding='utf-8'))
    root=Path(baseline['project_root'])
    allowed=task.get('write_scope', [])
    base_paths=set(baseline.get('git_status_paths', []))
    now_paths=set(git_status_paths(root))
    new_paths=now_paths-base_paths
    # hash changes within write_scope
    base_hashes=baseline.get('write_scope_hashes', {})
    now_hashes=current_hashes(root, allowed)
    changed=set()
    for p in set(base_hashes)|set(now_hashes):
        if base_hashes.get(p) != now_hashes.get(p):
            changed.add(p)
    actual_all={p for p in (new_paths|changed) if not is_cache_path(p)}
    # host-owned run artifacts are not AI writes; do not hard-fail them
    run_dir = Path(sub_path).resolve().parents[3]
    try:
        run_rel = str(run_dir.relative_to(root))
    except Exception:
        run_rel = ""
    host_prefixes = [
        f"{run_rel}/sctg/evidence/", f"{run_rel}/sctg/ledger/", f"{run_rel}/sctg/gate-results/",
        f"{run_rel}/sctg/channels/", f"{run_rel}/sctg/tasks/", f"{run_rel}/sctg/schemas/",
        f"{run_rel}/sctg/gates/", f"{run_rel}/sctg/scripts/", f"{run_rel}/sctg/host/", f"{run_rel}/stage2/auto/",
    ]
    def host_owned(p):
        return any(p == x.rstrip('/') or p.startswith(x) for x in host_prefixes)
    actual_all = {p for p in actual_all if not host_owned(p)}
    actual_in_scope = {p for p in actual_all if is_allowed(p, allowed)}
    reported = set(sub.get('changed_files', [])) | set(sub.get('produced_files', []))
    reported = {p for p in reported if not is_cache_path(p) and not host_owned(p)}
    # the submission file itself is part of the transaction; do not require it in changed_files
    try:
        reported.add(str(Path(sub_path).resolve().relative_to(root)))
    except Exception:
        pass
    reported_in_scope = {p for p in reported if is_allowed(p, allowed)}
    reported_outside = sorted(p for p in reported if not is_allowed(p, allowed) and not host_owned(p))
    missing = sorted(actual_in_scope - reported_in_scope)
    extra = sorted(reported_in_scope - actual_in_scope)
    warnings = sorted(p for p in actual_all if p not in actual_in_scope and not host_owned(p))
    problems=[]
    if missing: problems.append(f"unreported in-scope changes: {missing}")
    if extra: problems.append(f"reported but not changed: {extra}")
    if reported_outside: problems.append(f"reported outside write_scope: {reported_outside}")
    if problems:
        return {"verdict":"FAIL","reason":"; ".join(problems),"actual_in_scope":sorted(actual_in_scope),"warnings":warnings}
    return {"verdict":"PASS","reason":"scope ok","actual_in_scope":sorted(actual_in_scope),"warnings":warnings}

if __name__ == '__main__':
    r=check(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r['verdict']=='PASS' else 1)
