import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_version_matches_pyproject():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert version == project["project"]["version"]
    assert version == "0.1.12"
