# Copyright 2026 SCTG contributors
# Licensed under the Apache License, Version 2.0.
"""Minimal append-only ledger helpers.

The ledger is JSONL. `append_event` never rewrites old rows. `verify` checks
that every row is valid JSON and that the file has not lost its chain marker
when `prev_hash` is present.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


def _sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def append_event(path: Path, event: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    prev = ""
    if path.exists() and path.stat().st_size:
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines:
            prev = _sha(lines[-1].encode("utf-8"))
    row = dict(event)
    row.setdefault("prev_hash", prev)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


def read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    prev = ""
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            errors.append(f"line {i}: invalid json: {exc}")
            continue
        if "prev_hash" in row and row["prev_hash"] != prev:
            errors.append(f"line {i}: prev_hash mismatch")
        prev = _sha(line.encode("utf-8"))
    return (not errors, errors)
