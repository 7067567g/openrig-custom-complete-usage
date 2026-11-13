import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md", "README.zh-CN.md", "WORKFLOW.md", "LICENSE", "VERSION",
    "scripts/wf.py", "scripts/openrig_smoke.py",
    "templates/specialized/openrig-workflow-master/PREFLIGHT.md",
    "templates/specialized/openrig-workflow-master/render_master.py",
    "sctg-kit/sctg.py", "examples/openrig-minimal/README.md",
]

def test_required_files_exist():
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    assert not missing, missing

def test_runs_directory_is_placeholder_only():
    entries = {p.name for p in (ROOT / "runs").iterdir()}
    assert entries <= {".gitkeep"}

def test_smoke_report_is_complete():
    report = json.loads((ROOT / "reports" / "openrig_smoke.json").read_text(encoding="utf-8"))
    assert report["rounds"] == 12
    assert report["passed"] == 12
    assert all(r["render"] == 0 and r["bridgeDoctorPass"] and r["workflowOk"] and r["upPlanStatus"] == "planned" for r in report["results"])
