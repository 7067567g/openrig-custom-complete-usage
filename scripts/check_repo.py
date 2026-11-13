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
    "CHANGELOG.md", "VERSION", "CITATION.cff", "VALIDATION.md", "VALIDATION.zh-CN.md", "SECURITY.md", "CONTRIBUTING.md",
    "docs/INDEX.md", "docs/QUICKSTART.md", "docs/QUICKSTART.zh-CN.md",
    "docs/ARCHITECTURE.md", "docs/ARCHITECTURE.zh-CN.md",
    "docs/MULTI-ROUND.md", "docs/MULTI-ROUND.zh-CN.md",
    "docs/OPENRIG.md", "docs/OPENRIG.zh-CN.md",
    "docs/PUBLISHING.md", "docs/PUBLISHING.zh-CN.md",
    "docs/VERSIONING.md", "docs/VERSIONING.zh-CN.md",
    "docs/ENVIRONMENT.md", "docs/ENVIRONMENT.zh-CN.md",
    "docs/REPRODUCIBILITY.md", "docs/REPRODUCIBILITY.zh-CN.md",
    "docs/LIMITATIONS.md", "docs/LIMITATIONS.zh-CN.md",
    "docs/REFERENCE.md", "docs/REFERENCE.zh-CN.md",
    "docs/CONCEPTS.md", "docs/CONCEPTS.zh-CN.md",
    "docs/MEMORY-SAFETY.md", "docs/MEMORY-SAFETY.zh-CN.md",
    "docs/cases/03-memory-incident.md", "docs/cases/03-memory-incident.zh-CN.md",
    "examples/memory-limits/README.md", "examples/memory-limits/README.zh-CN.md",
    "examples/memory-limits/seat-launch.example.sh", "examples/memory-limits/guard.example.sh",
    "docs/cases/README.md", "docs/cases/README.zh-CN.md",
    "docs/cases/01-render-smoke.md", "docs/cases/01-render-smoke.zh-CN.md",
    "docs/releases/v0.1.0.md",
    "roles/MAIN.md", "roles/PMO.md", "roles/TDO.md", "roles/QA.md",
    "roles/SAFETY.md", "roles/common-contract.md", "roles/delegation-briefs.md",
    "scripts/wf.py", "scripts/wf_close_lint.py", "scripts/doc_consistency.py",
    "scripts/issues.py", "scripts/openrig_preflight.py", "scripts/openrig_smoke.py", "scripts/check_content.py", "scripts/check_sanitization.py", "scripts/generate_round_cases.py",
    "scripts/adapters/headless.py",
    "templates/specialized/openrig-workflow-master/SPEC.md",
    "templates/specialized/openrig-workflow-master/PREFLIGHT.md",
    "templates/specialized/openrig-workflow-master/render_master.py",
    "templates/specialized/openrig-workflow-master/tools/openrig_bridge.py",
    "sctg-kit/sctg.py", "sctg-kit/gates/g0_schema.py", "sctg-kit/gates/g1_scope.py",
    "sctg-kit/gates/g2_evidence.py", "sctg-kit/gates/g3_command.py",
    "sctg-kit/schemas/submission.schema.json",
    "examples/openrig-minimal/README.md", "examples/openrig-minimal/README.zh-CN.md",
    "examples/sctg-minimal/run_demo.py",
    "examples/multi-card/run_demo.py", "examples/decision/run_demo.py",
    "examples/multi-card/README.md", "examples/decision/README.md",
    "examples/rollback/README.md", "examples/two-seat-handoff/README.md",
    "examples/rollback/run_demo.py", "examples/two-seat-handoff/run_demo.py",
    "examples/README.md", "examples/README.zh-CN.md",
    "examples/live-run/README.md", "examples/live-run/README.zh-CN.md",
    "examples/round-cases/README.md", "examples/round-cases/README.zh-CN.md",
    "examples/round-cases/case-12-rounds-hardening/run/ROUNDS.json",
    "examples/live-run/OPENRIG-STATE.json",
    "examples/multi-round/README.md", "examples/multi-round/README.zh-CN.md",
    "examples/sanitized-run/README.md", "examples/sanitized-run/README.zh-CN.md",
    "tests/test_public_repo.py", "tests/test_version.py", "tests/test_examples.py", "tests/test_round_cases.py", "tests/test_wf.py",
    ".github/workflows/ci.yml", ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.md", ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/CODEOWNERS", ".github/dependabot.yml",
    "reports/openrig_smoke.json", "reports/openrig_smoke.md",
    "reports/content_gap_audit.md", "reports/content_gap_audit.zh-CN.md",
    "reports/openrig_analyst_report.md",
]
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".agents"}
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
