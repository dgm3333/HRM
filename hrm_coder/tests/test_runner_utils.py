import subprocess

from hrm_coder.config import RunnerConfig
from hrm_coder.runner import create_sandbox_runner, run_in_sandbox
from runners import IsolateRunner, NSJailRunner, sandbox_detector


def test_create_sandbox_runner_explicit():
    cfg = RunnerConfig(sandbox="isolate")
    runner = create_sandbox_runner(cfg)
    assert isinstance(runner, IsolateRunner)


def test_create_sandbox_runner_auto(monkeypatch):
    cfg = RunnerConfig(sandbox="auto")

    def _fake_select():
        return "nsjail", {}

    monkeypatch.setattr(sandbox_detector, "select_sandbox", _fake_select)
    runner = create_sandbox_runner(cfg)
    assert isinstance(runner, NSJailRunner)


def test_run_in_sandbox_passes_limits(monkeypatch):
    cfg = RunnerConfig(
        sandbox="isolate", timeout=3, memory_limit=128, cpus=2, network=False
    )

    called = {}

    def fake_run(self, command, **kwargs):
        called.update(kwargs)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(IsolateRunner, "run", fake_run)
    run_in_sandbox(["/bin/true"], cfg)
    assert called["time_limit"] == 3
    assert called["wall_time"] == 3
    assert called["memory"] == 128 * 1024
    assert called["processes"] == 2
    assert called["network"] is False


def test_run_in_sandbox_override_network(monkeypatch):
    cfg = RunnerConfig(sandbox="isolate", network=False)
    called = {}

    def fake_run(self, command, **kwargs):
        called.update(kwargs)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(IsolateRunner, "run", fake_run)
    run_in_sandbox(["/bin/true"], cfg, network=True)
    assert called["network"] is True
