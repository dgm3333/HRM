import os
import sys
from types import SimpleNamespace

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from runners import sandbox_detector  # noqa: E402


def test_detect_sandboxes_all_missing(monkeypatch):
    monkeypatch.setattr(sandbox_detector.shutil, "which", lambda cmd: None)
    result = sandbox_detector.detect_sandboxes()
    assert set(result.keys()) == {"isolate", "nsjail", "runsc"}
    assert all(not info["available"] for info in result.values())


def test_detect_sandboxes_reports_version(monkeypatch):
    def fake_which(cmd: str):
        return f"/usr/bin/{cmd}"

    def fake_run(cmd, capture_output, text):
        return SimpleNamespace(returncode=0, stdout=f"{cmd[0]} version 1.2\n")

    monkeypatch.setattr(sandbox_detector.shutil, "which", fake_which)
    monkeypatch.setattr(sandbox_detector.subprocess, "run", fake_run)
    result = sandbox_detector.detect_sandboxes()
    assert all(info["available"] for info in result.values())
    assert all(info["version"].endswith("1.2") for info in result.values())


def test_select_sandbox_prefers_first_available(monkeypatch):
    def fake_detect():
        return {
            "isolate": {"available": False},
            "nsjail": {"available": True},
            "runsc": {"available": True},
        }

    monkeypatch.setattr(sandbox_detector, "detect_sandboxes", fake_detect)
    name, info = sandbox_detector.select_sandbox()
    assert name == "nsjail"
    assert info["available"]


def test_select_sandbox_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr(
        sandbox_detector,
        "detect_sandboxes",
        lambda: {
            "isolate": {"available": False},
            "nsjail": {"available": False},
            "runsc": {"available": False},
        },
    )
    name, info = sandbox_detector.select_sandbox()
    assert name is None and info is None
