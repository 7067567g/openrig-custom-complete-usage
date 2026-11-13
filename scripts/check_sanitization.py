#!/usr/bin/env python3
"""Sanitization gate: no author paths, credentials, or private-key material."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".agents"}
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".xlsx", ".db", ".sqlite", ".pyc", ".zip"}
PATTERNS = [
    (re.compile(r"/home/[A-Za-z0-9_.-]+/"), "author home path"),
    (re.compile(r"/Users/[A-Za-z0-9_.-]+/"), "macOS user path"),
    (re.compile(r"~/.dsh"), "DSH credential path"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "API key"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"gho_[A-Za-z0-9]{20,}"), "GitHub OAuth token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"), "Slack token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS key"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"DEEPSEEK_API_KEY\s*=\s*[^\s]+"), "inline API key assignment"),
]

def main() -> int:
    errors = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in SKIP for part in p.parts):
            continue
        if p.resolve() == Path(__file__).resolve():
            continue
        if p.suffix.lower() in BINARY:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pat, label in PATTERNS:
            if pat.search(text):
                errors.append(f"{label} in {p.relative_to(ROOT)}")
    print(json.dumps({"verdict": "PASS" if not errors else "FAIL", "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
