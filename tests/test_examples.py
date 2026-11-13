import subprocess, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMOS = ["sctg-minimal", "multi-card", "decision", "rollback", "two-seat-handoff"]

@pytest.mark.parametrize("name", DEMOS)
def test_example_demo_passes(name):
    p = subprocess.run([sys.executable, str(ROOT / "examples" / name / "run_demo.py")], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stdout + p.stderr
    assert '"verdict": "PASS"' in p.stdout or '"verdict":"PASS"' in p.stdout
