#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
"""Demonstrate Decision request, independent approval, and replay."""
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def load_decision():
    spec = importlib.util.spec_from_file_location("sctg_decision", ROOT / "sctg-kit" / "decision.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

def main() -> int:
    d = load_decision()
    obj = ROOT / "docs" / "REFERENCE.md"
    h = "sha256:" + hashlib.sha256(obj.read_bytes()).hexdigest()
    now = "2026-11-13T00:00:00+00:00"
    req = {
        "id": "REQ-DEMO-001", "requested_by": "producer-seat", "subject": "Enable Lite for one demo run",
        "object": str(obj.relative_to(ROOT)), "object_hash": h,
        "scope": ["examples/multi-card/**"], "options": [
            {"id": "lite-demo", "summary": "enable Lite for the demo"},
            {"id": "keep-shadow", "summary": "do not switch"},
        ],
        "recommendation": "lite-demo", "conditions": "demo only; rollback on failure",
        "expiry": "2099-01-01T00:00:00+00:00",
        "mode_change": {"from_mode": "shadow", "to_mode": "lite", "rollback": "switch back to shadow"},
    }
    rec, errors = d.decide(req, approver="MAIN", choice="lite-demo", now=now, producer="producer-seat")
    if errors:
        print(json.dumps({"verdict": "FAIL", "errors": errors}, ensure_ascii=False)); return 1
    replays = {
        "in_scope": d.is_authorized(rec, now=now, action_scope="examples/multi-card/card-1"),
        "out_of_scope": d.is_authorized(rec, now=now, action_scope="examples/other/card-1"),
        "expired": d.is_authorized(rec, now="2100-01-01T00:00:00+00:00", action_scope="examples/multi-card/card-1"),
    }
    self_review, self_errors = d.decide(req, approver="producer-seat", choice="lite-demo", now=now, producer="producer-seat")
    ok = (
        replays["in_scope"] == (True, "OK")
        and replays["out_of_scope"][1] == "SCOPE_NOT_COVERED"
        and replays["expired"][1] == "EXPIRED"
        and self_review is None and self_errors
    )
    print(json.dumps({"verdict": "PASS" if ok else "FAIL", "decision": rec, "replays": {k: {"ok": v[0], "reason": v[1]} for k, v in replays.items()}, "self_review_rejected": self_review is None}, ensure_ascii=False, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
