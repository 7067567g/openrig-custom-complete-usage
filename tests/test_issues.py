# -*- coding: utf-8 -*-
"""WS-2 · issues.py 单测

覆盖 PROJECT §1-G2：ID 分配、枚举校验、S1 规则、close 需决策。
全部离线：在 tmp_path 内建临时 xlsx（openpyxl），不联网、不碰 runs/。

替补实现开关（用于证明用例非空转 / 先红后绿）：
  WF_ISSUES_PATH=/tmp/mutant_issues.py python3 -m pytest workflow-group/tests/test_issues.py -q
默认加载 workflow-group/scripts/issues.py。
"""

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # workflow-group/
ISSUES_PY = Path(os.environ.get("WF_ISSUES_PATH") or (ROOT / "scripts" / "issues.py"))


def _load():
    spec = importlib.util.spec_from_file_location("wf_issues_under_test", ISSUES_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


issues = _load()
SRC = "runs/wf-engine-tests-20261014/STATUS-Round-1.md#进度条目"


def ns(**kw):
    return argparse.Namespace(**kw)


def wb_of(path):
    from openpyxl import load_workbook

    return load_workbook(path)


def cell(path, row, header):
    return wb_of(path)[issues.SHEET].cell(row=row, column=issues.COL[header]).value


@pytest.fixture()
def xlsx(tmp_path):
    p = tmp_path / "ISSUES.xlsx"
    issues.cmd_init(ns(xlsx=str(p), force=False))
    return p


def add(p, **kw):
    a = dict(
        xlsx=str(p),
        round=1,
        type="风险",
        title="t",
        desc="",
        severity="S3",
        status="新建",
        owner="PMO",
        source=SRC,
        action="do x",
        need_decision="no",
        id=None,
        force=False,
    )
    a.update(kw)
    issues.cmd_add(ns(**a))


# --------------------------------------------------------------- init / 模板
def test_init_creates_three_sheets_and_headers(xlsx):
    wb = wb_of(xlsx)
    assert set([issues.SHEET, issues.SHEET_SUM, issues.SHEET_HELP]) <= set(
        wb.sheetnames
    )
    ws = wb[issues.SHEET]
    assert [
        ws.cell(row=1, column=i).value for i in range(1, issues.NC + 1)
    ] == issues.HEADERS


def test_init_refuses_overwrite_without_force(xlsx, capsys):
    with pytest.raises(SystemExit) as e:
        issues.cmd_init(ns(xlsx=str(xlsx), force=False))
    assert e.value.code == 1
    assert "已存在" in capsys.readouterr().err


def test_load_rejects_missing_sheet(tmp_path, capsys):
    from openpyxl import Workbook

    p = tmp_path / "bad.xlsx"
    wb = Workbook()
    wb.active.title = "别的表"
    wb.save(p)
    with pytest.raises(SystemExit):
        issues.load(p)
    assert "缺少 sheet" in capsys.readouterr().err


# --------------------------------------------------------------- ID 分配
def test_id_sequential_per_prefix(xlsx):
    add(xlsx, type="问题", title="p1")
    add(xlsx, type="问题", title="p2")
    add(xlsx, type="风险", title="r1")
    add(xlsx, type="变更", title="c1")
    assert cell(xlsx, 2, "ID") == "P-001"
    assert cell(xlsx, 3, "ID") == "P-002"
    assert cell(xlsx, 4, "ID") == "R-001"
    assert cell(xlsx, 5, "ID") == "C-001"


def test_next_id_ignores_malformed_and_takes_max(xlsx):
    ws = wb_of(xlsx)[issues.SHEET]
    ws.cell(row=2, column=issues.COL["ID"], value="P-abc")  # 畸形，忽略
    ws.cell(row=3, column=issues.COL["ID"], value="P-005")
    ws.cell(row=4, column=issues.COL["ID"], value="R-009")
    ws.parent.save(xlsx)
    ws2 = wb_of(xlsx)[issues.SHEET]
    assert issues.next_id(ws2, "P") == "P-006"
    assert issues.next_id(ws2, "R") == "R-010"


def test_add_explicit_id_is_respected(xlsx):
    add(xlsx, id="P-100", type="问题")
    assert cell(xlsx, 2, "ID") == "P-100"


# --------------------------------------------------------------- 枚举校验
@pytest.mark.parametrize(
    "field,allowed,bad",
    [
        ("type", "TYPES", "告警"),
        ("severity", "SEV", "S9"),
        ("status", "STATUSES", "完工"),
        ("owner", "OWNERS", "用户"),
    ],
)
def test_add_rejects_invalid_enum(xlsx, capsys, field, allowed, bad):
    kw = {field: bad}
    with pytest.raises(SystemExit) as e:
        add(xlsx, **kw)
    assert e.value.code == 1
    assert "非法" in capsys.readouterr().err


def test_ensure_enum_blank_is_ok():
    assert issues.ensure_enum("", issues.SEV, "--severity") == ""
    assert issues.ensure_enum(None, issues.SEV, "--severity") == ""


def test_update_rejects_invalid_enum(xlsx, capsys):
    add(xlsx)
    with pytest.raises(SystemExit):
        issues.cmd_update(
            ns(
                xlsx=str(xlsx),
                id="R-001",
                status="完工",
                owner=None,
                severity=None,
                action=None,
                decision=None,
                desc=None,
                title=None,
            )
        )
    assert "非法" in capsys.readouterr().err


def test_update_without_any_field_dies(xlsx, capsys):
    add(xlsx)
    with pytest.raises(SystemExit):
        issues.cmd_update(
            ns(
                xlsx=str(xlsx),
                id="R-001",
                status=None,
                owner=None,
                severity=None,
                action=None,
                decision=None,
                desc=None,
                title=None,
            )
        )
    assert "没有指定要修改的字段" in capsys.readouterr().err


# --------------------------------------------------------------- S1 硬规则
def test_s1_requires_need_decision_yes(xlsx, capsys):
    with pytest.raises(SystemExit) as e:
        add(xlsx, severity="S1", need_decision="no")
    assert e.value.code == 1
    assert "S1 行必须" in capsys.readouterr().err


def test_s1_with_need_decision_yes_ok(xlsx):
    add(xlsx, severity="S1", need_decision="yes")
    assert cell(xlsx, 2, "严重度") == "S1"
    assert cell(xlsx, 2, "需主会话决策") == "是"


def test_s1_with_force_bypasses_rule(xlsx):
    add(xlsx, severity="S1", need_decision="no", force=True)
    assert cell(xlsx, 2, "需主会话决策") == "否"


def test_need_decision_accepts_cn_and_en(xlsx):
    add(xlsx, type="问题", need_decision="是")
    add(xlsx, type="问题", need_decision="yes")
    assert cell(xlsx, 2, "需主会话决策") == "是"
    assert cell(xlsx, 3, "需主会话决策") == "是"


def test_add_requires_source_and_action(xlsx, capsys):
    with pytest.raises(SystemExit):
        add(xlsx, source="   ")
    assert "--source 不能为空" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        add(xlsx, action="")
    assert "--action 不能为空" in capsys.readouterr().err


# --------------------------------------------------------------- close 需决策
def test_close_requires_decision_argparse(xlsx, monkeypatch):
    add(xlsx, type="问题")
    monkeypatch.setattr(sys, "argv", ["issues.py", "close", str(xlsx), "P-001"])
    with pytest.raises(SystemExit) as e:
        issues.main()
    assert e.value.code == 2  # argparse 缺必填 --decision


def test_close_dies_when_decision_empty(xlsx, capsys):
    add(xlsx, type="问题")
    with pytest.raises(SystemExit) as e:
        issues.cmd_close(ns(xlsx=str(xlsx), id="P-001", decision=None))
    assert e.value.code == 1
    assert "必须给 --decision" in capsys.readouterr().err


def test_close_sets_status_and_decision(xlsx):
    add(xlsx, type="问题")
    issues.cmd_close(ns(xlsx=str(xlsx), id="P-001", decision="D-004"))
    assert cell(xlsx, 2, "状态") == "已关闭"
    assert cell(xlsx, 2, "关联决策ID") == "D-004"


def test_close_unknown_id_dies(xlsx, capsys):
    with pytest.raises(SystemExit):
        issues.cmd_close(ns(xlsx=str(xlsx), id="P-999", decision="D-001"))
    assert "找不到 ID" in capsys.readouterr().err


# --------------------------------------------------------------- list / find
def test_find_row_case_insensitive(xlsx):
    add(xlsx, type="问题")
    ws = wb_of(xlsx)[issues.SHEET]
    assert issues.find_row(ws, "p-001") == 2
    assert issues.find_row(ws, "P-404") is None


def json_tail(capsys):
    """只取本段 stdout 的 JSON（跳过同一 buffer 里 add/close 的 [OK] 行）。"""
    return json.loads(capsys.readouterr().out.strip())


def test_list_open_only_excludes_closed(xlsx, capsys):
    add(xlsx, type="问题", title="仍开着")
    add(xlsx, type="问题", title="将关闭")
    issues.cmd_close(ns(xlsx=str(xlsx), id="P-002", decision="D-001"))
    capsys.readouterr()  # 丢弃前面的 [OK] 输出
    issues.cmd_list(
        ns(
            xlsx=str(xlsx),
            open_only=True,
            round=None,
            severity=None,
            need_decision=None,
            json=True,
        )
    )
    rows = json_tail(capsys)
    assert [r["ID"] for r in rows] == ["P-001"]
    assert rows[0]["标题"] == "仍开着"


def test_list_filters_round_severity_need_decision(xlsx, capsys):
    add(xlsx, type="问题", round=1, severity="S2", need_decision="yes", title="R1S2")
    add(xlsx, type="问题", round=2, severity="S3", need_decision="no", title="R2S3")
    capsys.readouterr()
    issues.cmd_list(
        ns(
            xlsx=str(xlsx),
            open_only=False,
            round=2,
            severity=None,
            need_decision=None,
            json=True,
        )
    )
    assert [r["标题"] for r in json_tail(capsys)] == ["R2S3"]
    issues.cmd_list(
        ns(
            xlsx=str(xlsx),
            open_only=False,
            round=None,
            severity="S2",
            need_decision=None,
            json=True,
        )
    )
    assert [r["标题"] for r in json_tail(capsys)] == ["R1S2"]
    issues.cmd_list(
        ns(
            xlsx=str(xlsx),
            open_only=False,
            round=None,
            severity=None,
            need_decision="是",
            json=True,
        )
    )
    assert [r["标题"] for r in json_tail(capsys)] == ["R1S2"]


# --------------------------------------------------------------- JSONL 镜像/降级
def test_xlsx_writes_jsonl_mirror_on_init_and_add(xlsx):
    mirror = issues.jsonl_path(xlsx)
    assert mirror.is_file()
    assert issues.read_jsonl_rows(xlsx) == []
    add(xlsx, type="问题", title="mirror")
    rows = issues.read_jsonl_rows(xlsx)
    assert len(rows) == 1
    assert rows[0]["ID"] == "P-001"
    assert rows[0]["标题"] == "mirror"


def test_jsonl_fallback_supports_init_add_list_update_close(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(issues, "HAS_OPENPYXL", False)
    p = tmp_path / "ISSUES.xlsx"
    issues.cmd_init(ns(xlsx=str(p), force=False))
    assert issues.jsonl_path(p).is_file()
    assert not p.exists()
    add(p, type="问题", title="fallback")
    assert issues.read_rows(p)[0]["ID"] == "P-001"
    issues.cmd_update(
        ns(
            xlsx=str(p), id="P-001", status="处理中", owner=None, severity=None,
            action=None, decision=None, desc=None, title=None,
        )
    )
    assert issues.read_rows(p)[0]["状态"] == "处理中"
    issues.cmd_close(ns(xlsx=str(p), id="P-001", decision="D-001"))
    row = issues.read_rows(p)[0]
    assert row["状态"] == "已关闭" and row["关联决策ID"] == "D-001"
    capsys.readouterr()
    issues.cmd_list(
        ns(
            xlsx=str(p), open_only=False, round=None, severity=None,
            need_decision=None, json=True,
        )
    )
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["ID"] == "P-001"


def test_wf_doctor_reads_jsonl_when_openpyxl_unavailable(new_run, monkeypatch):
    """AFC-011：doctor 在 openpyxl 不可用时仍能读取 JSONL 镜像。"""
    import argparse as _argparse
    import sys as _sys
    from pathlib import Path as _Path

    scripts = _Path(__file__).resolve().parent.parent / "scripts"
    if str(scripts) not in _sys.path:
        _sys.path.insert(0, str(scripts))
    import wf  # noqa: E402

    rd = new_run(run_id="t-issues-fallback-doctor")
    issues.cmd_add(
        _argparse.Namespace(
            xlsx=str(rd / "ISSUES.xlsx"), round=1, type="风险", title="mirror only",
            desc="", severity="S3", status="新建", owner="PMO",
            source="STATUS-Round-1.md#进度", action="修复", need_decision="no",
            id=None, force=False,
        )
    )
    monkeypatch.setattr(issues, "HAS_OPENPYXL", False)
    rc = wf.doctor("t-issues-fallback-doctor")
    assert rc == 0
