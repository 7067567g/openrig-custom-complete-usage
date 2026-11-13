#!/usr/bin/env python3
# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
"""Demonstrate a two-seat handoff and independent join contract."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "examples" / "two-seat-handoff" / "_work"

def main() -> int:
    shutil.rmtree(BASE, ignore_errors=True)
    BASE.mkdir(parents=True)
    artifact = BASE / "handoff.md"
    artifact.write_text("# Handoff\n\nShip the contract.\n", encoding="utf-8")
    h = "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest()
    handoff = {"from_seat": "producer", "to_seat": "reviewer", "artifact": "handoff.md", "artifact_hash": h, "acceptance": ["hash matches", "reviewer is independent"]}
    join = {"reviewer": "reviewer", "producer": "producer", "handoff_hash": h, "verdict": "PASS", "scope_conflicts": 0, "findings": ["hash bound", "seats distinct"]}
    (BASE / "handoff.json").write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BASE / "join.json").write_text(json.dumps(join, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = handoff["from_seat"] != join["reviewer"] and handoff["artifact_hash"] == join["handoff_hash"] and join["scope_conflicts"] == 0
    print(json.dumps({"verdict": "PASS" if ok else "FAIL", "handoff": handoff, "join": join}, ensure_ascii=False, indent=2))
    shutil.rmtree(BASE, ignore_errors=True)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
