import runpy
import subprocess
import sys
from pathlib import Path

import pytest


def test_run_in_sandbox_script(monkeypatch, capsys):
    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "run_in_sandbox.py"
    )

    import hrm_coder.runner as runner_mod

    def fake_run(cmd, cfg):
        assert cfg.timeout == 7
        assert cmd == ["echo", "hi"]
        return subprocess.CompletedProcess(cmd, 0, "OUT", "")

    monkeypatch.setattr(runner_mod, "run_in_sandbox", fake_run)
    monkeypatch.setattr(
        sys, "argv", [str(script), "--timeout", "7", "--", "echo", "hi"]
    )

    with pytest.raises(SystemExit) as exc:
        runpy.run_path(script, run_name="__main__")
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert captured.out == "OUT"
