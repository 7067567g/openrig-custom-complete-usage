# -*- coding: utf-8 -*-
"""WS-1 测试夹具（tdo-a1 独占）。

提供：临时 git 仓库 + 临时 runs 目录 + 真实四件套 run 工厂。
隔离保证：绝不写入真实 `workflow-group/runs/`，也绝不向 KB 仓库提交。
WS-2 的测试文件不得依赖本文件的夹具（见 PROJECT §0.1 文件边界）。
"""

import argparse
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import wf  # noqa: E402  （脚本非包，需先注入 scripts/ 到 sys.path）


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )


def git_ok(repo, *args):
    """跑 git 并要求成功，失败直接断言爆出（便于定位环境问题）。"""
    r = _git(repo, *args)
    assert r.returncode == 0, f"git {' '.join(args)} 失败: {r.stdout}{r.stderr}"
    return r


@pytest.fixture
def tmp_git_repo(tmp_path):
    """已初始化、含 `.gitignore`(`*.log`) 与初始提交的临时 git 仓库。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    git_ok(repo, "init", "-q")
    git_ok(repo, "config", "user.email", "tdo@test.local")
    git_ok(repo, "config", "user.name", "tdo-test")
    (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    git_ok(repo, "add", "--", "README.md", ".gitignore")
    git_ok(repo, "commit", "-q", "-m", "seed")
    return repo


@pytest.fixture
def wf_env(tmp_git_repo, monkeypatch):
    """把 wf 的 REPO/ROOT/RUNS 重定向到临时仓库；TEMPLATES 仍用真实模板目录。"""
    wg = tmp_git_repo / "workflow-group"
    runs = wg / "runs"
    runs.mkdir(parents=True)
    monkeypatch.setattr(wf, "REPO", tmp_git_repo)
    monkeypatch.setattr(wf, "ROOT", wg)
    monkeypatch.setattr(wf, "RUNS", runs)
    return SimpleNamespace(repo=tmp_git_repo, wg=wg, runs=runs, monkeypatch=monkeypatch)


@pytest.fixture
def new_run(wf_env):
    """工厂：在临时 runs/ 下用真实模板实例化一个四件套 run。"""

    def _make(run_id="t-run", **over):
        args = argparse.Namespace(
            run_id=run_id,
            goal="测试目标",
            goal_file="",
            project_root="/tmp/proj",
            scope="workflow-group/**",
            template="",
            project_name="",
            tdo=2,
            force=False,
        )
        for k, v in over.items():
            setattr(args, k, v)
        wf.cmd_new_run(args)
        return wf.RUNS / run_id

    return _make


@pytest.fixture
def git():
    """供测试直接调用的 git 包装（失败返回 CompletedProcess，不抛）。"""
    return _git
