"""Tests for the minimal CMake build helpers."""
from __future__ import annotations

from pathlib import Path
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from runners.cpp_build import build, configure, run_tests  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "hrm_coder" / "cpp"


def test_build_and_test(tmp_path: Path) -> None:
    """Configure, build, and run the placeholder C++ tests."""
    build_dir = tmp_path / "build"
    cfg = configure(SRC_DIR, build_dir)
    assert cfg.returncode == 0, cfg.stderr

    comp = build(build_dir)
    assert comp.returncode == 0, comp.stderr

    res = run_tests(build_dir)
    assert res.returncode == 0, res.stderr
