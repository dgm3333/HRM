import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from runners.gvisor import GVisorRunner  # noqa: E402
from runners.isolate import IsolateRunner  # noqa: E402
from runners.nsjail import NSJailRunner  # noqa: E402


def _available_runners() -> List[Tuple[str, object]]:
    runners: List[Tuple[str, object]] = []
    if shutil.which("isolate") is not None:
        runners.append(("isolate", IsolateRunner()))
    if shutil.which("nsjail") is not None:
        runners.append(("nsjail", NSJailRunner()))
    if shutil.which("docker") is not None:
        cmd = [
            "docker",
            "run",
            "--rm",
            "--runtime=runsc",
            "python:3.11-slim",
            "python",
            "-c",
            "print('hi')",
        ]
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode == 0:
            runners.append(("gvisor", GVisorRunner(image="python:3.11-slim")))
    return runners


@pytest.mark.parametrize("name, runner", _available_runners())
def test_time_limit_enforced(name: str, runner: object) -> None:
    if name == "gvisor":
        pytest.skip("gVisor does not expose a CPU time or wall clock limit")
    proc = runner.run(
        [sys.executable, "-c", "while True: pass"],
        time_limit=1,
        wall_time=1,
    )
    assert proc.returncode != 0


@pytest.mark.parametrize("name, runner", _available_runners())
def test_memory_limit_enforced(name: str, runner: object) -> None:
    cmd = [
        sys.executable,
        "-c",
        "a = 'x' * (200 * 1024 * 1024); print(len(a))",
    ]
    proc = runner.run(cmd, memory=32 * 1024)
    assert proc.returncode != 0
