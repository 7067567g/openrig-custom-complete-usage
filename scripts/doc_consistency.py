#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""workflow-group 文档一致性校验（仅标准库）。

校验项：
1. ``templates/specialized/*/``（含 SPEC.md 的目录）与 BASELINE-MAP.md 行一一对应；
2. ``templates/baseline/*`` 与 REGISTRY.json 的 id 集合一致且数量为 9；
3. WORKFLOW-TAGS.md 顶部的 canonical/baseline/specialized 声明与实测目录数一致；
4. WORKFLOW.md 内 ``§x.y`` 引用能解析到标题或编号项；
5. roles/*.md 内的 ``wf.py state`` 状态迁移命令是否带 ``--by``（WARN）。

用法::

    python3 workflow-group/scripts/doc_consistency.py --check

退出码：存在 ERROR 时为 1，否则为 0。WARN 不阻塞。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ERROR = "ERROR"
WARN = "WARN"

# canonical 复合类型基准模板的冻结数量；新增/删除 baseline 时必须显式更新本常量
# 并同步 REGISTRY.json、REGISTRY.md、FREEZE-NOTES.md 与 WORKFLOW-TAGS.md。
EXPECTED_BASELINE_COUNT = 9

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Finding:
    """一条校验结果。"""

    level: str
    code: str
    message: str


def _subdirs(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name)


def parse_baseline_map(map_path: Path) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """解析 BASELINE-MAP.md 的登记行，返回 (name -> (baseline, contracts), 重复名)。

    只接受以 ``| `name` |`` 开头的行；表头/说明行自动忽略。
    """

    rows: dict[str, tuple[str, str]] = {}
    duplicates: list[str] = []
    if not map_path.is_file():
        return rows, duplicates
    for line in map_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        name = cells[0].strip("`")
        if name in rows:
            duplicates.append(name)
        rows[name] = (cells[1].strip("`"), cells[2])
    return rows, duplicates


def check_specialized_coverage(root: Path) -> list[Finding]:
    """specialized 目录与 BASELINE-MAP 行一一对应。"""

    findings: list[Finding] = []
    specialized = root / "templates" / "specialized"
    entry_map = specialized / "BASELINE-MAP.md"
    if not entry_map.is_file():
        return [Finding(ERROR, "specialized-map", f"缺少映射文件: {entry_map}")]

    names = {
        p.name for p in _subdirs(specialized) if (p / "SPEC.md").is_file()
    }
    rows, duplicates = parse_baseline_map(entry_map)
    for name in sorted(set(duplicates)):
        findings.append(
            Finding(ERROR, "specialized-map", f"BASELINE-MAP.md 重复登记: {name}")
        )
    for name in sorted(names - set(rows)):
        findings.append(
            Finding(
                ERROR,
                "specialized-map",
                f"templates/specialized/{name}/SPEC.md 存在，但 BASELINE-MAP.md 缺行",
            )
        )
    for name in sorted(set(rows) - names):
        findings.append(
            Finding(
                ERROR,
                "specialized-map",
                f"BASELINE-MAP.md 登记了 {name}，但 templates/specialized/{name}/SPEC.md 不存在",
            )
        )
    return findings


def check_baseline_registry(root: Path) -> list[Finding]:
    """baseline 目录、REGISTRY.json id 集合与冻结数量三者一致。"""

    findings: list[Finding] = []
    baseline = root / "templates" / "baseline"
    registry_path = baseline / "REGISTRY.json"
    dirs = {p.name for p in _subdirs(baseline)}

    if not registry_path.is_file():
        return [Finding(ERROR, "baseline-registry", f"缺少注册表: {registry_path}")]
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            Finding(ERROR, "baseline-registry", f"REGISTRY.json 不是合法 JSON: {exc}")
        ]

    items = registry.get("baselines")
    if not isinstance(items, list):
        return [Finding(ERROR, "baseline-registry", "REGISTRY.json 缺少 baselines 数组")]
    ids = {item.get("id") for item in items if isinstance(item, dict)}
    if None in ids:
        findings.append(
            Finding(ERROR, "baseline-registry", "REGISTRY.json 存在无 id 的 baseline 条目")
        )
        ids.discard(None)

    for name in sorted(dirs - ids):
        findings.append(
            Finding(
                ERROR,
                "baseline-registry",
                f"templates/baseline/{name}/ 存在，但 REGISTRY.json 未登记 id",
            )
        )
    for name in sorted(ids - dirs):
        findings.append(
            Finding(
                ERROR,
                "baseline-registry",
                f"REGISTRY.json 登记了 {name}，但 templates/baseline/{name}/ 不存在",
            )
        )
    if len(ids) != EXPECTED_BASELINE_COUNT:
        findings.append(
            Finding(
                ERROR,
                "baseline-count",
                f"baseline 数量应为 {EXPECTED_BASELINE_COUNT}，实际 REGISTRY.json={len(ids)}",
            )
        )
    if len(dirs) != EXPECTED_BASELINE_COUNT:
        findings.append(
            Finding(
                ERROR,
                "baseline-count",
                f"baseline 目录数量应为 {EXPECTED_BASELINE_COUNT}，实际={len(dirs)}",
            )
        )
    for name in sorted(ids & dirs):
        if not (baseline / name / "BASELINE.md").is_file():
            findings.append(
                Finding(
                    ERROR,
                    "baseline-registry",
                    f"templates/baseline/{name}/ 缺 BASELINE.md",
                )
            )
    return findings


def parse_canonical_counts(text: str) -> tuple[int, int, int] | None:
    """从 WORKFLOW-TAGS.md 顶部声明解析 canonical/baseline/specialized 计数。"""

    pattern = re.compile(
        r"canonical\s*=\s*(\d+)\s*[、,，]\s*"
        r"baseline\s*=\s*(\d+)\s*[、,，]\s*"
        r"specialized\s*=\s*(\d+)"
    )
    match = pattern.search(text)
    if not match:
        return None
    return tuple(int(x) for x in match.groups())  # type: ignore[return-value]


def check_workflow_tags_counts(root: Path) -> list[Finding]:
    """WORKFLOW-TAGS.md 顶部时效声明必须与目录实测值一致。"""

    findings: list[Finding] = []
    tags_path = root / "WORKFLOW-TAGS.md"
    if not tags_path.is_file():
        return [Finding(ERROR, "tags-count", f"缺少文件: {tags_path}")]
    text = tags_path.read_text(encoding="utf-8")
    if "不是当前索引" not in text:
        findings.append(
            Finding(
                ERROR,
                "tags-count",
                "WORKFLOW-TAGS.md 顶部必须声明本文件是快照、不是当前索引",
            )
        )
    counts = parse_canonical_counts(text)
    if counts is None:
        return findings + [
            Finding(
                ERROR,
                "tags-count",
                "WORKFLOW-TAGS.md 顶部缺 canonical=<n>、baseline=<n>、specialized=<n> 声明",
            )
        ]

    actual_runs = len(_subdirs(root / "runs"))
    actual_baseline = len(_subdirs(root / "templates" / "baseline"))
    actual_specialized = len(_subdirs(root / "templates" / "specialized"))
    declared = dict(zip(("canonical", "baseline", "specialized"), counts))
    actual = {
        "canonical": actual_runs,
        "baseline": actual_baseline,
        "specialized": actual_specialized,
    }
    for key in ("canonical", "baseline", "specialized"):
        if declared[key] != actual[key]:
            findings.append(
                Finding(
                    ERROR,
                    "tags-count",
                    f"WORKFLOW-TAGS.md 声明 {key}={declared[key]}，实际目录数={actual[key]}",
                )
            )
    return findings


_HEADING_RE = re.compile(r"^(#{1,6})\s+(\d+(?:\.\d+)*)\.?\s+")
# 显式编号项：行首写成 ``1.3 ...`` 这类带点号的编号（普通 ``1.`` 列表项不算锚）。
_DOTTED_ITEM_RE = re.compile(r"^\s*(\d+(?:\.\d+)+)[\.、]?\s+")


def workflow_anchor_ids(text: str) -> set[str]:
    """收集 WORKFLOW.md 中可被 §x.y 引用的标题号与显式编号项号。"""

    anchors: set[str] = set()
    for line in text.splitlines():
        heading = _HEADING_RE.match(line)
        if heading:
            anchors.add(heading.group(2))
            continue
        item = _DOTTED_ITEM_RE.match(line)
        if item:
            anchors.add(item.group(1))
    return anchors


def _check_refs_in_text(
    text: str,
    anchors: set[str],
    source: str,
    *,
    only_workflow_refs: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if only_workflow_refs and "WORKFLOW" not in line:
            continue
        for ref in sorted(set(re.findall(r"§(\d+(?:\.\d+)+)", line))):
            if ref not in anchors:
                findings.append(
                    Finding(
                        ERROR,
                        "workflow-ref",
                        f"{source}:{lineno} 引用了无法解析的 WORKFLOW.md §{ref}",
                    )
                )
    return findings


def check_workflow_references(text: str) -> list[Finding]:
    """校验 WORKFLOW.md 自身的 §x.y 引用均可解析。"""

    return _check_refs_in_text(
        text,
        workflow_anchor_ids(text),
        "WORKFLOW.md",
        only_workflow_refs=False,
    )


def check_canonical_references(root: Path) -> list[Finding]:
    """校验 canonical 文档中对 WORKFLOW.md 的 §x.y 引用均可解析。"""

    workflow = root / "WORKFLOW.md"
    if not workflow.is_file():
        return [Finding(ERROR, "workflow-ref", f"缺少文件: {workflow}")]
    workflow_text = workflow.read_text(encoding="utf-8")
    anchors = workflow_anchor_ids(workflow_text)
    findings = _check_refs_in_text(
        workflow_text,
        anchors,
        "WORKFLOW.md",
        only_workflow_refs=False,
    )
    candidates = [root / name for name in (
        "EXAMPLE.md",
        "AGENTS.md",
        "README.md",
        "DESIGN.md",
        "EVOLUTION.md",
        "WORKFLOW-TAGS.md",
    )]
    candidates.extend(sorted((root / "roles").glob("*.md")))
    for path in candidates:
        if not path.is_file():
            continue
        findings.extend(
            _check_refs_in_text(
                path.read_text(encoding="utf-8"),
                anchors,
                str(path.relative_to(root)),
                only_workflow_refs=True,
            )
        )
    return findings


_STATE_CMD_RE = re.compile(r"wf\.py\s+state\s+<[^>\n]+>")


def check_role_state_by(roles_dir: Path) -> list[Finding]:
    """角色手册中的状态迁移命令缺 --by 时给出 WARN。"""

    findings: list[Finding] = []
    if not roles_dir.is_dir():
        return [Finding(ERROR, "role-by", f"缺少 roles 目录: {roles_dir}")]
    for path in sorted(roles_dir.glob("*.md")):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if _STATE_CMD_RE.search(line) and "--by" not in line:
                findings.append(
                    Finding(
                        WARN,
                        "role-by",
                        f"{path.name}:{lineno} 状态迁移命令缺 --by",
                    )
                )
    return findings


def check_root(root: Path) -> list[Finding]:
    """运行全部检查。"""

    findings: list[Finding] = []
    findings.extend(check_specialized_coverage(root))
    findings.extend(check_baseline_registry(root))
    findings.extend(check_workflow_tags_counts(root))
    findings.extend(check_canonical_references(root))
    findings.extend(check_role_state_by(root / "roles"))
    return findings


def format_findings(findings: Iterable[Finding]) -> str:
    lines = [f"{f.level:<5} [{f.code}] {f.message}" for f in findings]
    errors = sum(1 for f in findings if f.level == ERROR)
    warnings = sum(1 for f in findings if f.level == WARN)
    lines.append(
        f"doc_consistency: {errors} error(s), {warnings} warning(s)"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="workflow-group 文档一致性校验")
    parser.add_argument(
        "--check", action="store_true", help="执行校验（默认行为，保留此参数供 CI 显式调用）"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="workflow-group 根目录（默认取脚本所在 workflow-group）",
    )
    args = parser.parse_args(argv)
    findings = check_root(args.root.resolve())
    print(format_findings(findings))
    return 1 if any(f.level == ERROR for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
