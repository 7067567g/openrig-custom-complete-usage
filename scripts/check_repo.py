#!/usr/bin/env python3
"""Public-repo hygiene check for the complete OpenRig usage repository."""
from __future__ import annotations
import json, py_compile, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md", "README.zh-CN.md", "LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md",
    "requirements.txt", "requirements-dev.txt", ".gitignore", ".editorconfig", "ruff.toml", "mypy.ini", ".pre-commit-config.yaml",
    "WORKFLOW.md", "WORKFLOW-TAGS.md", "AGENTS.md", "Makefile", "pyproject.toml",
    "CHANGELOG.md", "VERSION", "CITATION.cff", "SECURITY.md", "CONTRIBUTING.md",
    "docs/QUICKSTART.md", "docs/ARCHITECTURE.md", "docs/MULTI-ROUND.md",
    "docs/OPENRIG.md", "docs/PUBLISHING.md", "docs/VERSIONING.md",
    "docs/ENVIRONMENT.md", "docs/REPRODUCIBILITY.md", "docs/LIMITATIONS.md",
    "docs/releases/v0.1.0.md",
    "roles/MAIN.md", "roles/PMO.md", "roles/TDO.md", "roles/QA.md",
    "roles/SAFETY.md", "roles/common-contract.md", "roles/delegation-briefs.md",
    "scripts/wf.py", "scripts/wf_close_lint.py", "scripts/doc_consistency.py",
    "scripts/issues.py", "scripts/openrig_preflight.py", "scripts/openrig_smoke.py",
    "scripts/adapters/headless.py",
    "templates/specialized/openrig-workflow-master/SPEC.md",
    "templates/specialized/openrig-workflow-master/PREFLIGHT.md",
    "templates/specialized/openrig-workflow-master/render_master.py",
    "templates/specialized/openrig-workflow-master/tools/openrig_bridge.py",
    "sctg-kit/sctg.py", "sctg-kit/gates/g0_schema.py", "sctg-kit/gates/g1_scope.py",
    "sctg-kit/gates/g2_evidence.py", "sctg-kit/gates/g3_command.py",
    "sctg-kit/schemas/submission.schema.json",
    "examples/openrig-minimal/README.md", "examples/multi-round/README.md",
    "tests/test_public_repo.py", "tests/test_version.py", "tests/test_wf.py",
    ".github/workflows/ci.yml", ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.md", ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/CODEOWNERS", ".github/dependabot.yml",
]
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TEXT_EXT = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".toml", ".cfg", ".cff", ".sh"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
LOCAL_PATH_PATTERNS = [
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\"),
]

def files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p

def main() -> int:
    errors = []
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required file: {rel}")
    for p in files():
        rel = p.relative_to(ROOT)
        if p.suffix not in TEXT_EXT:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                errors.append(f"secret-like pattern in {rel}")
                break
        for pat in LOCAL_PATH_PATTERNS:
            if pat.search(text):
                errors.append(f"local absolute path in {rel}")
                break
    try:
        import tomllib
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        project_version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        if version != project_version:
            errors.append(f"VERSION {version!r} != pyproject version {project_version!r}")
    except Exception as exc:
        errors.append(f"version consistency check failed: {exc}")
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for p in files():
        if p.suffix != ".md":
            continue
        text = p.read_text(encoding="utf-8")
        for target in link_re.findall(text):
            target = target.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (p.parent / target).resolve().exists():
                errors.append(f"broken link in {p.relative_to(ROOT)}: {target}")
    for p in files():
        if p.suffix == ".py":
            try:
                py_compile.compile(str(p), doraise=True)
            except Exception as exc:
                errors.append(f"python compile failed: {p.relative_to(ROOT)}: {exc}")
    print(json.dumps({"verdict": "PASS" if not errors else "FAIL", "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
