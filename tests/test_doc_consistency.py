# -*- coding: utf-8 -*-
"""doc_consistency.py 的标准库回归测试（unittest，无 pytest/openpyxl 依赖）。

可直接运行：``python3 workflow-group/tests/test_doc_consistency.py``
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import doc_consistency as dc  # noqa: E402


class TempRootCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _touch(self, rel: str, text: str = "") -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class CoverageTests(TempRootCase):
    def test_baseline_registry_covers_dirs_and_count(self) -> None:
        baseline = self.root / "templates" / "baseline"
        ids = [f"b{i}" for i in range(dc.EXPECTED_BASELINE_COUNT)]
        for name in ids:
            self._touch(f"templates/baseline/{name}/BASELINE.md", "# baseline\n")
        self._touch(
            "templates/baseline/REGISTRY.json",
            json.dumps({"baselines": [{"id": name} for name in ids]}),
        )
        self.assertEqual([], dc.check_baseline_registry(self.root))

        self._touch("templates/baseline/extra/BASELINE.md", "# extra\n")
        findings = dc.check_baseline_registry(self.root)
        self.assertTrue(any(f.level == dc.ERROR for f in findings))
        self.assertTrue(any("extra" in f.message for f in findings))

    def test_specialized_map_matches_every_spec_dir(self) -> None:
        self._touch("templates/specialized/a/SPEC.md", "baseline: none — x\n")
        self._touch("templates/specialized/b/SPEC.md", "baseline: none — y\n")
        self._touch(
            "templates/specialized/BASELINE-MAP.md",
            "| 领域特化 | baseline | contracts | 映射理由 |\n"
            "| --- | --- | --- | --- |\n"
            "| `a` | `none` | audit | a |\n",
        )
        findings = dc.check_specialized_coverage(self.root)
        self.assertTrue(any("b" in f.message for f in findings))

        self._touch(
            "templates/specialized/BASELINE-MAP.md",
            "| 领域特化 | baseline | contracts | 映射理由 |\n"
            "| --- | --- | --- | --- |\n"
            "| `a` | `none` | audit | a |\n"
            "| `b` | `none` | audit | b |\n",
        )
        self.assertEqual([], dc.check_specialized_coverage(self.root))


class CountTests(TempRootCase):
    def _prepare(self, canonical: int) -> None:
        for i in range(canonical):
            (self.root / "runs" / f"r{i}").mkdir(parents=True)
        (self.root / "templates" / "specialized" / "s0").mkdir(parents=True)
        (self.root / "templates" / "baseline" / "b0").mkdir(parents=True)
        self._touch(
            "WORKFLOW-TAGS.md",
            "> 时效声明：本文件是 2026-10-23 快照，不是当前索引。\n"
            f"> 当前 canonical={canonical}、baseline=1、specialized=1。\n",
        )

    def test_declared_counts_match_actual_dirs(self) -> None:
        self._prepare(canonical=2)
        self.assertEqual([], dc.check_workflow_tags_counts(self.root))

    def test_stale_canonical_count_is_error(self) -> None:
        self._prepare(canonical=2)
        self._touch(
            "WORKFLOW-TAGS.md",
            "> 时效声明：本文件是快照，不是当前索引。\n"
            "> 当前 canonical=31、baseline=1、specialized=1。\n",
        )
        findings = dc.check_workflow_tags_counts(self.root)
        self.assertTrue(any(f.level == dc.ERROR and "canonical=31" in f.message for f in findings))


class ReferenceTests(unittest.TestCase):
    def test_invalid_workflow_refs_are_errors(self) -> None:
        text = (
            "## 1. 总原则\n"
            "## 9. opencode\n"
            "## 10. 反模式\n"
            "\n"
            "见 §1.3、§9.7、§10.8、§10.11。\n"
        )
        findings = dc.check_workflow_references(text)
        messages = "\n".join(f.message for f in findings)
        for ref in ("§1.3", "§9.7", "§10.8", "§10.11"):
            self.assertIn(ref, messages)
        self.assertEqual(4, len(findings))

    def test_heading_and_explicit_numbered_items_are_valid(self) -> None:
        text = (
            "## 1. 总原则\n"
            "### 1.3 盲读\n"
            "## 9. opencode\n"
            "### 9.7 历史说明\n"
            "## 10. 反模式\n"
            "10.8 唯一 WS 绑定\n"
            "10.11 --also 限制\n"
            "\n"
            "见 §1.3、§9.7、§10.8、§10.11。\n"
        )
        self.assertEqual([], dc.check_workflow_references(text))


class RoleByTests(TempRootCase):
    def test_state_command_without_by_is_warn(self) -> None:
        self._touch(
            "roles/MAIN.md",
            "```bash\n"
            "python3 scripts/wf.py state <run> PROJECT closed\n"
            "python3 scripts/wf.py state <run2> STATUS closed --by MAIN\n"
            "```\n",
        )
        findings = dc.check_role_state_by(self.root / "roles")
        self.assertEqual(1, len(findings))
        self.assertEqual(dc.WARN, findings[0].level)
        self.assertIn("MAIN.md:2", findings[0].message)

    def test_state_command_with_by_is_clean(self) -> None:
        self._touch(
            "roles/PMO.md",
            "python3 scripts/wf.py state <run> PROJECT plan-ready --by PMO\n",
        )
        self.assertEqual([], dc.check_role_state_by(self.root / "roles"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
