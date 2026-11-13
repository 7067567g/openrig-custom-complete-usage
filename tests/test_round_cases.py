import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = ["case-12-rounds-hardening", "case-12-rounds-release", "case-12-rounds-docs"]

@pytest.mark.parametrize("case", CASES)
def test_round_case_is_complete(case):
    base = ROOT / "examples" / "round-cases" / case / "run"
    data = json.loads((base / "ROUNDS.json").read_text(encoding="utf-8"))
    assert len(data["rounds"]) == 12
    statuses = sorted(base.glob("STATUS-Round-*.md"))
    assert len(statuses) == 12
    assert len(list((base / "evidence").glob("round-*.log"))) == 12
    project = (base / "PROJECT.md").read_text(encoding="utf-8")
    assert "state: closed" in project
    decisions = (base / "DECISIONS.md").read_text(encoding="utf-8")
    assert "状态：达成" in decisions
