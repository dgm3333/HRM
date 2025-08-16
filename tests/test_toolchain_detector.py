import os
import sys
from types import SimpleNamespace

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from runners import toolchain_detector  # noqa: E402


def test_detect_toolchains_all_missing(monkeypatch):
    monkeypatch.setattr(toolchain_detector.shutil, "which", lambda cmd: None)
    result = toolchain_detector.detect_toolchains()
    expected = {"g++", "clang++", "lcov", "llvm-cov", "gcov"}
    assert set(result.keys()) == expected
    assert all(not info["available"] for info in result.values())


def test_detect_toolchains_reports_version(monkeypatch):
    def fake_which(cmd: str):
        return f"/usr/bin/{cmd}"

    def fake_run(cmd, capture_output, text):
        return SimpleNamespace(returncode=0, stdout=f"{cmd[0]} version 1.2\n")

    monkeypatch.setattr(toolchain_detector.shutil, "which", fake_which)
    monkeypatch.setattr(toolchain_detector.subprocess, "run", fake_run)
    result = toolchain_detector.detect_toolchains()
    assert all(info["available"] for info in result.values())
    assert all(info["version"].endswith("1.2") for info in result.values())


def test_select_compiler_prefers_first_available(monkeypatch):
    def fake_detect():
        return {
            "g++": {"available": False},
            "clang++": {"available": True},
        }

    monkeypatch.setattr(toolchain_detector, "detect_toolchains", fake_detect)
    name, info = toolchain_detector.select_compiler()
    assert name == "clang++"
    assert info["available"]


def test_select_compiler_handles_missing(monkeypatch):
    def fake_detect():
        return {
            "g++": {"available": False},
            "clang++": {"available": False},
        }

    monkeypatch.setattr(toolchain_detector, "detect_toolchains", fake_detect)
    name, info = toolchain_detector.select_compiler()
    assert name is None and info is None
