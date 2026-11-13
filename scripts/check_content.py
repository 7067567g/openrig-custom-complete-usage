#!/usr/bin/env python3
"""Content audit: bilingual docs, examples, sanitized sample, no internal names."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    ("README.md", "README.zh-CN.md"),
    ("benchmark/README.md", "benchmark/README.zh-CN.md"),
    ("examples/README.md", "examples/README.zh-CN.md"),
    ("VALIDATION.md", "VALIDATION.zh-CN.md"),
    ("docs/QUICKSTART.md", "docs/QUICKSTART.zh-CN.md"),
    ("docs/ARCHITECTURE.md", "docs/ARCHITECTURE.zh-CN.md"),
    ("docs/MULTI-ROUND.md", "docs/MULTI-ROUND.zh-CN.md"),
    ("docs/OPENRIG.md", "docs/OPENRIG.zh-CN.md"),
    ("docs/PUBLISHING.md", "docs/PUBLISHING.zh-CN.md"),
    ("docs/VERSIONING.md", "docs/VERSIONING.zh-CN.md"),
    ("docs/ENVIRONMENT.md", "docs/ENVIRONMENT.zh-CN.md"),
    ("docs/REPRODUCIBILITY.md", "docs/REPRODUCIBILITY.zh-CN.md"),
    ("docs/LIMITATIONS.md", "docs/LIMITATIONS.zh-CN.md"),
    ("docs/cases/README.md", "docs/cases/README.zh-CN.md"),
    ("docs/cases/01-render-smoke.md", "docs/cases/01-render-smoke.zh-CN.md"),
    ("docs/cases/02-12-round-cases.md", "docs/cases/02-12-round-cases.zh-CN.md"),
    ("docs/REFERENCE.md", "docs/REFERENCE.zh-CN.md"),
    ("docs/CONCEPTS.md", "docs/CONCEPTS.zh-CN.md"),
    ("docs/MEMORY-SAFETY.md", "docs/MEMORY-SAFETY.zh-CN.md"),
    ("docs/cases/03-memory-incident.md", "docs/cases/03-memory-incident.zh-CN.md"),
    ("examples/README.md", "examples/README.zh-CN.md"),
]
EXAMPLES = ["openrig-minimal", "multi-round", "sctg-minimal", "sanitized-run", "multi-card", "decision", "rollback", "two-seat-handoff", "live-run", "round-cases", "memory-limits"]
SANITIZED = [
    "examples/sanitized-run/PROJECT.md",
    "examples/sanitized-run/SPEC.md",
    "examples/sanitized-run/DECISIONS.md",
    "examples/sanitized-run/STATUS-Round-1.md",
    "examples/sanitized-run/ISSUES.md",
    "examples/sanitized-run/sctg/submission.json",
    "examples/sanitized-run/sctg/gate-result.json",
    "examples/sanitized-run/evidence/README.md",
]
FORBIDDEN = [
    re.compile("yue" + "yue", re.I),
    re.compile("月" + "月"),
    re.compile("we" + "chat", re.I),
    re.compile("deepseek-" + "知识库"),
    re.compile("10-" + "openrig-" + "deepseek"),
    re.compile("person" + "nal", re.I),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]
SKIP = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".agents"}

def main() -> int:
    errors = []
    for en, zh in PAIRS:
        pe, pz = ROOT / en, ROOT / zh
        if not pe.is_file(): errors.append(f"missing English doc: {en}")
        if not pz.is_file(): errors.append(f"missing Chinese doc: {zh}")
        if pe.is_file() and "简体中文" not in pe.read_text(encoding="utf-8").splitlines()[0]:
            errors.append(f"missing Chinese switch in {en}")
        if pz.is_file() and "English" not in pz.read_text(encoding="utf-8").splitlines()[0]:
            errors.append(f"missing English switch in {zh}")
    for ex in EXAMPLES:
        for name in ("README.md", "README.zh-CN.md"):
            if not (ROOT / "examples" / ex / name).is_file():
                errors.append(f"missing example doc: examples/{ex}/{name}")
    for rel in SANITIZED:
        if not (ROOT / rel).is_file():
            errors.append(f"missing sanitized sample: {rel}")
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in SKIP for part in p.parts):
            continue
        if p.resolve() == Path(__file__).resolve():
            continue
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".xlsx", ".db", ".sqlite", ".pyc"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pat in FORBIDDEN:
            if pat.search(text):
                errors.append(f"forbidden content {pat.pattern!r} in {p.relative_to(ROOT)}")
                break
    report = ROOT / "reports" / "openrig_smoke.json"
    if not report.is_file():
        errors.append("missing reports/openrig_smoke.json")
    else:
        data = json.loads(report.read_text(encoding="utf-8"))
        if data.get("passed") != 12 or data.get("rounds") != 12:
            errors.append(f"OpenRig smoke not 12/12: {data.get('passed')}/{data.get('rounds')}")
    print(json.dumps({"verdict": "PASS" if not errors else "FAIL", "pairs": len(PAIRS), "examples": len(EXAMPLES), "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
