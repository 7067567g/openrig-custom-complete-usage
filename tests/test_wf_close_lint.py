#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for workflow-group/scripts/wf_close_lint.py.

Run with:
    python3 workflow-group/tests/test_wf_close_lint.py

Uses only the Python standard library (unittest/tempfile/zipfile/xml).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True

TEST_PATH = Path(__file__).resolve()
WORKFLOW_GROUP = TEST_PATH.parents[1]
MODULE_PATH = WORKFLOW_GROUP / "scripts" / "wf_close_lint.py"

spec = importlib.util.spec_from_file_location("wf_close_lint", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import {MODULE_PATH}")
close_lint = importlib.util.module_from_spec(spec)
sys.modules["wf_close_lint"] = close_lint
spec.loader.exec_module(close_lint)


HEADERS = [
    "ID",
    "轮次",
    "类型",
    "标题",
    "描述",
    "严重度",
    "状态",
    "责任角色",
    "来源",
    "建议动作",
    "需主会话决策",
    "关联决策ID",
    "创建时间",
    "更新时间",
]


def _col_name(index: int) -> str:
    result = ""
    n = index + 1
    while n:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def write_inline_xlsx(path: Path, rows) -> None:
    """Write a minimal one-sheet xlsx using inline strings only."""
    sheet_rows = []
    for row_index, values in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(values):
            ref = f"{_col_name(col_index)}{row_index}"
            cells.append(
                f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
            )
        sheet_rows.append(f'<row r="{row_index}">' + "".join(cells) + "</row>")

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>" + "".join(sheet_rows) + "</sheetData></worksheet>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def write_shared_strings_xlsx(path: Path, rows) -> None:
    """Write a minimal xlsx whose text cells use sharedStrings.xml."""
    shared = []
    sheet_rows = []
    for row_index, values in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(values):
            text = str(value)
            try:
                shared_index = shared.index(text)
            except ValueError:
                shared_index = len(shared)
                shared.append(text)
            ref = f"{_col_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="s"><v>{shared_index}</v></c>')
        sheet_rows.append(f'<row r="{row_index}">' + "".join(cells) + "</row>")

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>" + "".join(sheet_rows) + "</sheetData></worksheet>"
    )
    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(shared)}" uniqueCount="{len(shared)}">'
        + "".join(f"<si><t>{escape(text)}</t></si>" for text in shared)
        + "</sst>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        archive.writestr("xl/sharedStrings.xml", shared_xml)


def workflow_doc(run_id: str, doc: str, state: str, *, omit: str | None = None) -> str:
    fields = {
        "run": run_id,
        "round": "1",
        "doc": doc,
        "owner": "PMO",
        "state": state,
        "updated": "2026-11-11",
    }
    if omit:
        fields.pop(omit, None)
    header = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"<!-- wf-doc\n{header}\n-->\n\n"


def project_text(run_id: str, state: str = "closed", *, omit_header_field: str | None = None) -> str:
    return workflow_doc(run_id, "PROJECT", state, omit=omit_header_field) + f"""# PROJECT — {run_id}

## 1. 目标与成功判据

- **G1**：test goal
  - 判据：test evidence

## 6. PMO 上报区

- **本轮结论**：完成。
- **残余风险/承接**：owner=MAIN；去向=runs/{run_id}/reports/final.md；最晚复核轮=R1。
"""


def decisions_text(run_id: str, *, terminal: bool = True) -> str:
    status = "达成" if terminal else "生效"
    return workflow_doc(run_id, "DECISIONS", "closed") + f"""# DECISIONS — {run_id}

## 1. 决策账本

### D-001（Round 1）测试决策

- **决策**：test decision
- **状态**：{status}
"""


def status_text(
    run_id: str,
    state: str = "qa-done",
    progress_status: str = "完成",
    *,
    omit_header_field: str | None = None,
) -> str:
    return workflow_doc(run_id, "STATUS", state, omit=omit_header_field) + f"""# STATUS · Round 1 — {run_id}

## 进度条目

<!-- wf:progress:start -->
| 时间 | 执行体 | WS | 动作 | 产出/证据 | 状态 |
| --- | --- | --- | --- | --- | --- |
| 2026-11-11 10:00 | tdo-a1 | WS-1 | test | reports/test.txt | {progress_status} |
<!-- wf:progress:end -->
"""


def issue_row(
    issue_id: str = "P-001",
    severity: str = "S3",
    status: str = "已关闭",
    decision_id: str = "D-001",
) -> list:
    return [
        issue_id,
        "1",
        "问题",
        "test issue",
        "test description",
        severity,
        status,
        "PMO",
        "reports/test.txt",
        "test action",
        "否",
        decision_id,
        "2026-11-11 10:00",
        "2026-11-11 10:00",
    ]


class CloseLintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.runs_root = Path(self.tmp.name) / "runs"
        self.runs_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def make_run(
        self,
        run_id: str,
        *,
        project_state: str = "closed",
        issue_rows=None,
        status_state: str = "qa-done",
        progress_status: str = "完成",
        terminal_decision: bool = True,
    ) -> Path:
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "PROJECT.md").write_text(
            project_text(run_id, project_state), encoding="utf-8"
        )
        (run_dir / "DECISIONS.md").write_text(
            decisions_text(run_id, terminal=terminal_decision), encoding="utf-8"
        )
        (run_dir / "STATUS-Round-1.md").write_text(
            status_text(run_id, status_state, progress_status), encoding="utf-8"
        )
        rows = [HEADERS]
        if issue_rows:
            rows.extend(issue_rows)
        write_inline_xlsx(run_dir / "ISSUES.xlsx", rows)
        return run_dir

    def codes(self, report):
        return [finding.code for finding in report.findings]

    def test_normal_closed_run_is_clean(self) -> None:
        run_dir = self.make_run(
            "normal-run",
            issue_rows=[issue_row("P-001", "S2", "已关闭", "D-001")],
        )
        report = close_lint.lint_run(run_dir)
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0, [f.code for f in report.findings])
        self.assertTrue(report.ok)

    def test_closed_run_with_new_issue_is_error(self) -> None:
        run_dir = self.make_run(
            "new-issue-run",
            issue_rows=[issue_row("P-001", "S2", "新建", "")],
        )
        report = close_lint.lint_run(run_dir)
        self.assertGreater(report.error_count, 0)
        self.assertIn("closed_has_active_issue", self.codes(report))

    def test_suspended_s1_s2_without_decision_is_error(self) -> None:
        run_dir = self.make_run(
            "suspended-no-decision",
            issue_rows=[issue_row("R-001", "S2", "挂起", "")],
        )
        report = close_lint.lint_run(run_dir)
        self.assertIn("s1_s2_decision_missing", self.codes(report))

    def test_suspended_s1_s2_with_valid_decision_is_accepted(self) -> None:
        run_dir = self.make_run(
            "suspended-valid-decision",
            issue_rows=[issue_row("R-001", "S2", "挂起", "D-001")],
        )
        report = close_lint.lint_run(run_dir)
        self.assertNotIn("s1_s2_decision_missing", self.codes(report))
        self.assertEqual(report.stats["suspended_s1_s2"], 1)

    def test_closed_run_without_terminal_decision_is_error(self) -> None:
        run_dir = self.make_run("no-terminal-decision", terminal_decision=False)
        report = close_lint.lint_run(run_dir)
        self.assertIn("terminal_decision_missing", self.codes(report))

    def test_status_qa_done_with_in_progress_is_error(self) -> None:
        run_dir = self.make_run(
            "status-conflict",
            status_state="qa-done",
            progress_status="进行中",
        )
        report = close_lint.lint_run(run_dir)
        self.assertIn("status_has_unfinished_rows", self.codes(report))
        self.assertEqual(report.stats["status_conflict_files"], 1)

    def test_missing_files_are_errors(self) -> None:
        run_dir = self.runs_root / "missing-files"
        run_dir.mkdir(parents=True)
        (run_dir / "PROJECT.md").write_text(
            project_text("missing-files", "plan-ready"), encoding="utf-8"
        )
        report = close_lint.lint_run(run_dir)
        missing = [f for f in report.findings if f.code == "required_file_missing"]
        self.assertEqual(len(missing), 3)  # DECISIONS, ISSUES, STATUS

    def test_missing_wf_doc_field_is_warning(self) -> None:
        run_dir = self.make_run("missing-doc-field")
        (run_dir / "STATUS-Round-1.md").write_text(
            status_text("missing-doc-field", omit_header_field="owner"), encoding="utf-8"
        )
        report = close_lint.lint_run(run_dir)
        self.assertIn("wf_doc_fields_missing", self.codes(report))
        self.assertEqual(report.error_count, 0)

    def test_malformed_xlsx_is_error_not_crash(self) -> None:
        run_dir = self.make_run("malformed-xlsx")
        (run_dir / "ISSUES.xlsx").write_bytes(b"not a zip file")
        report = close_lint.lint_run(run_dir)
        self.assertIn("issues_ledger_invalid", self.codes(report))

    def test_shared_strings_xlsx_is_supported(self) -> None:
        run_dir = self.make_run("shared-strings")
        write_shared_strings_xlsx(
            run_dir / "ISSUES.xlsx",
            [
                HEADERS,
                issue_row("R-001", "S2", "挂起", "D-001"),
            ],
        )
        report = close_lint.lint_run(run_dir)
        self.assertNotIn("issues_ledger_invalid", self.codes(report))
        self.assertEqual(report.stats["suspended_s1_s2"], 1)

    def test_acceptance_downgrades_only_matching_error(self) -> None:
        run_dir = self.make_run(
            "acceptance-match",
            issue_rows=[issue_row("P-001", "S2", "新建", "")],
        )
        manifest = Path(self.tmp.name) / "acceptances.json"
        manifest.write_text(
            json.dumps(
                [
                    {
                        "run_id": "acceptance-match",
                        "code": "closed_has_active_issue",
                        "issue_id": "P-001",
                        "decision_id": "D-001",
                        "owner": "MAIN",
                        "destination": "runs/acceptance-match/reports/final.md",
                        "review_round": "R2",
                        "reason": "historical residual accepted",
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = close_lint.main(
                [
                    "--run",
                    "acceptance-match",
                    "--runs-root",
                    str(self.runs_root),
                    "--acceptances",
                    str(manifest),
                    "--json",
                ]
            )
        payload = json.loads(buffer.getvalue())
        self.assertEqual(rc, 0)
        self.assertEqual(payload["summary"]["accepted_errors"], 1)
        self.assertEqual(payload["summary"]["unaccepted_errors"], 0)
        self.assertEqual(payload["summary"]["closed_violation_runs"], 0)

    def test_acceptance_does_not_accept_unmatched_issue(self) -> None:
        self.make_run(
            "acceptance-mismatch",
            issue_rows=[issue_row("P-001", "S2", "新建", "")],
        )
        manifest = Path(self.tmp.name) / "acceptances.json"
        manifest.write_text(
            json.dumps(
                [
                    {
                        "run_id": "acceptance-mismatch",
                        "code": "closed_has_active_issue",
                        "issue_id": "P-999",
                        "decision_id": "D-001",
                        "owner": "MAIN",
                        "destination": "runs/acceptance-mismatch/reports/final.md",
                        "review_round": "R2",
                        "reason": "should not match",
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = close_lint.main(
                [
                    "--run",
                    "acceptance-mismatch",
                    "--runs-root",
                    str(self.runs_root),
                    "--acceptances",
                    str(manifest),
                    "--json",
                ]
            )
        payload = json.loads(buffer.getvalue())
        self.assertEqual(rc, 1)
        self.assertEqual(payload["summary"]["accepted_errors"], 0)
        self.assertEqual(payload["summary"]["unaccepted_errors"], 1)

    def test_invalid_acceptance_manifest_is_error(self) -> None:
        self.make_run("invalid-acceptance")
        manifest = Path(self.tmp.name) / "acceptances.json"
        manifest.write_text(
            json.dumps([{"run_id": "invalid-acceptance"}]),
            encoding="utf-8",
        )
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = close_lint.main(
                [
                    "--run",
                    "invalid-acceptance",
                    "--runs-root",
                    str(self.runs_root),
                    "--acceptances",
                    str(manifest),
                    "--json",
                ]
            )
        payload = json.loads(buffer.getvalue())
        self.assertEqual(rc, 1)
        self.assertIn("errors", payload)

    def test_json_cli_contains_summary(self) -> None:
        self.make_run("json-run")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = close_lint.main(
                ["--all", "--runs-root", str(self.runs_root), "--json"]
            )
        payload = json.loads(buffer.getvalue())
        self.assertEqual(rc, 0)
        self.assertEqual(payload["summary"]["runs_scanned"], 1)
        self.assertEqual(payload["summary"]["closed_runs"], 1)
        self.assertIn("closed_violation_runs", payload["summary"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
