#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only close-semantics linter for workflow-group runs.

Usage:
  python3 workflow-group/scripts/wf_close_lint.py --run <run-id>
  python3 workflow-group/scripts/wf_close_lint.py --all
  python3 workflow-group/scripts/wf_close_lint.py --all --json
  python3 workflow-group/scripts/wf_close_lint.py --all \
      --acceptances reports/close-semantics-20261111/ACCEPTANCES.json

Exit codes:
  0: no ERROR findings (WARN is allowed)
  1: at least one ERROR finding, or invalid CLI/input root

The checker is intentionally dependency-free: it uses only the Python standard
library.  ISSUES.xlsx is parsed directly from `xl/worksheets/sheet1.xml`, with
optional `xl/sharedStrings.xml` support, so openpyxl is not required.

Checks:
  * required run files: PROJECT.md / DECISIONS.md / ISSUES.xlsx / STATUS-Round-*.md
  * PROJECT state=closed:
      - no 新建 / 处理中 / 待主会话 issue rows
      - 挂起/已决议 S1/S2 rows must carry an existing D-xxx 关联决策ID
      - DECISIONS must contain at least one D-xxx whose 状态 contains
        达成 / 终止 / 关闭
      - PROJECT should contain a 残余风险/承接 block with owner / 去向 /
        最晚复核轮 (WARN for legacy compatibility)
  * wf-doc headers on PROJECT/DECISIONS/STATUS and any nested md that
    carries a wf-doc header must contain run/round/doc/owner/state/updated
  * STATUS state=qa-done/closed must not retain progress rows whose status is
    进行中 or 阻塞

An acceptance manifest may downgrade only exactly matched ERROR findings to
WARN.  Match key is (run_id, code, issue_id); unmatched findings are never
downgraded.  The required acceptance fields are run_id/code/issue_id/
decision_id/owner/destination/review_round/reason.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

SCRIPT_PATH = Path(__file__).resolve()
WORKFLOW_GROUP_DIR = SCRIPT_PATH.parent.parent
DEFAULT_RUNS_ROOT = WORKFLOW_GROUP_DIR / "runs"

ACTIVE_OPEN_STATUSES = {"新建", "处理中", "待主会话"}
SUSPENDED_STATUS = "挂起"
RESOLVED_STATUS = "已决议"
CLOSED_STATUS = "已关闭"
TERMINAL_STATUS_WORDS = ("达成", "终止", "关闭")
REQUIRED_DOCS = ("PROJECT.md", "DECISIONS.md", "ISSUES.xlsx")
WF_DOC_FIELDS = ("run", "round", "doc", "owner", "state", "updated")
ISSUE_REQUIRED_HEADERS = ("ID", "严重度", "状态", "关联决策ID")


@dataclass
class Finding:
    level: str
    code: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    issue_id: str = ""
    accepted: bool = False
    accepted_by: Optional[str] = None


@dataclass
class RunReport:
    run_id: str
    path: str
    project_state: Optional[str] = None
    findings: List[Finding] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.level == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.level == "WARN")

    @property
    def ok(self) -> bool:
        return self.error_count == 0


@dataclass
class IssueLedger:
    path: Path
    headers: Dict[str, str] = field(default_factory=dict)
    rows: List[Dict[str, str]] = field(default_factory=list)
    error: Optional[str] = None
    warning: Optional[str] = None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _cell_text(cell: ET.Element, shared_strings: Sequence[str]) -> str:
    """Return a cell's display text without openpyxl."""
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        # Rich text may contain multiple <t> runs.
        parts = []
        for node in cell.iter():
            if _local_name(node.tag) == "t" and node.text:
                parts.append(node.text)
        return "".join(parts)

    value_node = None
    for node in cell:
        if _local_name(node.tag) == "v":
            value_node = node
            break
    if value_node is None or value_node.text is None:
        return ""

    raw = value_node.text
    if cell_type == "s":
        try:
            return shared_strings[int(raw)]
        except (ValueError, IndexError):
            return ""
    return raw


def _col_letters(ref: str) -> str:
    return "".join(ch for ch in ref if ch.isalpha())


def _read_shared_strings(archive: zipfile.ZipFile) -> List[str]:
    try:
        raw = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    values: List[str] = []
    for si in root:
        if _local_name(si.tag) != "si":
            continue
        parts = []
        for node in si.iter():
            if _local_name(node.tag) == "t" and node.text:
                parts.append(node.text)
        values.append("".join(parts))
    return values


def read_issue_ledger(path: Path) -> IssueLedger:
    """Read sheet1.xml + sharedStrings.xml directly from an xlsx archive.

    A valid workbook with no rows is treated as an empty ledger (zero issues),
    not as an unreadable file.  A broken zip/XML or a ledger missing required
    columns produces `error` and never raises.
    """
    ledger = IssueLedger(path=path)
    if not path.exists():
        ledger.error = "ISSUES.xlsx does not exist"
        return ledger

    try:
        with zipfile.ZipFile(path) as archive:
            try:
                sheet_raw = archive.read("xl/worksheets/sheet1.xml")
            except KeyError:
                ledger.error = "xl/worksheets/sheet1.xml not found in ISSUES.xlsx"
                return ledger
            shared = _read_shared_strings(archive)
    except (zipfile.BadZipFile, OSError) as exc:
        ledger.error = f"cannot open ISSUES.xlsx: {exc}"
        return ledger

    try:
        workbook = ET.fromstring(sheet_raw)
    except ET.ParseError as exc:
        ledger.error = f"cannot parse xl/worksheets/sheet1.xml: {exc}"
        return ledger

    rows: List[Dict[str, str]] = []
    for row_node in workbook.iter():
        if _local_name(row_node.tag) != "row":
            continue
        row: Dict[str, str] = {}
        for cell in row_node:
            if _local_name(cell.tag) != "c":
                continue
            ref = cell.attrib.get("r", "")
            col = _col_letters(ref)
            if not col:
                continue
            row[col] = _cell_text(cell, shared).strip()
        if any(v != "" for v in row.values()):
            rows.append(row)

    if not rows:
        # Empty worksheet: valid empty ledger.
        ledger.warning = "ISSUES.xlsx has no rows"
        return ledger

    # Find the header row by content, not by assuming row 1.
    header_row: Optional[Dict[str, str]] = None
    data_start = 0
    for index, candidate in enumerate(rows):
        values = set(candidate.values())
        if "ID" in values and "状态" in values and "严重度" in values:
            header_row = candidate
            data_start = index + 1
            break

    if header_row is None:
        ledger.error = "ISSUES.xlsx header row not found"
        return ledger

    header_by_name: Dict[str, str] = {}
    for col, value in header_row.items():
        if value:
            header_by_name[value] = col

    missing = [name for name in ISSUE_REQUIRED_HEADERS if name not in header_by_name]
    if missing:
        ledger.error = "ISSUES.xlsx missing required columns: " + ", ".join(missing)
        return ledger

    # Expose a logical header map to callers (field name -> sheet column).
    ledger.headers = header_by_name
    for raw_row in rows[data_start:]:
        logical = {
            name: raw_row.get(col, "").strip()
            for name, col in header_by_name.items()
        }
        if any(logical.values()):
            ledger.rows.append(logical)
    return ledger


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_wf_doc_header(text: str) -> Tuple[Optional[Dict[str, str]], Optional[int]]:
    match = re.search(r"<!--\s*wf-doc\s*(.*?)\s*-->", text, re.S)
    if not match:
        return None, None
    fields: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        fm = re.match(r"^\s*([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*$", line)
        if fm:
            fields[fm.group(1).strip().lower()] = fm.group(2).strip()
    line_no = text[: match.start()].count("\n") + 1
    return fields, line_no


def decision_ids(text: str) -> set:
    return set(re.findall(r"(?m)^###\s+(D-\d+)\b", text))


def _decision_blocks(text: str) -> Iterable[Tuple[str, str]]:
    """Yield (D-id, body) for every `### D-xxx...` block."""
    header_re = re.compile(r"(?m)^###\s+(D-\d+)\b[^\n]*\n")
    matches = list(header_re.finditer(text))
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        # Stop at the next section heading if it is not another D entry.
        next_section = re.search(r"(?m)^##\s+", text[body_start:body_end])
        if next_section:
            body_end = body_start + next_section.start()
        yield match.group(1), text[body_start:body_end]


def has_terminal_decision(text: str) -> bool:
    # The status marker may be at the start of a bullet, or embedded in a
    # compact line such as "**编制**：... ｜ **状态**：达成（终止）".
    status_re = re.compile(r"\*\*状态(?:[：:]|\*\*\s*[：:])")
    for _did, body in _decision_blocks(text):
        for line in body.splitlines():
            status_match = status_re.search(line)
            if not status_match:
                continue
            tail = line[status_match.end():]
            if any(word in tail for word in TERMINAL_STATUS_WORDS):
                return True
    return False


def extract_progress_entries(text: str) -> List[Tuple[int, str, str]]:
    """Return (line_no, status_cell, full_line) for progress table rows.

    The preferred source is the `wf:progress` marker region.  For legacy files
    without markers, fall back to the whole document; table separator/header
    rows are ignored and the last cell is treated as the status cell.
    """
    marker = re.search(
        r"<!--\s*wf:progress:start\s*-->(.*?)<!--\s*wf:progress:end\s*-->",
        text,
        re.S,
    )
    if marker:
        region = marker.group(1)
        base_line = text[: marker.start(1)].count("\n") + 1
    else:
        region = text
        base_line = 1

    entries: List[Tuple[int, str, str]] = []
    for offset, raw_line in enumerate(region.splitlines(), start=base_line):
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        if all(re.fullmatch(r"[\s:\-]*", cell or "") for cell in cells):
            continue
        if cells[0] in ("时间", ""):
            continue
        status = cells[-1]
        if not status:
            continue
        entries.append((offset, status, line))
    return entries


def _has_residual_contract(text: str) -> Tuple[bool, bool]:
    """Return (keyword_found, complete).

    A residual/承接 block is considered complete only when the nearby region
    contains owner, 去向 and 最晚复核轮 labels.
    """
    lines = text.splitlines()
    keyword_indexes = [
        index
        for index, line in enumerate(lines)
        if "残余风险" in line or "承接" in line or "residual" in line.lower()
    ]
    if not keyword_indexes:
        return False, False

    for index in keyword_indexes:
        end = index + 1
        while end < len(lines) and not re.match(r"^#{1,6}\s", lines[end]):
            end += 1
        if end == index + 1:
            # The keyword was a heading; include its following section.
            while end < len(lines) and not re.match(r"^#{1,6}\s", lines[end]):
                end += 1
            if end == index + 1:
                end = min(len(lines), index + 40)
        else:
            # A bullet/line may only be one line; include a small following
            # context because many legacy files continue the fields below.
            end = min(len(lines), max(end, index + 20))
        block = "\n".join(lines[index:end]).lower()
        has_owner = "owner" in block
        has_destination = "去向" in block
        has_review = "最晚复核轮" in block
        if has_owner and has_destination and has_review:
            return True, True
    return True, False


def _norm(value: Optional[str]) -> str:
    return (value or "").strip()


def _row_decision_ids(value: str) -> List[str]:
    return re.findall(r"D-\d+", value or "")


def _add(
    findings: List[Finding],
    level: str,
    code: str,
    message: str,
    file: Optional[Path] = None,
    line: Optional[int] = None,
    issue_id: str = "",
) -> None:
    findings.append(
        Finding(
            level=level,
            code=code,
            message=message,
            file=str(file) if file is not None else None,
            line=line,
            issue_id=issue_id,
        )
    )


def lint_run(run_dir: Path, reports_root: Optional[Path] = None) -> RunReport:
    """Lint one run directory. Never raises for bad content."""
    run_dir = Path(run_dir)
    report = RunReport(
        run_id=run_dir.name,
        path=str(run_dir),
        stats={
            "issue_rows": 0,
            "active_open_rows": 0,
            "open_s1_s2": 0,
            "suspended_s1_s2": 0,
            "resolved_s1_s2": 0,
            "unaccepted_s1_s2": 0,
            "status_files": 0,
            "status_conflict_files": 0,
        },
    )

    if not run_dir.is_dir():
        _add(report.findings, "ERROR", "run_dir_missing", "run directory does not exist", run_dir)
        return report

    paths = {name: run_dir / name for name in REQUIRED_DOCS}
    for name, path in paths.items():
        if not path.exists():
            _add(report.findings, "ERROR", "required_file_missing", f"missing required file: {name}", path)

    project_path = paths["PROJECT.md"]
    decisions_path = paths["DECISIONS.md"]
    issues_path = paths["ISSUES.xlsx"]
    status_paths = sorted(run_dir.glob("STATUS-Round-*.md"))
    if not status_paths:
        _add(
            report.findings,
            "ERROR",
            "required_file_missing",
            "missing required file: STATUS-Round-*.md",
            run_dir,
        )

    project_text = read_text(project_path) if project_path.exists() else ""
    decisions_text = read_text(decisions_path) if decisions_path.exists() else ""
    project_header, project_header_line = parse_wf_doc_header(project_text)
    if project_header:
        report.project_state = _norm(project_header.get("state")) or None

    # Validate wf-doc headers on canonical docs.  Nested md files are checked
    # only when they actually opt into the wf-doc convention.
    canonical = {project_path, decisions_path, *status_paths}
    checked = set()
    for path in [project_path, decisions_path, *status_paths]:
        if not path.exists():
            continue
        text = read_text(path)
        header, line_no = parse_wf_doc_header(text)
        checked.add(path)
        if header is None:
            _add(
                report.findings,
                "WARN",
                "wf_doc_header_missing",
                "canonical document has no wf-doc header",
                path,
                1,
            )
            continue
        missing = [field for field in WF_DOC_FIELDS if not _norm(header.get(field))]
        if missing:
            _add(
                report.findings,
                "WARN",
                "wf_doc_fields_missing",
                "wf-doc header missing field(s): " + ", ".join(missing),
                path,
                line_no,
            )
    # Also validate any nested markdown document that opts into wf-doc.
    for path in sorted(run_dir.rglob("*.md")):
        if path in checked or not path.is_file():
            continue
        text = read_text(path)
        if "<!-- wf-doc" not in text:
            continue
        header, line_no = parse_wf_doc_header(text)
        if header is None:
            _add(report.findings, "WARN", "wf_doc_header_malformed", "malformed wf-doc header", path, 1)
            continue
        missing = [field for field in WF_DOC_FIELDS if not _norm(header.get(field))]
        if missing:
            _add(
                report.findings,
                "WARN",
                "wf_doc_fields_missing",
                "wf-doc header missing field(s): " + ", ".join(missing),
                path,
                line_no,
            )

    # ISSUES.xlsx parsing and issue-level statistics.
    ledger: Optional[IssueLedger] = None
    if issues_path.exists():
        ledger = read_issue_ledger(issues_path)
        if ledger.error:
            _add(report.findings, "ERROR", "issues_ledger_invalid", ledger.error, issues_path)
        elif ledger.warning:
            _add(report.findings, "WARN", "issues_ledger_empty", ledger.warning, issues_path)

    defined_decisions = decision_ids(decisions_text)
    issue_rows: List[Dict[str, str]] = ledger.rows if ledger is not None and not ledger.error else []
    report.stats["issue_rows"] = len(issue_rows)

    for row in issue_rows:
        severity = _norm(row.get("严重度"))
        status = _norm(row.get("状态"))
        if status in ACTIVE_OPEN_STATUSES:
            report.stats["active_open_rows"] += 1
            if severity in ("S1", "S2"):
                report.stats["open_s1_s2"] += 1
        if severity in ("S1", "S2") and status == SUSPENDED_STATUS:
            report.stats["suspended_s1_s2"] += 1
        if severity in ("S1", "S2") and status == RESOLVED_STATUS:
            report.stats["resolved_s1_s2"] += 1

    if report.project_state == "closed":
        # 1) No active-open issue rows.
        if ledger is not None and not ledger.error:
            for row in issue_rows:
                severity = _norm(row.get("严重度"))
                status = _norm(row.get("状态"))
                issue_id = _norm(row.get("ID")) or "?"
                if status in ACTIVE_OPEN_STATUSES:
                    _add(
                        report.findings,
                        "ERROR",
                        "closed_has_active_issue",
                        f"{issue_id} ({severity or '?'}) is still active open: {status}",
                        issues_path,
                        issue_id=issue_id,
                    )

            # 2) Suspended/resolved S1/S2 rows need a real D-xxx link.
            for row in issue_rows:
                severity = _norm(row.get("严重度"))
                status = _norm(row.get("状态"))
                if severity not in ("S1", "S2") or status not in (SUSPENDED_STATUS, RESOLVED_STATUS):
                    continue
                issue_id = _norm(row.get("ID")) or "?"
                decision_cell = _norm(row.get("关联决策ID"))
                refs = _row_decision_ids(decision_cell)
                valid = bool(refs) and all(ref in defined_decisions for ref in refs)
                if not valid:
                    report.stats["unaccepted_s1_s2"] += 1
                    _add(
                        report.findings,
                        "ERROR",
                        "s1_s2_decision_missing",
                        f"{issue_id} ({severity}, {status}) lacks a valid D-xxx 关联决策ID; got {decision_cell or '<empty>'}",
                        issues_path,
                        issue_id=issue_id,
                    )

        # 3) A closed run must have a terminal decision entry.
        if decisions_path.exists() and not has_terminal_decision(decisions_text):
            _add(
                report.findings,
                "ERROR",
                "terminal_decision_missing",
                "PROJECT is closed but DECISIONS has no D-xxx whose 状态 contains 达成/终止/关闭",
                decisions_path,
            )

        # 4) Residual/承接 contract is a WARN for legacy compatibility.
        if project_path.exists():
            keyword_found, complete = _has_residual_contract(project_text)
            if not keyword_found:
                _add(
                    report.findings,
                    "WARN",
                    "residual_contract_missing",
                    "PROJECT has no 残余风险/承接 block with owner/去向/最晚复核轮",
                    project_path,
                )
            elif not complete:
                _add(
                    report.findings,
                    "WARN",
                    "residual_contract_incomplete",
                    "PROJECT 残余风险/承接 block lacks owner/去向/最晚复核轮 field(s)",
                    project_path,
                )

    # STATUS state vs table content.
    for status_path in status_paths:
        report.stats["status_files"] += 1
        status_text = read_text(status_path)
        header, _line_no = parse_wf_doc_header(status_text)
        state = _norm(header.get("state")) if header else ""
        if state not in ("qa-done", "closed"):
            continue
        bad_rows = [
            (line_no, value)
            for line_no, value, _line in extract_progress_entries(status_text)
            if value.startswith("进行中") or value.startswith("阻塞")
        ]
        if bad_rows:
            report.stats["status_conflict_files"] += 1
            locations = ", ".join(f"line {line_no}:{value}" for line_no, value in bad_rows[:8])
            if len(bad_rows) > 8:
                locations += f", ... (+{len(bad_rows) - 8})"
            _add(
                report.findings,
                "ERROR",
                "status_has_unfinished_rows",
                f"STATUS declares state={state} but still has 进行中/阻塞 rows: {locations}",
                status_path,
                bad_rows[0][0],
            )

    return report


ACCEPTANCE_FIELDS = (
    "run_id",
    "code",
    "issue_id",
    "decision_id",
    "owner",
    "destination",
    "review_round",
    "reason",
)


def load_acceptances(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    """Load and validate an acceptance manifest.

    Expected shape: a JSON list, or an object with an ``acceptances`` list.
    Every entry must contain all ACCEPTANCE_FIELDS.  ``issue_id`` may be an
    empty string for structural findings; all other values must be non-empty.
    """
    if not path.exists():
        return [], [f"acceptance manifest does not exist: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"cannot read acceptance manifest: {exc}"]
    if isinstance(data, dict):
        data = data.get("acceptances")
    if not isinstance(data, list):
        return [], ['acceptance manifest must be a list or {"acceptances": [...]}']

    entries: List[Dict[str, str]] = []
    errors: List[str] = []
    seen = set()
    for index, raw in enumerate(data):
        where = f"entry {index}"
        if not isinstance(raw, dict):
            errors.append(f"{where}: must be an object")
            continue
        missing = [field for field in ACCEPTANCE_FIELDS if field not in raw]
        if missing:
            errors.append(f"{where}: missing field(s): {', '.join(missing)}")
            continue
        entry = {field: str(raw.get(field, "")).strip() for field in ACCEPTANCE_FIELDS}
        empty = [field for field in ACCEPTANCE_FIELDS if field != "issue_id" and not entry[field]]
        if empty:
            errors.append(f"{where}: empty field(s): {', '.join(empty)}")
            continue
        if not re.fullmatch(r"D-\d+", entry["decision_id"]):
            errors.append(f"{where}: decision_id is not D-xxx: {entry['decision_id']}")
            continue
        key = (entry["run_id"], entry["code"], entry["issue_id"])
        if key in seen:
            errors.append(f"{where}: duplicate run_id/code/issue_id: {key}")
            continue
        seen.add(key)
        entries.append(entry)
    return entries, errors


def apply_acceptances(
    reports: Sequence[RunReport],
    acceptances: Sequence[Dict[str, str]],
) -> Dict[str, int]:
    """Downgrade only exactly matched ERROR findings to WARN.

    A match is (run_id, code, issue_id).  This deliberately does not match by
    substring, severity, message or file, so a manifest cannot broaden itself
    to newer/unlisted findings with a different issue id or code.
    """
    index = {
        (entry["run_id"], entry["code"], entry["issue_id"]): entry
        for entry in acceptances
    }
    used = set()
    accepted_errors = 0
    for report in reports:
        for finding in report.findings:
            if finding.level != "ERROR":
                continue
            key = (report.run_id, finding.code, finding.issue_id)
            entry = index.get(key)
            if entry is None:
                continue
            finding.level = "WARN"
            finding.accepted = True
            finding.accepted_by = entry["decision_id"]
            finding.message = (
                finding.message
                + f" [accepted by {entry['decision_id']}; owner={entry['owner']}; "
                + f"destination={entry['destination']}; review_round={entry['review_round']}]"
            )
            used.add(key)
            accepted_errors += 1
    return {
        "accepted_errors": accepted_errors,
        "acceptances_loaded": len(acceptances),
        "acceptances_used": len(used),
        "acceptances_unused": len(index) - len(used),
    }


def _report_to_json(report: RunReport) -> Dict[str, object]:
    return {
        "run_id": report.run_id,
        "path": report.path,
        "project_state": report.project_state,
        "ok": report.ok,
        "errors": report.error_count,
        "warnings": report.warning_count,
        "stats": report.stats,
        "findings": [asdict(item) for item in report.findings],
    }


def summarize(
    reports: Sequence[RunReport],
    acceptance_stats: Optional[Dict[str, int]] = None,
) -> Dict[str, int]:
    def total(key: str) -> int:
        return sum(report.stats.get(key, 0) for report in reports)

    closed = [report for report in reports if report.project_state == "closed"]
    stats_accept = acceptance_stats or {}
    return {
        "runs_scanned": len(reports),
        "closed_runs": len(closed),
        "closed_violation_runs": sum(1 for report in closed if report.error_count > 0),
        "errors": sum(report.error_count for report in reports),
        "accepted_errors": stats_accept.get("accepted_errors", 0),
        "unaccepted_errors": sum(report.error_count for report in reports),
        "acceptances_loaded": stats_accept.get("acceptances_loaded", 0),
        "acceptances_used": stats_accept.get("acceptances_used", 0),
        "acceptances_unused": stats_accept.get("acceptances_unused", 0),
        "warnings": sum(report.warning_count for report in reports),
        "issue_rows": total("issue_rows"),
        "active_open_rows": total("active_open_rows"),
        "open_s1_s2": total("open_s1_s2"),
        "suspended_s1_s2": total("suspended_s1_s2"),
        "resolved_s1_s2": total("resolved_s1_s2"),
        "unaccepted_s1_s2": total("unaccepted_s1_s2"),
        "status_files": total("status_files"),
        "status_conflict_files": total("status_conflict_files"),
    }


def print_report(report: RunReport) -> None:
    for finding in report.findings:
        location = ""
        if finding.file:
            location = f" {finding.file}"
            if finding.line is not None:
                location += f":{finding.line}"
        print(f"{finding.level} [{report.run_id}] [{finding.code}]{location}: {finding.message}")
    if not report.findings:
        print(f"OK [{report.run_id}] no findings")


def run_all(runs_root: Path) -> List[RunReport]:
    reports = []
    for run_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        reports.append(lint_run(run_dir))
    return reports


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only workflow-group run close-semantics linter"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", help="run id under the runs root")
    group.add_argument("--all", action="store_true", help="scan every run directory")
    parser.add_argument(
        "--runs-root",
        default=str(DEFAULT_RUNS_ROOT),
        help=f"runs root (default: {DEFAULT_RUNS_ROOT})",
    )
    parser.add_argument(
        "--acceptances",
        help="JSON acceptance manifest; matching ERROR findings are downgraded to WARN",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    runs_root = Path(args.runs_root).expanduser().resolve()
    if not runs_root.is_dir():
        message = f"runs root does not exist or is not a directory: {runs_root}"
        if args.json:
            print(json.dumps({"error": message}, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR [input] [runs_root_invalid]: {message}")
        return 1

    acceptances: List[Dict[str, str]] = []
    acceptance_errors: List[str] = []
    if args.acceptances:
        acceptances, acceptance_errors = load_acceptances(Path(args.acceptances).expanduser().resolve())
    if acceptance_errors:
        if args.json:
            print(json.dumps({"errors": acceptance_errors}, ensure_ascii=False, indent=2))
        else:
            for message in acceptance_errors:
                print(f"ERROR [acceptances] [acceptance_manifest_invalid]: {message}")
        return 1

    if args.all:
        reports = run_all(runs_root)
    else:
        run_dir = runs_root / args.run
        # Still lint so the missing directory is reported as an ERROR.
        reports = [lint_run(run_dir)]

    acceptance_stats = apply_acceptances(reports, acceptances) if acceptances else {
        "accepted_errors": 0,
        "acceptances_loaded": 0,
        "acceptances_used": 0,
        "acceptances_unused": 0,
    }
    summary = summarize(reports, acceptance_stats)
    if args.json:
        payload = {
            "runs": [_report_to_json(report) for report in reports],
            "summary": summary,
            "result": "FAIL" if summary["errors"] else ("PASS_WITH_WARNINGS" if summary["warnings"] else "PASS"),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print_report(report)
        print("")
        print(
            "SUMMARY "
            f"runs={summary['runs_scanned']} "
            f"closed={summary['closed_runs']} "
            f"closed_violation_runs={summary['closed_violation_runs']} "
            f"open_s1_s2={summary['open_s1_s2']} "
            f"suspended_s1_s2={summary['suspended_s1_s2']} "
            f"unaccepted_s1_s2={summary['unaccepted_s1_s2']} "
            f"status_conflict_files={summary['status_conflict_files']} "
            f"errors={summary['errors']} warnings={summary['warnings']} "
            f"accepted_errors={summary['accepted_errors']} "
            f"unaccepted_errors={summary['unaccepted_errors']} "
            f"acceptances_loaded={summary['acceptances_loaded']} "
            f"used={summary['acceptances_used']} unused={summary['acceptances_unused']}"
        )
        print(
            "RESULT "
            + ("FAIL" if summary["errors"] else ("PASS_WITH_WARNINGS" if summary["warnings"] else "PASS"))
        )

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
