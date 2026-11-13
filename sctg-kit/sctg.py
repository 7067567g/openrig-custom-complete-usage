#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
"""SCTG shadow runner v0.2 — fixes P0: card text hash, real scope diff, dispatch ledger."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, time, glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml

def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())

def digest_text(text: str) -> str:
    # hash everything except the card_hash line itself
    kept = "".join(line for line in text.splitlines(True) if not line.lstrip().startswith("card_hash:"))
    return "sha256:" + sha256_bytes(kept.encode("utf-8"))

def card_digest(path: Path) -> str:
    return digest_text(path.read_text(encoding="utf-8"))

def load_yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))

def sctg(run_dir: Path) -> Path:
    return run_dir / "sctg"

def task_path(run_dir: Path, task_id: str) -> Path:
    return sctg(run_dir) / "tasks" / f"{task_id}.yaml"

def submission_path(run_dir: Path, task_id: str, attempt: int) -> Path:
    return sctg(run_dir) / "submissions" / task_id / f"attempt-{attempt}.json"

def gate_result_path(run_dir: Path, task_id: str, attempt: int) -> Path:
    return sctg(run_dir) / "gate-results" / task_id / f"attempt-{attempt}.json"

def evidence_dir(run_dir: Path, task_id: str, attempt: int) -> Path:
    return sctg(run_dir) / "evidence" / task_id / f"attempt-{attempt}"

def channel_path(run_dir: Path, task: dict) -> Path:
    return sctg(run_dir) / "channels" / task.get("seat", "main") / f"{task['id']}.md"

def append_jsonl(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def project_root(run_dir: Path) -> Path:
    return run_dir.parents[2]

def git_status_paths(root: Path) -> list[str]:
    p = subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "-uall"], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git status failed: {p.stderr.strip()}")
    paths = []
    for line in p.stdout.splitlines():
        if len(line) < 4:
            continue
        rest = line[3:]
        if " -> " in rest:
            rest = rest.split(" -> ")[-1]
        paths.append(rest.strip().strip('"'))
    return sorted(set(paths))

def expand_write_scope(root: Path, scope: list[str]) -> list[Path]:
    out: list[Path] = []
    for s in scope:
        if s.endswith("/**"):
            base = root / s[:-3]
            if base.exists():
                out.extend([p for p in base.rglob("*") if p.is_file()])
        else:
            p = root / s
            if p.exists() and p.is_file():
                out.append(p)
    return sorted(set(out))

def hash_write_scope(root: Path, scope: list[str]) -> dict[str, str | None]:
    h: dict[str, str | None] = {}
    for p in expand_write_scope(root, scope):
        try:
            h[str(p.relative_to(root))] = sha256_file(p)
        except Exception:
            h[str(p.relative_to(root))] = None
    return h

def render(run_dir: Path, task_id: str, attempt: int) -> Path:
    pattern = load_yaml(sctg(run_dir) / "pattern.yaml")
    task = load_yaml(task_path(run_dir, task_id))
    seat = task.get("seat", "main")
    lines = [
        f"# TASK CARD · {task_id} · attempt {attempt}/{task.get('max_attempts', 1)}",
        f"pattern: sctg/{pattern.get('mode', 'shadow')}",
        f"run_id: {pattern.get('run_id', run_dir.name)}",
        f"seat: {seat}",
        f"depends_on: {task.get('depends_on', [])}",
        "",
        "## 目标",
        str(task.get("title", "")),
        "",
        "## 输入（只读）",
        *[f"- {x}" for x in task.get("inputs", [])],
        "",
        "## 可写范围",
        *[f"- {x}" for x in task.get("write_scope", [])],
        "",
        "## 交付格式",
        f"按 {task.get('deliverable', {}).get('schema', 'sctg/schemas/submission.schema.json')} 输出到：",
        f"- sctg/submissions/{task_id}/attempt-{attempt}.json",
        "必填字段：" + ", ".join(task.get("deliverable", {}).get("required", [])),
        "",
        "## 门禁",
        " -> ".join(task.get("gates", [])),
        "",
        "## 字段语义",
        "- changed_files：修改/删除的已有文件（repo-relative）。",
        "- produced_files：本任务新建的文件（repo-relative）。",
        "- submission 自身不必列入 changed_files / produced_files。",
        "",
        "## 行为约束",
        "- 只读本卡和卡上列出的输入。",
        "- 只写 write_scope 内的文件。",
        "- 不要调用 rig queue / rig workflow。",
        "- 写完提交 JSON 后停止，等待宿主跑门禁。",
        "- 如果无法完成，status 写 BLOCKED，并在 summary 里说明原因。",
        "",
        "## 提交模板",
        "```json",
        json.dumps({
            "task_id": task_id,
            "card_hash": "<computed from card>",
            "summary": "",
            "findings": [],
            "changed_files": [],
            "produced_files": [],
            "commands": [{"cmd": "command you ran", "exit_code": 0, "expect_exit": 0}],
            "test_command": "command that should exit as expected",
            "test_expect_exit": 0,
            "evidence_paths": [],
            "status": "OK",
        }, ensure_ascii=False, indent=2),
        "```",
    ]
    body = "\n".join(lines) + "\n"
    h = digest_text(body)
    final = lines[0] + "\n" + f"card_hash: {h}\n" + "\n".join(lines[1:]) + "\n"
    out = channel_path(run_dir, task)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(final, encoding="utf-8")
    assert card_digest(out) == h, "card digest mismatch"
    append_jsonl(sctg(run_dir) / "ledger" / "events.jsonl", {
        "ts": now(), "event": "card_rendered", "task_id": task_id,
        "attempt": attempt, "card_hash": h, "channel": str(out.relative_to(run_dir)),
    })
    print(json.dumps({"ok": True, "task_id": task_id, "attempt": attempt, "card_hash": h, "channel": str(out)}, ensure_ascii=False))
    return out

def start(run_dir: Path, task_id: str, attempt: int) -> int:
    task = load_yaml(task_path(run_dir, task_id))
    root = project_root(run_dir)
    ed = evidence_dir(run_dir, task_id, attempt)
    ed.mkdir(parents=True, exist_ok=True)
    baseline = {
        "ts": now(),
        "project_root": str(root),
        "git_status_paths": git_status_paths(root),
        "write_scope_hashes": hash_write_scope(root, task.get("write_scope", [])),
    }
    (ed / "baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_jsonl(sctg(run_dir) / "ledger" / "events.jsonl", {
        "ts": now(), "event": "task_started", "task_id": task_id,
        "attempt": attempt, "baseline": str((ed / "baseline.json").relative_to(run_dir)),
    })
    print(json.dumps({"ok": True, "task_id": task_id, "attempt": attempt, "baseline": str(ed / "baseline.json")}, ensure_ascii=False))
    return 0

def dispatch(run_dir: Path, task_id: str, attempt: int, driver_id: str) -> int:
    task = load_yaml(task_path(run_dir, task_id))
    ch = channel_path(run_dir, task)
    sub = submission_path(run_dir, task_id, attempt)
    append_jsonl(sctg(run_dir) / "ledger" / "events.jsonl", {
        "ts": now(), "event": "dispatch", "driver_id": driver_id,
        "task_id": task_id, "attempt": attempt, "card_hash": card_digest(ch),
        "channel": str(ch.relative_to(run_dir)), "submission": str(sub.relative_to(run_dir)),
    })
    print(json.dumps({"ok": True, "event": "dispatch", "task_id": task_id, "attempt": attempt}, ensure_ascii=False))
    return 0

def collect(run_dir: Path, task_id: str, attempt: int, timeout: int, driver_id: str) -> int:
    sub = submission_path(run_dir, task_id, attempt)
    deadline = time.time() + timeout
    last_hash = None
    stable_since = None
    while time.time() < deadline:
        if sub.exists():
            h = sha256_file(sub)
            if h != last_hash:
                last_hash = h
                stable_since = time.time()
            elif stable_since and time.time() - stable_since >= 1.0:
                append_jsonl(sctg(run_dir) / "ledger" / "events.jsonl", {
                    "ts": now(), "event": "submission_received", "driver_id": driver_id,
                    "task_id": task_id, "attempt": attempt, "submission": str(sub.relative_to(run_dir)),
                    "submission_sha256": h,
                })
                print(json.dumps({"ok": True, "submission": str(sub), "sha256": h}, ensure_ascii=False))
                return 0
        time.sleep(0.5)
    print(json.dumps({"ok": False, "error": "timeout waiting for submission", "submission": str(sub)}, ensure_ascii=False))
    return 1

def run_gate(script: Path, args: list[str], cwd: Path) -> dict:
    p = subprocess.run([sys.executable, str(script), *args], cwd=str(cwd), capture_output=True, text=True)
    out = p.stdout.strip()
    try:
        res = json.loads(out) if out else {}
    except Exception:
        res = {"verdict": "FAIL", "reason": f"gate output not JSON: {out[:200]}"}
    res.setdefault("verdict", "PASS" if p.returncode == 0 else "FAIL")
    res["gate"] = script.stem
    res["exit_code"] = p.returncode
    if p.stderr.strip():
        res["stderr"] = p.stderr.strip()[:500]
    return res

def gate(run_dir: Path, task_id: str, attempt: int) -> int:
    pattern = load_yaml(sctg(run_dir) / "pattern.yaml")
    task = load_yaml(task_path(run_dir, task_id))
    sub = submission_path(run_dir, task_id, attempt)
    if not sub.exists():
        print(json.dumps({"ok": False, "error": f"missing submission: {sub}"}, ensure_ascii=False))
        return 1
    try:
        sub_data = json.loads(sub.read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"bad submission json: {e}"}, ensure_ascii=False))
        return 1
    ch = channel_path(run_dir, task)
    expected = card_digest(ch)
    results = [{
        "gate": "g_card_hash",
        "verdict": "PASS" if sub_data.get("card_hash") == expected else "FAIL",
        "reason": "card text hash matches" if sub_data.get("card_hash") == expected else f"expected {expected}, got {sub_data.get('card_hash')}",
        "exit_code": 0,
    }]
    gdir = sctg(run_dir) / "gates"
    ed = evidence_dir(run_dir, task_id, attempt)
    # gate order from task, but always card hash first
    for g in task.get("gates", []):
        if g == "g0_schema":
            results.append(run_gate(gdir / "g0_schema.py", [str(sub), str(sctg(run_dir) / "schemas" / "submission.schema.json")], run_dir))
        elif g == "g1_scope":
            results.append(run_gate(gdir / "g1_scope.py", [str(sub), str(task_path(run_dir, task_id)), str(ed / "baseline.json")], run_dir))
        elif g == "g2_evidence":
            results.append(run_gate(gdir / "g2_evidence.py", [str(sub), str(task_path(run_dir, task_id)), str(project_root(run_dir))], run_dir))
        elif g == "g3_command":
            results.append(run_gate(gdir / "g3_command.py", [str(sub), str(project_root(run_dir)), str(ed)], run_dir))
        else:
            results.append({"gate": g, "verdict": "FAIL", "reason": "unknown gate", "exit_code": 1})
    overall = "PASS" if all(r.get("verdict") == "PASS" for r in results) else "FAIL"
    record = {
        "ts": now(), "task_id": task_id, "attempt": attempt, "card_hash": expected,
        "submission": str(sub.relative_to(run_dir)), "gates": results, "verdict": overall,
    }
    out = gate_result_path(run_dir, task_id, attempt)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_jsonl(sctg(run_dir) / "ledger" / "events.jsonl", {
        "ts": now(), "event": "gates_run", "task_id": task_id, "attempt": attempt,
        "verdict": overall, "gate_result": str(out.relative_to(run_dir)),
    })
    append_jsonl(sctg(run_dir) / "ledger" / "acceptance.jsonl", {
        "ts": now(), "task_id": task_id, "attempt": attempt, "verdict": overall,
        "card_hash": expected, "submission_hash": sha256_file(sub),
        "gate_result": str(out.relative_to(run_dir)),
    })
    print(json.dumps({"ok": overall == "PASS", "task_id": task_id, "attempt": attempt, "verdict": overall, "gates": results}, ensure_ascii=False))
    return 0 if overall == "PASS" else 1

def read_jsonl(p: Path):
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

def metrics(run_dir: Path) -> int:
    from datetime import datetime
    events = read_jsonl(sctg(run_dir) / "ledger" / "events.jsonl")
    acceptance = read_jsonl(sctg(run_dir) / "ledger" / "acceptance.jsonl")
    def ts(s):
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    tasks: dict[tuple[Any, Any], dict[str, Any]] = {}
    for e in events:
        key = (e.get("task_id"), e.get("attempt"))
        if key == (None, None):
            continue
        t = tasks.setdefault(key, {"task_id": e.get("task_id"), "attempt": e.get("attempt"), "events": []})
        t["events"].append(e)
    out = []
    for key, t in sorted(tasks.items(), key=lambda x: (str(x[0][0]), x[0][1] or 0)):
        ev = t["events"]
        def first(kind):
            for e in ev:
                if e.get("event") == kind:
                    return e
            return None
        def last(kind):
            r = None
            for e in ev:
                if e.get("event") == kind:
                    r = e
            return r
        start = first("task_started"); sub = first("submission_received"); gate = last("gates_run")
        start_ts = ts(start.get("ts")) if start else None
        sub_ts = ts(sub.get("ts")) if sub else None
        gate_ts = ts(gate.get("ts")) if gate else None
        sub_path = submission_path(run_dir, t["task_id"], t["attempt"])
        cmd_count = 0
        if sub_path.exists():
            try:
                cmd_count = len(json.loads(sub_path.read_text(encoding="utf-8")).get("commands", []))
            except Exception:
                cmd_count = 0
        out.append({
            "task_id": t["task_id"],
            "attempt": t["attempt"],
            "started_at": start.get("ts") if start else None,
            "submission_at": sub.get("ts") if sub else None,
            "gate_at": gate.get("ts") if gate else None,
            "seconds_start_to_submission": round((sub_ts - start_ts).total_seconds(), 2) if start_ts and sub_ts else None,
            "seconds_submission_to_gate": round((gate_ts - sub_ts).total_seconds(), 2) if sub_ts and gate_ts else None,
            "command_count": cmd_count,
            "gate_verdict": gate.get("verdict") if gate else None,
            "attempts_for_task": sum(1 for e in events if e.get("task_id") == t["task_id"] and e.get("event") == "task_started"),
        })
    print(json.dumps({"run_id": run_dir.name, "metrics": out, "acceptance": acceptance}, ensure_ascii=False, indent=2))
    return 0

def report(run_dir: Path) -> int:
    pattern = load_yaml(sctg(run_dir) / "pattern.yaml")
    ledger = sctg(run_dir) / "ledger" / "acceptance.jsonl"
    rows = []
    if ledger.exists():
        rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()]
    print(json.dumps({"run_id": pattern.get("run_id"), "mode": pattern.get("mode"), "acceptance": rows}, ensure_ascii=False, indent=2))
    return 0

def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("run_dir")
    p = sub.add_parser("render"); p.add_argument("run_dir"); p.add_argument("task_id"); p.add_argument("--attempt", type=int, default=1)
    p = sub.add_parser("start"); p.add_argument("run_dir"); p.add_argument("task_id"); p.add_argument("attempt", type=int)
    p = sub.add_parser("dispatch"); p.add_argument("run_dir"); p.add_argument("task_id"); p.add_argument("attempt", type=int); p.add_argument("--driver-id", default="sctg-host-runner")
    p = sub.add_parser("collect"); p.add_argument("run_dir"); p.add_argument("task_id"); p.add_argument("attempt", type=int); p.add_argument("--timeout", type=int, default=600); p.add_argument("--driver-id", default="sctg-host-runner")
    p = sub.add_parser("gate"); p.add_argument("run_dir"); p.add_argument("task_id"); p.add_argument("attempt", type=int)
    p = sub.add_parser("report"); p.add_argument("run_dir")
    p = sub.add_parser("metrics"); p.add_argument("run_dir")
    p = sub.add_parser("digest"); p.add_argument("card")
    a = ap.parse_args(argv)
    if a.cmd == "digest":
        print(card_digest(Path(a.card))); return 0
    run_dir = Path(a.run_dir).resolve()
    if a.cmd == "init":
        for d in ("tasks","channels","submissions","gate-results","ledger","evidence","schemas","gates","scripts"):
            (sctg(run_dir)/d).mkdir(parents=True, exist_ok=True)
        print(json.dumps({"ok": True, "run_dir": str(run_dir)})); return 0
    if a.cmd == "render": render(run_dir, a.task_id, a.attempt); return 0
    if a.cmd == "start": return start(run_dir, a.task_id, a.attempt)
    if a.cmd == "dispatch": return dispatch(run_dir, a.task_id, a.attempt, a.driver_id)
    if a.cmd == "collect": return collect(run_dir, a.task_id, a.attempt, a.timeout, a.driver_id)
    if a.cmd == "gate": return gate(run_dir, a.task_id, a.attempt)
    if a.cmd == "report": return report(run_dir)
    if a.cmd == "metrics": return metrics(run_dir)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
