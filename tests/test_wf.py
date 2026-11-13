# -*- coding: utf-8 -*-
"""WS-1：`scripts/wf.py` 单元测试（tdo-a1 独占）。

覆盖 SPEC §1 / PROJECT §4 的 6 类分支：
  1. 状态机守卫 `_delegate_guards` 四种不匹配
  2. 锁 TTL / `--steal` / 安全释放
  3. `append-status --also` 的 gitignore 过滤（复现 F9：被忽略文件跳过+告警、整条提交成功）
  4. `commit` 子命令路径
  5. `ledger` 汇总
  6. `doctor` 报错分支

夹具见 conftest.py；所有用例在临时 git 仓库与临时 runs/ 下运行。
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import wf  # noqa: E402


# ------------------------------------------------------------------ helpers
def _append_args(**over):
    base = dict(
        run_id="t-run",
        agent="tdo-a1",
        ws="WS-1",
        action="动作",
        evidence="证据",
        state="完成",
        blocker="",
        also=[],
        commit=True,
        wait=0,
        steal=False,
    )
    base.update(over)
    return argparse.Namespace(**base)


def _status(rd):
    return rd / "STATUS-Round-1.md"


# ================================================================ 1. 守卫
def test_guard_pmo_rejects_bad_project_state(new_run):
    """反例①：PROJECT.state=closed 时不得委派 PMO。"""
    rd = new_run()
    wf.write_header_field(rd / "PROJECT.md", "state", "closed")
    with pytest.raises(SystemExit):
        wf._delegate_guards(rd, "pmo")


def test_guard_tdo_requires_project_plan_ready(new_run):
    """反例②：PROJECT.state≠plan-ready 时不得委派 TDO。"""
    rd = new_run()
    wf.write_header_field(rd / "PROJECT.md", "state", "pmo-plan")
    with pytest.raises(SystemExit):
        wf._delegate_guards(rd, "tdo")


def test_guard_tdo_rejects_wrong_status_state(new_run):
    """反例③：STATUS.state=qa-pending 时不得再委派 TDO。"""
    rd = new_run()
    wf.write_header_field(rd / "PROJECT.md", "state", "plan-ready")
    wf.write_header_field(_status(rd), "state", "qa-pending")
    with pytest.raises(SystemExit):
        wf._delegate_guards(rd, "tdo")


def test_guard_qa_requires_status_qa_pending(new_run):
    """反例④：STATUS.state≠qa-pending 时不得委派 QA。"""
    rd = new_run()
    wf.write_header_field(_status(rd), "state", "tdo-in-progress")
    with pytest.raises(SystemExit):
        wf._delegate_guards(rd, "qa")


def test_guard_happy_path_and_force(new_run):
    """正例：pmo-plan→pmo 通过；force 绕过一切守卫。"""
    rd = new_run()
    wf.write_header_field(rd / "PROJECT.md", "state", "pmo-plan")
    ph, sh = wf._delegate_guards(rd, "pmo")  # 不抛
    assert ph.get("state") == "pmo-plan"
    wf.write_header_field(rd / "PROJECT.md", "state", "closed")
    wf._delegate_guards(rd, "tdo", force=True)  # force 不抛


# ================================================================ 2. 锁
def test_lock_acquire_read_release(new_run):
    """加锁→元信息可读→持有者安全释放。"""
    rd = new_run()
    assert wf.acquire_lock(rd, "tdo-a1", wait=0) is True
    meta = wf.read_lock(rd)
    assert meta["agent"] == "tdo-a1" and meta["stale"] is False
    assert wf.release_lock(rd, agent="tdo-a1") is True
    assert not wf.lock_path(rd).exists()
    assert wf.read_lock(rd) is None


def test_lock_second_acquire_times_out(new_run):
    """已持锁时第二次获取（wait=0）必须失败，不能硬写。"""
    rd = new_run()
    assert wf.acquire_lock(rd, "tdo-a1", wait=0) is True
    assert wf.acquire_lock(rd, "tdo-a2", wait=0) is False
    assert wf.read_lock(rd)["agent"] == "tdo-a1"


def test_lock_ttl_stale_and_steal(new_run):
    """TTL 过期→stale=True；`--steal` 接管成功且写 steal 说明行。"""
    rd = new_run()
    assert wf.acquire_lock(rd, "tdo-a1", wait=0) is True
    old = time.time() - wf.LOCK_TTL - 100
    import os

    os.utime(wf.lock_path(rd), (old, old))
    meta = wf.read_lock(rd)
    assert meta["stale"] is True and meta["age"] > wf.LOCK_TTL
    # 非 steal 拿不到
    assert wf.acquire_lock(rd, "tdo-a2", wait=0) is False
    # steal 接管
    assert wf.acquire_lock(rd, "tdo-a2", wait=0, steal=True) is True
    assert wf.read_lock(rd)["agent"] == "tdo-a2"
    assert "接管过期锁" in _status(rd).read_text(encoding="utf-8")


def test_lock_release_wrong_agent_dies_then_force(new_run):
    """安全释放：非持有者释放报错；--force 才能强解。"""
    rd = new_run()
    assert wf.acquire_lock(rd, "tdo-a1", wait=0) is True
    with pytest.raises(SystemExit):
        wf.release_lock(rd, agent="tdo-a2")
    assert wf.lock_path(rd).exists()  # 未被误删
    assert wf.release_lock(rd, agent="tdo-a2", force=True) is True
    assert not wf.lock_path(rd).exists()


# ============================================ 3. append-status --also 过滤
def test_append_status_skips_gitignored_also(new_run, capsys):
    """F9 复现：`--also` 指向被 gitignore 的 *.log 时，跳过并告警，整条提交成功。"""
    rd = new_run()
    ignored = rd / "noise.log"  # 命中 .gitignore 的 *.log
    ignored.write_text("运行时噪声\n", encoding="utf-8")
    tracked = rd / "notes.md"
    tracked.write_text("该入库\n", encoding="utf-8")

    wf.cmd_append_status(_append_args(also=[str(ignored), str(tracked)]))

    # 整条提交成功：HEAD 含本次 STATUS 变更与 notes.md
    repo = wf.REPO
    shown = subprocess.run(
        ["git", "-C", str(repo), "show", "--name-only", "--pretty=format:", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout
    assert "STATUS-Round-1.md" in shown
    assert "notes.md" in shown
    assert "noise.log" not in shown
    # 日志文件未被跟踪
    r = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "ls-files",
            "--error-unmatch",
            "workflow-group/runs/t-run/noise.log",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    # 进度行落盘（动作文本出现在 STATUS 中）
    assert "动作" in _status(rd).read_text(encoding="utf-8")


def test_append_status_warns_on_ignored(new_run, capsys):
    """F9 告警：被忽略路径必须出现在告警输出中（可观测）。"""
    rd = new_run()
    ignored = rd / "debug.log"
    ignored.write_text("x\n", encoding="utf-8")
    wf.cmd_append_status(_append_args(also=[str(ignored)]))
    captured = capsys.readouterr()
    blob = captured.out + captured.err
    assert "debug.log" in blob
    assert "忽略" in blob or "gitignore" in blob or "skip" in blob.lower()


def test_append_status_normalizes_duplicate_workflow_group_prefix(new_run):
    """F9 follow-up：在 workflow-group/ 下传入 workflow-group/... 不再翻倍。"""
    rd = new_run()
    md = rd / "evidence.md"
    md.write_text("证据\n", encoding="utf-8")
    old_cwd = Path.cwd()
    os.chdir(wf.ROOT)
    try:
        wf.cmd_append_status(
            _append_args(also=["workflow-group/runs/t-run/evidence.md"])
        )
    finally:
        os.chdir(old_cwd)
    shown = subprocess.run(
        ["git", "-C", str(wf.REPO), "show", "--name-only", "--pretty=format:", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout
    assert "evidence.md" in shown
    assert "workflow-group/workflow-group" not in shown


def test_append_status_commits_tracked_also(new_run):
    """正例：`--also` 指向被跟踪文件时正常提交。"""
    rd = new_run()
    md = rd / "evidence.md"
    md.write_text("证据\n", encoding="utf-8")
    wf.cmd_append_status(_append_args(also=[str(md)]))
    shown = subprocess.run(
        ["git", "-C", str(wf.REPO), "show", "--name-only", "--pretty=format:", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout
    assert "evidence.md" in shown


def test_append_status_rejects_empty_evidence(new_run):
    """--evidence 为空是硬错误。"""
    with pytest.raises(SystemExit):
        wf.cmd_append_status(_append_args(evidence="   "))


def test_append_status_blocker_registers_row(new_run):
    """--state 阻塞 必须要求 --blocker 并登记阻塞行。"""
    rd = new_run()
    with pytest.raises(SystemExit):
        wf.cmd_append_status(_append_args(state="阻塞", blocker=""))
    wf.cmd_append_status(_append_args(state="阻塞", blocker="等 API key"))
    assert "B-001" in _status(rd).read_text(encoding="utf-8")


# ================================================================ 4. commit
def test_commit_rejects_non_git_repo(tmp_path):
    args = argparse.Namespace(
        repo=str(tmp_path), run="r1", round=1, message="m", paths=["x"]
    )
    with pytest.raises(SystemExit):
        wf.cmd_commit(args)


def test_commit_requires_paths(tmp_git_repo):
    args = argparse.Namespace(
        repo=str(tmp_git_repo), run="r1", round=1, message="m", paths=[]
    )
    with pytest.raises(SystemExit):
        wf.cmd_commit(args)


def test_commit_success(tmp_git_repo, capsys):
    (tmp_git_repo / "README.md").write_text("changed\n", encoding="utf-8")
    args = argparse.Namespace(
        repo=str(tmp_git_repo), run="r1", round=2, message="收口", paths=["README.md"]
    )
    wf.cmd_commit(args)
    out = capsys.readouterr().out
    assert "[OK] 已提交" in out
    subj = subprocess.run(
        ["git", "-C", str(tmp_git_repo), "log", "-1", "--pretty=%s"],
        capture_output=True,
        text=True,
    ).stdout
    assert "audit(r1) r2: 收口" in subj


def test_commit_nothing_staged_dies(tmp_git_repo):
    args = argparse.Namespace(
        repo=str(tmp_git_repo), run="r1", round=1, message="m", paths=["README.md"]
    )
    with pytest.raises(SystemExit):
        wf.cmd_commit(args)  # README 无改动 → 无可提交内容


# ================================================================ 5. ledger
_DELEGATIONS = (
    "# DELEGATIONS — t-run\n\n"
    "| 时间 | 轮次 | 角色 | 执行体 | WS | session | 状态 | 耗时 | cost($) | tokens(in/out/cache-r) | 回执摘要 |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    "| 2026-10-14 10:00 | 1 | pmo | pmo | - | `s1` | ok | 12.0s | 0.001 | 100/20/500 | done |\n"
    "| 2026-10-14 10:05 | 1 | tdo | tdo-a1 | WS-1 | `s2` | ok | 30.0s | 0.002 | 200/40/1000 | done |\n"
)


def test_ledger_no_file(new_run, capsys):
    new_run()
    wf.cmd_ledger(argparse.Namespace(run_id="t-run"))
    assert "还没有委派记录" in capsys.readouterr().out


def test_ledger_summary_by_role(new_run, capsys):
    rd = new_run()
    (rd / "DELEGATIONS.md").write_text(_DELEGATIONS, encoding="utf-8")
    wf.cmd_ledger(argparse.Namespace(run_id="t-run"))
    out = capsys.readouterr().out
    assert "== 委派账本 · t-run ==" in out
    assert "pmo" in out and "tdo" in out
    assert "0.003000" in out  # cost 合计 0.001+0.002
    assert "300" in out  # input 合计 100+200


# ================================================================ 6. doctor
def test_doctor_missing_run_dies(wf_env):
    with pytest.raises(SystemExit):
        wf.doctor("no-such-run")


def test_doctor_missing_file_reports_error(new_run, capsys):
    rd = new_run()
    (rd / "PROJECT.md").unlink()
    assert wf.doctor("t-run") == 1
    assert "缺文件: PROJECT.md" in capsys.readouterr().out


def test_doctor_missing_header_reports_error(new_run):
    rd = new_run()
    (rd / "DECISIONS.md").write_text("# 没有 wf-doc 块\n", encoding="utf-8")
    assert wf.doctor("t-run") == 1


def test_doctor_illegal_state_reports_error(new_run):
    rd = new_run()
    wf.write_header_field(_status(rd), "state", "bogus")
    assert wf.doctor("t-run") == 1


def test_doctor_healthy_run_passes(new_run, capsys):
    new_run()
    assert wf.doctor("t-run") == 0
    assert "结果: PASS" in capsys.readouterr().out


def test_doctor_json_shape(new_run, capsys):
    new_run()
    capsys.readouterr()  # 丢弃 new_run 的打印，只留 doctor 的 JSON
    wf.doctor("t-run", as_json=True)
    payload = json.loads(capsys.readouterr().out)
    assert payload["run"] == "t-run"
    assert set(payload) >= {"errors", "warns", "ok"}


# ============================================ 7. wf-doc tags / state --by
def test_new_run_writes_machine_readable_template_metadata(wf_env):
    """AFC-003：new-run 从 SPEC §0 投影 baseline/contracts/tags/maturity。"""
    args = argparse.Namespace(
        run_id="t-meta",
        goal="元数据测试",
        goal_file="",
        project_root="/tmp/proj",
        scope="runs/t-meta/**",
        template=str(wf.TEMPLATES / "specialized" / "openrig-workflow-master"),
        project_name="meta",
        tdo=1,
        force=False,
    )
    wf.cmd_new_run(args)
    h = wf.read_header(wf.RUNS / "t-meta" / "PROJECT.md")
    assert h["baseline"] == "composite/two-plane-orchestration@1.0.0"
    assert h["contracts"] == "strategy@1.0.0, research@1.0.0, architecture@1.0.0, optimize@1.0.0, verify@1.0.0, audit@1.0.0"
    assert h["primary_type"] == "composite/two-plane-orchestration"
    assert h["maturity"] == "M3"
    assert "template/openrig-workflow-master" in h["tags"]


def test_state_by_rejects_unauthorized_role(new_run):
    """AFC-003：PMO 迁移不能由 QA 冒充。"""
    new_run(run_id="t-state-by")
    with pytest.raises(SystemExit):
        wf.cmd_state(
            argparse.Namespace(
                run_id="t-state-by", doc="PROJECT", new_state="plan-ready", by="qa"
            )
        )


def test_state_by_accepts_authorized_role(new_run):
    new_run(run_id="t-state-ok")
    wf.cmd_state(
        argparse.Namespace(
            run_id="t-state-ok", doc="PROJECT", new_state="plan-ready", by="pmo"
        )
    )
    assert wf.read_header(wf.RUNS / "t-state-ok" / "PROJECT.md")["state"] == "plan-ready"


# ============================================ 8. PLAN-GATE 机检
def test_doctor_plan_gate_accepts_complete_round_plan(new_run):
    rd = new_run(run_id="t-plan-gate-ok")
    (rd / "SPEC.md").write_text(
        "baseline: composite/fix-wave@1.0.0\n"
        "contracts: audit@1.0.0, optimize@1.0.0, verify@1.0.0\n",
        encoding="utf-8",
    )
    (rd / "ROUND-PLAN.md").write_text(
        "contract: research@1.0.0\n"
        "produces: reports/ANALYSIS.md\n"
        "gate: pytest -q\n"
        "budget: targets=3; tdo=2; minutes=60\n"
        "NOT-DOING: no-write\n",
        encoding="utf-8",
    )
    assert wf.doctor("t-plan-gate-ok", phase="plan-gate") == 0


def test_doctor_plan_gate_blocks_missing_not_doing(new_run):
    rd = new_run(run_id="t-plan-gate-bad")
    (rd / "SPEC.md").write_text(
        "baseline: none — atomic\ncontracts: audit@1.0.0\n", encoding="utf-8"
    )
    (rd / "ROUND-PLAN.md").write_text(
        "contract: research@1.0.0\n"
        "produces: reports/ANALYSIS.md\n"
        "gate: pytest -q\n"
        "budget: targets=3; tdo=2; minutes=60\n",
        encoding="utf-8",
    )
    assert wf.doctor("t-plan-gate-bad", phase="plan-gate") == 1


# ============================================ 9. 关闭收口 open S1/S2
def test_closure_blocks_open_s2(new_run):
    rd = new_run(run_id="t-close-s2")
    import sys as _sys
    from pathlib import Path as _Path
    _scripts = _Path(__file__).resolve().parent.parent / "scripts"
    if str(_scripts) not in _sys.path:
        _sys.path.insert(0, str(_scripts))
    import issues  # noqa: E402
    import argparse as _argparse

    issues.cmd_add(
        _argparse.Namespace(
            xlsx=str(rd / "ISSUES.xlsx"), round=1, type="风险", title="open S2",
            desc="", severity="S2", status="新建", owner="PMO",
            source="STATUS-Round-1.md#进度", action="修复", need_decision="no",
            id=None, force=False,
        )
    )
    blockers = wf._closure_issue_blockers(rd)
    assert blockers and "S2" in blockers[0]


def test_state_critical_transition_requires_by(new_run):
    """AFC-003：waiting-main 关闭类迁移不得省略 --by。"""
    new_run(run_id="t-state-critical")
    wf.write_header_field(wf.RUNS / "t-state-critical" / "PROJECT.md", "state", "plan-ready")
    with pytest.raises(SystemExit):
        wf.cmd_state(
            argparse.Namespace(
                run_id="t-state-critical", doc="PROJECT", new_state="waiting-main", by=""
            )
        )


# ============================================ 10. ROUND-PLAN / VERDICT 投影
def _contract_block() -> str:
    return (
        "\n<!-- wf:round-plan\n"
        "contract: research@1.0.0\n"
        "produces: reports/ANALYSIS.md\n"
        "gate: pytest -q\n"
        "budget: targets=3; tdo=2; minutes=60\n"
        "NOT-DOING: no-write\n"
        "-->\n"
    )


def test_state_plan_ready_projects_round_plan_strict(new_run):
    rd = new_run(run_id="t-proj-plan")
    (rd / "SPEC.md").write_text(
        "baseline: none — atomic\ncontracts: research@1.0.0\n", encoding="utf-8"
    )
    with (rd / "PROJECT.md").open("a", encoding="utf-8") as f:
        f.write(_contract_block())
    wf.write_header_field(rd / "PROJECT.md", "contract_mode", "strict")
    wf.cmd_state(
        argparse.Namespace(run_id="t-proj-plan", doc="PROJECT", new_state="plan-ready", by="pmo")
    )
    plan = (rd / "ROUND-PLAN.md").read_text(encoding="utf-8")
    assert "contract: research@1.0.0" in plan
    assert "NOT-DOING: no-write" in plan
    assert wf.doctor("t-proj-plan", phase="plan-gate") == 0


def test_state_plan_ready_strict_requires_projection_block(new_run):
    rd = new_run(run_id="t-proj-missing")
    (rd / "SPEC.md").write_text(
        "baseline: none — atomic\ncontracts: research@1.0.0\n", encoding="utf-8"
    )
    wf.write_header_field(rd / "PROJECT.md", "contract_mode", "strict")
    with pytest.raises(SystemExit):
        wf.cmd_state(
            argparse.Namespace(
                run_id="t-proj-missing", doc="PROJECT", new_state="plan-ready", by="pmo"
            )
        )


def test_sync_verdict_projects_hidden_block(new_run):
    rd = new_run(run_id="t-verdict")
    with (rd / "DECISIONS.md").open("a", encoding="utf-8") as f:
        f.write(
            "\n<!-- wf:verdict\n"
            "decision: CONTINUE\n"
            "rationale: tests green\n"
            "next: R2\n"
            "contracts_used: research@1.0.0\n"
            "budget: used=1/3; time=10m\n"
            "queue_patch: none\n"
            "open_items: none\n"
            "notes: ok\n"
            "-->\n"
        )
    out = wf.sync_verdict(rd)
    assert out is not None and out.is_file()
    assert "decision: CONTINUE" in out.read_text(encoding="utf-8")


# ============================================ 11. STATUS WS/交接绑定
def test_status_binding_checks_reject_duplicate_and_unknown_ws():
    proj = "## 4. 分任务\n\n| WS | 任务 |\n| --- | --- |\n| WS-1 | x |\n\n## 5. 轮次\n"
    status = (
        "<!-- wf:progress:start -->\n"
        "| 时间 | 执行体 | WS | 动作 | 证据 | 状态 |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| 10:00 | tdo-a | WS-9 | act | ev | 完成 |\n"
        "<!-- wf:progress:end -->\n\n"
        "## 交接给 QA\n"
        "- **WS-1**：x\n- **WS-1**：y\n- **WS-2**：z\n\n"
        "<!-- wf:handoff:start -->\n"
    )
    errors, _warns = wf._status_binding_checks(proj, status)
    blob = "\n".join(errors)
    assert "WS-9 未在 PROJECT §4 登记" in blob
    assert "重复 WS 小节: WS-1" in blob
    assert "交接给 QA 的 WS 未在 PROJECT §4 登记: WS-2" in blob


def test_status_binding_checks_accept_consistent_ws():
    proj = "## 4. 分任务\n\n| WS | 任务 |\n| --- | --- |\n| WS-1 | x |\n\n## 5. 轮次\n"
    status = (
        "<!-- wf:progress:start -->\n"
        "| 时间 | 执行体 | WS | 动作 | 证据 | 状态 |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| 10:00 | tdo-a | WS-1 | act | ev | 完成 |\n"
        "<!-- wf:progress:end -->\n\n"
        "## 交接给 QA\n"
        "- **WS-1**：done\n\n"
        "<!-- wf:handoff:start -->\n"
    )
    errors, warns = wf._status_binding_checks(proj, status)
    assert errors == [] and warns == []


# ============================================ 12. status-all / overview
def test_status_all_scans_runs_as_json_without_writes(new_run, capsys):
    rd = new_run(run_id="t-status-all")
    bridge = rd / "openrig" / "OPENRIG-BRIDGE.json"
    bridge.parent.mkdir(parents=True)
    bridge.write_text('{"schemaVersion": 2}', encoding="utf-8")
    capsys.readouterr()  # 丢弃 new-run 的 [OK] 输出
    before = {p: p.stat().st_mtime_ns for p in rd.rglob("*") if p.is_file()}
    wf.cmd_status_all(argparse.Namespace(json=True))
    data = json.loads(capsys.readouterr().out)
    row = next(x for x in data["runs"] if x["run"] == "t-status-all")
    assert row["projectState"] == "pmo-plan"
    assert row["openrigBridgeSchema"] == 2
    after = {p: p.stat().st_mtime_ns for p in rd.rglob("*") if p.is_file()}
    assert before == after


# ============================================ 13. evidence-pack
def test_evidence_pack_writes_environment_and_hashes(new_run, tmp_path):
    rd = new_run(run_id="t-evidence-pack")
    (rd / "reports").mkdir(exist_ok=True)
    (rd / "reports" / "sample.md").write_text("sample\n", encoding="utf-8")
    out = tmp_path / "evidence-pack.md"
    wf.cmd_evidence_pack(
        argparse.Namespace(
            run_id="t-evidence-pack", out=str(out), pytest=False, test_timeout=10, json=False
        )
    )
    text = out.read_text(encoding="utf-8")
    assert "# EVIDENCE PACK — t-evidence-pack" in text
    assert "gitHead:" in text and "python:" in text
    assert "reports/sample.md" in text
    assert "sha256" in text


# ============================================ 14. 资源准入
def test_resource_admission_rejects_low_memory(monkeypatch):
    monkeypatch.setattr(wf, "system_free_mb", lambda: 100)
    with pytest.raises(SystemExit):
        wf.resource_admission(2)


def test_resource_admission_rejects_too_many_agents(monkeypatch):
    monkeypatch.setenv("WF_MAX_CONCURRENT_AGENTS", "1")
    monkeypatch.setattr(wf, "system_free_mb", lambda: 4096)
    with pytest.raises(SystemExit):
        wf.resource_admission(2)


def test_resource_admission_force_bypasses_limits(monkeypatch):
    monkeypatch.setattr(wf, "system_free_mb", lambda: 10)
    result = wf.resource_admission(99, force=True)
    assert result["admitted"] is True and result["reason"] == "forced"


# ============================================ 15. run-end commit
def test_commit_run_commits_only_run_directory(new_run):
    rd = new_run(run_id="t-commit-run")
    (rd / "reports").mkdir(exist_ok=True)
    f = rd / "reports" / "out.md"
    f.write_text("out\n", encoding="utf-8")
    wf.cmd_commit_run(
        argparse.Namespace(run_id="t-commit-run", message="round end", also=[], dry_run=False)
    )
    shown = subprocess.run(
        ["git", "-C", str(wf.REPO), "show", "--name-only", "--pretty=format:", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout
    assert "workflow-group/runs/t-commit-run/reports/out.md" in shown
    assert "workflow-group/scripts/wf.py" not in shown


# ============================================ 16. STATUS shards
def test_append_and_merge_status_shards(new_run):
    rd = new_run(run_id="t-shards")
    for agent, ws in (("tdo-a", "WS-1"), ("tdo-b", "WS-2")):
        wf.cmd_append_shard(
            argparse.Namespace(
                run_id="t-shards", agent=agent, ws=ws, action=f"{agent} done",
                evidence=f"runs/t-shards/{agent}.md", state="完成", blocker="",
            )
        )
    assert len(list((rd / "status-shards").glob("*.jsonl"))) == 2
    wf.cmd_merge_shards(
        argparse.Namespace(run_id="t-shards", agent="merge", wait=0, steal=False)
    )
    text = (rd / "STATUS-Round-1.md").read_text(encoding="utf-8")
    assert "tdo-a done" in text and "tdo-b done" in text
    assert wf.read_header(rd / "STATUS-Round-1.md")["state"] == "tdo-in-progress"
    assert not list((rd / "status-shards").glob("*.jsonl"))
    assert list((rd / "status-shards" / "merged").rglob("*.jsonl"))
