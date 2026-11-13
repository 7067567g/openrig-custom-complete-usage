# -*- coding: utf-8 -*-
"""WS-A · render_master.py bridge v2 / bundle 可搬迁定向测试（G1）

覆盖 PROJECT §4.2 WS-A 的三条交付自查：

  1. bridge 升 ``schemaVersion=2``，bundle 内路径相对化
     （``bundleDir="."`` / ``rigSpec="rig.yaml"`` / ``workflowSpec="workflow.yaml"``）；
  2. 同一 run、同一参数渲染到两个临时 output-dir，5 个产物逐字节一致（M3）；
  3. 渲染产物落盘后 ``openrig_bridge.py doctor`` v2 正例 rc=0。

全部离线：只在 ``tmp_path`` 内渲染，不启动 daemon、不调 OpenRig CLI、不联网。

前置（P-004 / D-021）：doctor v2 正例与「可搬迁」两条用例需要 PATH 上有**可解析的真实**
``rig``——渲染出的 bridge 把 ``openrigCli`` 记为 ``rig``，doctor 从 PATH 解析它。
CI runner（`.github/workflows/wf-validate.yml`，无 rig）上这两条按 ``requires_rig`` 诚实 SKIP
并写明理由，门禁保持 0 failed；有 ``rig`` 时真实执行，覆盖不删除。
**禁止**用 ``python -V`` 之类假 CLI 消音（会让断言不再证明任何事，D-015 第 1 条）。

运行：
  python3 -m pytest workflow-group/tests/test_render_master_portability.py -q

替补实现开关（证明用例先红后绿）：
  OPENRIG_RENDER_MASTER=/tmp/render_master_before.py \\
    python3 -m pytest workflow-group/tests/test_render_master_portability.py -q
默认加载 workflow-group/templates/specialized/openrig-workflow-master/render_master.py。
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # workflow-group/
MASTER = ROOT / "templates" / "specialized" / "openrig-workflow-master"
RENDER_PY = Path(os.environ.get("OPENRIG_RENDER_MASTER") or (MASTER / "render_master.py"))
DOCTOR_PY = MASTER / "tools" / "openrig_bridge.py"

# The five files render_master.py ships (MANIFEST_FILES): four templates + bridge.
ARTIFACTS = (
    "rig.yaml",
    "workflow.yaml",
    "agents/worker/agent.yaml",
    "guidance/team.md",
    "OPENRIG-BRIDGE.json",
)
RUN_ID = "portability-20260101"


def render(project_root: Path, output_dir: Path, run_id: str = RUN_ID) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(RENDER_PY),
            "--run-id",
            run_id,
            "--project-root",
            str(project_root),
            "--output-dir",
            str(output_dir),
            "--json",
        ],
        text=True,
        capture_output=True,
    )


def bundle_path(tmp_path: Path, lane: str, run_id: str = RUN_ID) -> Path:
    """A bundle at <tmp>/<lane>/runs/<run_id>/openrig so doctor's runId check applies."""
    return tmp_path / lane / "runs" / run_id / "openrig"


def hashes(bundle: Path) -> dict:
    return {
        name: hashlib.sha256((bundle / name).read_bytes()).hexdigest()
        for name in ARTIFACTS
    }


def read_bridge(bundle: Path) -> dict:
    return json.loads((bundle / "OPENRIG-BRIDGE.json").read_text(encoding="utf-8"))


def doctor(bundle: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(DOCTOR_PY), "doctor", "--run-dir", str(bundle.parent)],
        text=True,
        capture_output=True,
    )


def test_render_writes_five_artifacts(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    bundle = bundle_path(tmp_path, "a")

    proc = render(project_root, bundle)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    for name in ARTIFACTS:
        assert (bundle / name).is_file(), name


def test_bridge_is_schema_v2_with_relative_paths(tmp_path):
    """G1：bridge 升 v2，bundle 内路径相对，运行期字段保持绝对语义。"""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    bundle = bundle_path(tmp_path, "a")

    assert render(project_root, bundle).returncode == 0

    bridge = read_bridge(bundle)
    assert bridge["schemaVersion"] == 2
    assert bridge["bundleDir"] == "."
    assert bridge["rigSpec"] == "rig.yaml"
    assert bridge["workflowSpec"] == "workflow.yaml"
    # runtime fields keep absolute, machine-local semantics
    assert Path(bridge["projectRoot"]).is_absolute()
    assert Path(bridge["openrigHome"]).is_absolute()


def test_two_output_dirs_are_byte_identical(tmp_path):
    """M3：同 run 同参数渲染到两个 output-dir，5 个产物逐字节一致。"""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    bundle_a = bundle_path(tmp_path, "a")
    bundle_b = bundle_path(tmp_path, "b")

    proc_a = render(project_root, bundle_a)
    proc_b = render(project_root, bundle_b)
    assert proc_a.returncode == 0, proc_a.stdout + proc_a.stderr
    assert proc_b.returncode == 0, proc_b.stdout + proc_b.stderr

    hashes_a = hashes(bundle_a)
    hashes_b = hashes(bundle_b)
    assert hashes_a == hashes_b, {k: (hashes_a[k], hashes_b[k]) for k in hashes_a if hashes_a[k] != hashes_b[k]}


# P-004 / D-021: a rendered bridge names `openrigCli="rig"`, and `doctor` resolves
# that executable from PATH. The live-CLI coverage therefore stays under this single
# explicit `requires_rig` marker instead of being deleted:
#   * CI runner (no `rig`)          -> these tests SKIP with the reason below (0 failed)
#   * developer/QA seat (has `rig`) -> they run for real and the assertion still means
#                                      what its name says ("passes doctor v2")
# A fake CLI such as `python -V` is forbidden: doctor's live checks (workflow list /
# ps / queue list) would then pass while proving nothing (D-015 ruling one).
requires_rig = pytest.mark.skipif(
    shutil.which("rig") is None,
    reason="需要可解析的 rig CLI：渲染出的 bridge 把 openrigCli 记为 'rig'，doctor 需从 PATH 解析（D-021）",
)


@requires_rig
def test_rendered_bundle_passes_doctor_v2(tmp_path):
    """G1 正例：渲染出的 v2 bundle 必须能被 doctor 判定 PASS。"""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    bundle = bundle_path(tmp_path, "a")

    assert render(project_root, bundle).returncode == 0

    proc = doctor(bundle)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS bridge" in proc.stdout
    assert "schema=2" in proc.stdout
    assert [ln for ln in proc.stdout.splitlines() if ln.startswith("FAIL ")] == []


@requires_rig
def test_bundle_is_relocatable(tmp_path):
    """可搬迁：整目录复制到别处后 doctor 仍 PASS（相对路径不绑定原目录）。"""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    bundle = bundle_path(tmp_path, "a")
    assert render(project_root, bundle).returncode == 0
    assert doctor(bundle).returncode == 0

    moved = bundle_path(tmp_path, "relocated")
    moved.parent.mkdir(parents=True)
    subprocess.run(["cp", "-a", str(bundle), str(moved)], check=True)

    proc = doctor(moved)
    assert proc.returncode == 0, proc.stdout + proc.stderr
