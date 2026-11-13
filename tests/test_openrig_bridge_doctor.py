# -*- coding: utf-8 -*-
"""WS-1 · openrig_bridge.py doctor 假 PASS 定向测试

覆盖 PROJECT §4.2 的三类假 PASS（A-1/A-2/A-3）与 live run 回归：

  A-1  runId 与 run 目录不交叉校验
  A-2  openrigCli 只校验 argv[0]，脚本路径不存在仍 PASS
  A-3  bundleDir 完全不校验，spec 可落在 bundle 外

全部离线：夹具在 tmp_path 内合成 rig.yaml / workflow.yaml / OPENRIG-BRIDGE.json，
不碰真实 runs/、不调 OpenRig CLI、不联网。
每条断言都走真实 CLI（subprocess + 退出码），因此同时覆盖 0/1 契约与
`FAIL <field> bridge=... spec=...` 行格式。

运行：
  python3 -m pytest workflow-group/tests/test_openrig_bridge_doctor.py -q

替补实现开关（证明用例非空转 / 先红后绿）：
  OPENRIG_BRIDGE_DOCTOR=/tmp/openrig_bridge_before.py \\
    python3 -m pytest workflow-group/tests/test_openrig_bridge_doctor.py -q
默认加载 workflow-group/templates/specialized/openrig-workflow-master/tools/openrig_bridge.py。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # workflow-group/
DOCTOR_PY = Path(
    os.environ.get("OPENRIG_BRIDGE_DOCTOR")
    or (ROOT / "templates" / "specialized" / "openrig-workflow-master" / "tools" / "openrig_bridge.py")
)
LIVE_RUN = ROOT / "runs" / "openrig-audit-fix-20261020"

RIG_NAME = "test-rig"
WORKFLOW_ID = "test-workflow"
SEAT_MAP = {
    "main": f"control-main@{RIG_NAME}",
    "pmo": f"control-pmo@{RIG_NAME}",
    "tdo_opencode": f"exec-tdo-oc@{RIG_NAME}",
    "tdo_dsh": f"exec-tdo-dsh@{RIG_NAME}",
    "qa": f"assurance-qa@{RIG_NAME}",
}


def _rig_yaml(project_root: str, name: str = RIG_NAME) -> str:
    return (
        'version: "0.2"\n'
        f'name: "{name}"\n'
        "pods:\n"
        "  - id: control\n"
        "    members:\n"
        "      - id: main\n"
        "        role: main\n"
        f'        cwd: "{project_root}"\n'
        "      - id: pmo\n"
        "        role: pmo\n"
        f'        cwd: "{project_root}"\n'
    )


def _workflow_yaml(rig: str = RIG_NAME, workflow_id: str = WORKFLOW_ID) -> str:
    lines = [
        "workflow:",
        f'  id: "{workflow_id}"',
        "  target:",
        f'    rig: "{rig}"',
        "  roles:",
    ]
    for role, seat in SEAT_MAP.items():
        lines.append(f"    {role}:")
        lines.append(f"      preferred_targets: [{seat}]")
    return "\n".join(lines) + "\n"


def _bridge(run_id: str, project_root: str, bundle: Path, cli: str) -> dict:
    return {
        "schemaVersion": 1,
        "runId": run_id,
        "projectRoot": project_root,
        "bundleDir": str(bundle),
        "rigName": RIG_NAME,
        "workflowId": WORKFLOW_ID,
        "rigSpec": str(bundle / "rig.yaml"),
        "workflowSpec": str(bundle / "workflow.yaml"),
        "openrigCli": cli,
        "openrigHome": str(bundle.parent / "home"),
        "daemonPort": 47895,
        "seatMap": dict(SEAT_MAP),
        "policy": {"mode": "managed-isolated", "safetyMode": "on-demand"},
    }


def _bridge_v2(run_id: str, project_root: str, bundle: Path, cli: str) -> dict:
    """A v2 bridge: bundle-relative paths, the shape render_master.py now emits."""
    return {
        "schemaVersion": 2,
        "runId": run_id,
        "projectRoot": project_root,
        "bundleDir": ".",
        "rigName": RIG_NAME,
        "workflowId": WORKFLOW_ID,
        "rigSpec": "rig.yaml",
        "workflowSpec": "workflow.yaml",
        "openrigCli": cli,
        "openrigHome": str(bundle.parent / "home"),
        "daemonPort": 47895,
        "seatMap": dict(SEAT_MAP),
        "policy": {"mode": "managed-isolated", "safetyMode": "on-demand"},
    }


def make_run(tmp_path: Path, run_id: str = "t-run-20260101", cli: str | None = None, schema: int = 1) -> Path:
    """合成一个 bridge/rig/workflow 自洽的 run 目录，返回 run_dir。"""
    project_root = tmp_path / "proj"
    project_root.mkdir(exist_ok=True)
    run_dir = tmp_path / "runs" / run_id
    bundle = run_dir / "openrig"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "rig.yaml").write_text(_rig_yaml(str(project_root)), encoding="utf-8")
    (bundle / "workflow.yaml").write_text(_workflow_yaml(), encoding="utf-8")
    factory = _bridge_v2 if schema == 2 else _bridge
    bridge = factory(run_id, str(project_root), bundle, cli or f"{sys.executable} -V")
    write_bridge(run_dir, bridge)
    return run_dir


def write_bridge(run_dir: Path, bridge: dict) -> None:
    (run_dir / "openrig").mkdir(parents=True, exist_ok=True)
    (run_dir / "openrig" / "OPENRIG-BRIDGE.json").write_text(
        json.dumps(bridge, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def read_bridge(run_dir: Path) -> dict:
    return json.loads((run_dir / "openrig" / "OPENRIG-BRIDGE.json").read_text(encoding="utf-8"))


def doctor(run_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(DOCTOR_PY), "doctor", "--run-dir", str(run_dir)],
        text=True,
        capture_output=True,
    )


def fail_lines(proc: subprocess.CompletedProcess) -> list[str]:
    return [ln for ln in proc.stdout.splitlines() if ln.startswith("FAIL ")]


def fail_field(proc: subprocess.CompletedProcess, field: str) -> list[str]:
    return [ln for ln in fail_lines(proc) if ln.startswith(f"FAIL {field} ")]


# ------------------------------------------------------------------ baseline


def test_consistent_bridge_passes(tmp_path):
    proc = doctor(make_run(tmp_path))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS bridge" in proc.stdout
    assert fail_lines(proc) == []


# ------------------------------------------------------------------ A-1 runId


def test_runid_mismatch_is_a_failure(tmp_path):
    """A-1：bridge 里的 runId 与 --run-dir 指向的 run 目录不一致时必须 FAIL runId。"""
    run_dir = make_run(tmp_path, run_id="t-run-20260101")
    bridge = read_bridge(run_dir)
    bridge["runId"] = "some-other-run-20260101"
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    lines = fail_field(proc, "runId")
    assert len(lines) == 1, proc.stdout
    assert "some-other-run-20260101" in lines[0]
    assert "t-run-20260101" in lines[0]


def test_runid_match_does_not_fail(tmp_path):
    run_dir = make_run(tmp_path, run_id="t-run-20260101")
    proc = doctor(run_dir)
    assert fail_field(proc, "runId") == []
    assert proc.returncode == 0, proc.stdout


# --------------------------------------------------------------- A-2 openrigCli


def test_missing_script_after_interpreter_is_a_failure(tmp_path):
    """A-2：`node /missing/wrapper.js` 不能再靠 argv[0] 存在而 PASS。"""
    run_dir = make_run(tmp_path)
    bridge = read_bridge(run_dir)
    bridge["openrigCli"] = f"{sys.executable} /tmp/definitely-missing/bin-wrapper.js"
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    lines = fail_field(proc, "openrigCli")
    assert len(lines) == 1, proc.stdout
    assert "bin-wrapper.js" in lines[0]
    assert "argv[1]" in lines[0]


def test_missing_interpreter_is_a_failure(tmp_path):
    run_dir = make_run(tmp_path)
    bridge = read_bridge(run_dir)
    bridge["openrigCli"] = "/tmp/definitely-missing/rig"
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert fail_field(proc, "openrigCli"), proc.stdout


def test_cli_flags_are_not_treated_as_paths(tmp_path):
    """A-2 反例：`--port 47895` 之类非路径 token 不得被误判为缺失文件。"""
    run_dir = make_run(tmp_path, cli=f"{sys.executable} --port 47895")
    proc = doctor(run_dir)
    assert fail_field(proc, "openrigCli") == []
    assert proc.returncode == 0, proc.stdout


def test_unparseable_cli_is_a_failure(tmp_path):
    run_dir = make_run(tmp_path)
    bridge = read_bridge(run_dir)
    bridge["openrigCli"] = "node 'unterminated"
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert fail_field(proc, "openrigCli"), proc.stdout


# ---------------------------------------------------------------- A-3 bundleDir


def test_bundle_dir_not_the_run_bundle_is_a_failure(tmp_path):
    """A-3：bundleDir 指向别处（此处为真实存在的 /tmp）必须 FAIL bundleDir。"""
    run_dir = make_run(tmp_path)
    bridge = read_bridge(run_dir)
    bridge["bundleDir"] = "/tmp"
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    lines = fail_field(proc, "bundleDir")
    assert len(lines) == 1, proc.stdout
    assert "FAIL bundleDir bridge=/tmp" in lines[0]
    assert str(run_dir / "openrig") in lines[0]


def test_bundle_dir_missing_is_a_failure(tmp_path):
    run_dir = make_run(tmp_path)
    bridge = read_bridge(run_dir)
    bridge["bundleDir"] = str(tmp_path / "nope")
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert fail_field(proc, "bundleDir"), proc.stdout


def test_spec_outside_bundle_is_a_failure(tmp_path):
    """spec 必须落在 bundle 内：把 rig.yaml 挪走并改 rigSpec 指向它。"""
    run_dir = make_run(tmp_path)
    bridge = read_bridge(run_dir)
    stray = tmp_path / "stray" / "rig.yaml"
    stray.parent.mkdir()
    stray.write_text(_rig_yaml(bridge["projectRoot"]), encoding="utf-8")
    bridge["rigSpec"] = str(stray)
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert fail_field(proc, "rig.yaml.inBundle"), proc.stdout


def test_missing_bundle_dir_field_is_reported(tmp_path):
    run_dir = make_run(tmp_path)
    bridge = read_bridge(run_dir)
    del bridge["bundleDir"]
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert "FAIL missing bridge field bundleDir" in proc.stdout


# ------------------------------------------------------------------ v2 正例/负例


def test_v2_bridge_passes(tmp_path):
    """G1 正例：bundle-relative v2 bridge rc=0，并声明 schemaVersion=2。"""
    proc = doctor(make_run(tmp_path, schema=2))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS bridge" in proc.stdout
    assert "schema=2" in proc.stdout
    assert fail_lines(proc) == []


def test_v2_absolute_bundle_dir_is_a_failure(tmp_path):
    """G1 负例①：v2 的 bundleDir 必须是相对路径。"""
    run_dir = make_run(tmp_path, schema=2)
    bridge = read_bridge(run_dir)
    bridge["bundleDir"] = str(run_dir / "openrig")  # absolute: v1 shape in a v2 bridge
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert fail_field(proc, "bundleDir.relative"), proc.stdout


def test_v2_absolute_spec_path_is_a_failure(tmp_path):
    """G1 负例②：v2 的 rigSpec/workflowSpec 必须是相对路径。"""
    run_dir = make_run(tmp_path, schema=2)
    bridge = read_bridge(run_dir)
    bridge["rigSpec"] = str(run_dir / "openrig" / "rig.yaml")
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert fail_field(proc, "rig.yaml.relative"), proc.stdout


def test_v2_spec_escaping_bundle_is_a_failure(tmp_path):
    """G1 负例③：v2 的相对路径不得逃逸 bundle（../ 指到 run 根）。"""
    run_dir = make_run(tmp_path, schema=2)
    bridge = read_bridge(run_dir)
    escaped = run_dir / "rig.yaml"
    escaped.write_text(_rig_yaml(bridge["projectRoot"]), encoding="utf-8")
    bridge["rigSpec"] = "../rig.yaml"
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert fail_field(proc, "rig.yaml.inBundle"), proc.stdout


def test_v2_missing_spec_is_a_failure(tmp_path):
    """G1 负例④：v2 相对路径指向不存在的产物必须 FAIL specFile。"""
    run_dir = make_run(tmp_path, schema=2)
    bridge = read_bridge(run_dir)
    bridge["workflowSpec"] = "nope/workflow.yaml"
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert "FAIL specFile" in proc.stdout


def test_v2_bundle_dir_traversal_is_a_failure(tmp_path):
    """bundleDir 也不得用相对路径跳出预期的 run bundle。"""
    run_dir = make_run(tmp_path, schema=2)
    bridge = read_bridge(run_dir)
    bridge["bundleDir"] = ".."
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert fail_field(proc, "bundleDir"), proc.stdout


def test_unsupported_schema_version_is_a_failure(tmp_path):
    run_dir = make_run(tmp_path, schema=2)
    bridge = read_bridge(run_dir)
    bridge["schemaVersion"] = 3
    write_bridge(run_dir, bridge)

    proc = doctor(run_dir)

    assert proc.returncode == 1
    assert "FAIL schemaVersion" in proc.stdout


# ------------------------------------------------------------- v1 legacy 只读兼容


def test_v1_legacy_passes_with_migration_note(tmp_path):
    """D-007：v1 legacy 保持只读兼容 rc=0，并提示迁移到 schemaVersion=2。"""
    proc = doctor(make_run(tmp_path, schema=1))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "schema=1" in proc.stdout
    assert "legacy bridge schemaVersion=1" in proc.stdout
    assert "schemaVersion=2" in proc.stdout


# ------------------------------------------------------------------ live 回归


@pytest.mark.skipif(
    not (LIVE_RUN / "openrig" / "OPENRIG-BRIDGE.json").is_file(),
    reason="live run bundle not present",
)
def test_live_run_still_passes():
    """修复不得把真实 run 判死：live doctor 必须仍 rc=0。"""
    proc = doctor(LIVE_RUN)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS bridge" in proc.stdout
