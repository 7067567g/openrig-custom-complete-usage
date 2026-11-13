import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

GUIDE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GUIDE_DIR.parents[1]
SPEC = importlib.util.spec_from_file_location("lead_guide", GUIDE_DIR / "guide.py")
lead_guide = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lead_guide)


class VersionTests(unittest.TestCase):
    def test_current_guide_is_pinned(self):
        self.assertEqual(lead_guide.check_version(), [])

    def test_version_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "VERSION").write_text("9.9.9\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "OPENRIG-WORKFLOW-GUIDE.zh-CN.md").write_text("changed\n", encoding="utf-8")
            guide = root / "guide"
            guide.mkdir()
            (guide / "content-index.json").write_text("{}", encoding="utf-8")
            (guide / "version.json").write_text(json.dumps({
                "openrigGuideVersion": "0.1.12",
                "mainDocSha256": "deadbeef",
                "contentIndexSha256": "deadbeef",
            }), encoding="utf-8")
            errors = lead_guide.check_version(root=root, guide_dir=guide)
            self.assertTrue(any("OpenRig 版本漂移" in e for e in errors))
            self.assertTrue(any("主文档哈希漂移" in e for e in errors))

    def test_missing_version_is_drift_not_exception(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs").mkdir()
            (root / "docs" / "OPENRIG-WORKFLOW-GUIDE.zh-CN.md").write_text("doc\n", encoding="utf-8")
            guide = root / "guide"
            guide.mkdir()
            (guide / "content-index.json").write_text("{}", encoding="utf-8")
            (guide / "version.json").write_text(json.dumps({
                "openrigGuideVersion": "0.1.12",
                "mainDocSha256": "deadbeef",
                "contentIndexSha256": "deadbeef",
            }), encoding="utf-8")
            errors = lead_guide.check_version(root=root, guide_dir=guide)
            self.assertTrue(any("缺少 OpenRig VERSION" in e for e in errors))

    def test_content_index_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            guide = Path(td)
            (guide / "content-index.json").write_text("{}", encoding="utf-8")
            pinned = json.loads((GUIDE_DIR / "version.json").read_text(encoding="utf-8"))
            pinned["contentIndexSha256"] = "deadbeef"
            (guide / "version.json").write_text(json.dumps(pinned), encoding="utf-8")
            errors = lead_guide.check_version(root=REPO_ROOT, guide_dir=guide)
            self.assertTrue(any("内容索引哈希漂移" in e for e in errors))

    def test_review_blocks_before_answers_on_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "VERSION").write_text("9.9.9\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "OPENRIG-WORKFLOW-GUIDE.zh-CN.md").write_text(
                "changed\n", encoding="utf-8"
            )
            guide = root / "guide"
            guide.mkdir()
            (guide / "content-index.json").write_text("{}", encoding="utf-8")
            (guide / "version.json").write_text(
                json.dumps(
                    {
                        "openrigGuideVersion": "0.1.12",
                        "mainDocSha256": "deadbeef",
                        "contentIndexSha256": "deadbeef",
                    }
                ),
                encoding="utf-8",
            )
            work = root / "run"
            args = SimpleNamespace(
                workdir=str(work),
                answers=str(GUIDE_DIR / "answers.example.md"),
                timeout=1,
                interactive=False,
            )
            old_root, old_guide = lead_guide.REPO_ROOT, lead_guide.GUIDE_DIR
            lead_guide.REPO_ROOT, lead_guide.GUIDE_DIR = root, guide
            try:
                with redirect_stdout(io.StringIO()):
                    rc = lead_guide.review(args)
            finally:
                lead_guide.REPO_ROOT, lead_guide.GUIDE_DIR = old_root, old_guide
            self.assertEqual(rc, 3)
            self.assertFalse((work / "RESULT.txt").exists())


class ReviewParsingTests(unittest.TestCase):
    def test_pass(self):
        text = textwrap.dedent("""
            Looks good.
            VERDICT: PASS
            MISSING: none
            QUESTIONS: none
            EXPLANATION: ok
            FINAL: 引导完成
        """)
        parsed = lead_guide.parse_review(text)
        self.assertEqual(parsed["verdict"], "PASS")
        self.assertEqual(parsed["final"], "引导完成")

    def test_small_deviation(self):
        parsed = lead_guide.parse_review("VERDICT: SMALL_DEVIATION\nQUESTIONS: 为什么要独立QA？; round和step区别？\nFINAL: 引导完成")
        self.assertEqual(parsed["verdict"], "SMALL_DEVIATION")
        self.assertIn("独立QA", parsed["questions"])

    def test_large_deviation(self):
        parsed = lead_guide.parse_review("VERDICT: LARGE_DEVIATION\nFINAL: 请重新运行引导")
        self.assertEqual(parsed["final"], "请重新运行引导")

    def test_incomplete(self):
        parsed = lead_guide.parse_review("VERDICT: INCOMPLETE\nMISSING: 没有回答治理层\nEXPLANATION: 缺少关键维度\nFINAL: 请重新运行引导")
        self.assertEqual(parsed["verdict"], "INCOMPLETE")
        self.assertEqual(parsed["missing"], "没有回答治理层")


class ResultTests(unittest.TestCase):
    def test_write_result_exact(self):
        with tempfile.TemporaryDirectory() as td:
            p = lead_guide.write_result(Path(td), "引导完成")
            self.assertEqual(p.read_text(encoding="utf-8"), "引导完成")


class EndToEndMockTests(unittest.TestCase):
    def _run_with_mock(self, reviewer_output: str, mock_exit: int = 0):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        tmp = Path(td.name)
        mock = tmp / "mock-reviewer.sh"
        mock.write_text(
            "#!/usr/bin/env bash\ncat <<'EOF'\n" + reviewer_output + "\nEOF\nexit " + str(mock_exit) + "\n",
            encoding="utf-8",
        )
        mock.chmod(0o755)
        work = tmp / "run"
        env = dict(os.environ)
        env["LEAD_GUIDE_REVIEWER_CMD"] = str(mock)
        proc = subprocess.run(
            [
                sys.executable,
                str(GUIDE_DIR / "guide.py"),
                "review",
                "--workdir",
                str(work),
                "--answers",
                str(GUIDE_DIR / "answers.example.md"),
            ],
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        return proc, work

    def test_pass_writes_exact_final(self):
        proc, work = self._run_with_mock(
            "VERDICT: PASS\nMISSING: none\nQUESTIONS: none\nEXPLANATION: ok\nFINAL: 引导完成"
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((work / "RESULT.txt").read_text(encoding="utf-8"), "引导完成")
        archived = list((work / "history").glob("*/RESULT.txt"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].read_text(encoding="utf-8"), "引导完成")

    def test_large_deviation_writes_rerun(self):
        proc, work = self._run_with_mock(
            "VERDICT: LARGE_DEVIATION\nMISSING: core model wrong\nQUESTIONS: none\n"
            "EXPLANATION: wrong\nFINAL: 请重新运行引导"
        )
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(
            (work / "RESULT.txt").read_text(encoding="utf-8"), "请重新运行引导"
        )

    def test_incomplete_explains(self):
        proc, work = self._run_with_mock(
            "VERDICT: INCOMPLETE\nMISSING: 治理层未答\nQUESTIONS: none\n"
            "EXPLANATION: 缺少关键维度\nFINAL: 请重新运行引导"
        )
        self.assertEqual(proc.returncode, 4)
        result = (work / "RESULT.txt").read_text(encoding="utf-8")
        self.assertTrue(result.startswith("未完成："))
        self.assertIn("缺少关键维度", result)
        self.assertNotEqual(result.strip(), "引导完成")

    def test_small_deviation_writes_followup(self):
        proc, work = self._run_with_mock(
            "VERDICT: SMALL_DEVIATION\nMISSING: none\n"
            "QUESTIONS: round 和 step 有什么区别？\n"
            "EXPLANATION: 需要确认\nFINAL: 请重新运行引导"
        )
        self.assertEqual(proc.returncode, 5)
        result = (work / "RESULT.txt").read_text(encoding="utf-8")
        self.assertNotEqual(result.strip(), "引导完成")
        followup = (work / "FOLLOWUP-QUESTIONS.md").read_text(encoding="utf-8")
        self.assertIn("round 和 step", followup)

    def test_small_deviation_cannot_pass_directly(self):
        proc, work = self._run_with_mock(
            "VERDICT: SMALL_DEVIATION\nMISSING: none\n"
            "QUESTIONS: round 和 step 有什么区别？\n"
            "EXPLANATION: 需要确认\nFINAL: 引导完成"
        )
        self.assertEqual(proc.returncode, 5)
        self.assertNotEqual(
            (work / "RESULT.txt").read_text(encoding="utf-8").strip(), "引导完成"
        )
        self.assertTrue((work / "FOLLOWUP-QUESTIONS.md").is_file())

    def test_missing_required_fields_fails_closed(self):
        proc, work = self._run_with_mock("VERDICT: PASS\nFINAL: 引导完成")
        self.assertEqual(proc.returncode, 4)
        result = (work / "RESULT.txt").read_text(encoding="utf-8")
        self.assertTrue(result.startswith("未完成："))
        self.assertIn("MISSING", result)

    def test_nonzero_reviewer_fails_closed(self):
        proc, work = self._run_with_mock(
            "VERDICT: PASS\nMISSING: none\nQUESTIONS: none\n"
            "EXPLANATION: ok\nFINAL: 引导完成",
            mock_exit=3,
        )
        self.assertEqual(proc.returncode, 4)
        result = (work / "RESULT.txt").read_text(encoding="utf-8")
        self.assertTrue(result.startswith("未完成："))
        self.assertIn("审查命令失败", result)


if __name__ == "__main__":
    unittest.main()
