import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from hrm_coder import config as cfg  # noqa: E402


def test_default_paths_resolve(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    conf = cfg.load_config()
    assert conf.paths.data_root == Path("data")
    assert conf.paths.runs_root == Path("runs")
    assert conf.paths.artifacts_root == Path("artifacts")


def test_override_paths(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    conf = cfg.load_config(
        overrides=[
            "paths.data_root=/tmp/data",
            "paths.runs_root=r",
            "paths.artifacts_root=a",
        ]
    )
    assert conf.paths.data_root == Path("/tmp/data")
    assert conf.paths.runs_root == Path("r")
    assert conf.paths.artifacts_root == Path("a")
