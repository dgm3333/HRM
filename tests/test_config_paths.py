import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from hrm_coder import config as cfg  # noqa: E402


def test_default_paths_resolve(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    conf = cfg.load_config()
    project_root = Path(__file__).resolve().parents[1]
    assert conf.paths.data_root == project_root / "data"
    assert conf.paths.runs_root == project_root / "runs"
    assert conf.paths.artifacts_root == project_root / "artifacts"


def test_override_paths(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    conf = cfg.load_config(
        overrides=[
            "paths.data_root=/tmp/data",
            "paths.runs_root=r",
            "paths.artifacts_root=a",
        ]
    )
    project_root = Path(__file__).resolve().parents[1]
    assert conf.paths.data_root == Path("/tmp/data")
    assert conf.paths.runs_root == project_root / "r"
    assert conf.paths.artifacts_root == project_root / "a"
