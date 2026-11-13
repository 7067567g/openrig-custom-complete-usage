#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
"""Demonstrate a Shadow -> Lite -> Shadow rollback with an append-only ledger."""
from __future__ import annotations
import importlib.util, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "examples" / "rollback" / "_ledger.jsonl"

def load_ledger():
    spec = importlib.util.spec_from_file_location("sctg_ledger", ROOT / "sctg-kit" / "ledger.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

def main() -> int:
    l = load_ledger()
    shutil.rmtree(LEDGER.parent / "_ledger.jsonl", ignore_errors=True)
    l.append_event(LEDGER, {"ts": "1", "event": "mode_switched", "from_mode": "shadow", "to_mode": "lite", "decision_id": "REQ-DEMO-001"})
    l.append_event(LEDGER, {"ts": "2", "event": "rollback_started", "reason": "demo"})
    l.append_event(LEDGER, {"ts": "3", "event": "mode_switched", "from_mode": "lite", "to_mode": "shadow", "decision_id": "REQ-DEMO-001"})
    ok, errors = l.verify(LEDGER)
    rows = l.read_events(LEDGER)
    final_mode = rows[-1].get("to_mode") if rows else None
    print(json.dumps({"verdict": "PASS" if ok and final_mode == "shadow" else "FAIL", "events": rows, "errors": errors}, ensure_ascii=False, indent=2))
    LEDGER.unlink(missing_ok=True)
    return 0 if ok and final_mode == "shadow" else 1

if __name__ == "__main__":
    raise SystemExit(main())
