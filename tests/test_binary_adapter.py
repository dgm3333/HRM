from pathlib import Path
import os
import subprocess
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)

from runners.binary_adapter import (  # noqa: E402
    BinarySandboxAdapter,
    SANITIZER_ENV,
)
from runners.cpp_runner import compile_cpp  # noqa: E402
from runners.gvisor import GVisorRunner  # noqa: E402
from runners.nsjail import NSJailRunner  # noqa: E402


def test_binary_adapter_injects_sanitizers(tmp_path: Path) -> None:
    src = tmp_path / "main.cpp"
    src.write_text("int main(){return 0;}")
    res = compile_cpp(src)
    assert res.success and res.binary is not None

    class CaptureEnvRunner:
        def __init__(self) -> None:
            self.env = None

        def run(self, cmd, **kwargs):
            self.env = kwargs.get("env")
            return subprocess.run(
                cmd,
                input=kwargs.get("stdin"),
                capture_output=True,
                text=True,
                check=False,
                cwd=kwargs.get("workdir"),
            )

    runner = CaptureEnvRunner()
    adapter = BinarySandboxAdapter(runner)
    code, _, _ = adapter.run(res.binary)
    assert code == 0
    assert runner.env is not None
    assert runner.env["ASAN_OPTIONS"] == SANITIZER_ENV["ASAN_OPTIONS"]
    assert runner.env["UBSAN_OPTIONS"] == SANITIZER_ENV["UBSAN_OPTIONS"]



def _compile_env_printer(tmp_path: Path):
    src = tmp_path / "main.cpp"
    src.write_text(
        """
        #include <cstdlib>
        #include <iostream>
        int main() {
            const char* asan = std::getenv("ASAN_OPTIONS");
            const char* ubsan = std::getenv("UBSAN_OPTIONS");
            if (asan) std::cout << asan;
            if (ubsan) std::cerr << ubsan;
            return 0;
        }
        """
    )
    res = compile_cpp(src)
    assert res.success and res.binary is not None
    return res.binary


def test_binary_adapter_nsjail(tmp_path: Path) -> None:
    binary = _compile_env_printer(tmp_path)

    fake = tmp_path / "nsjail"
    fake.write_text(
        """#!/usr/bin/env python3
import os, sys, subprocess
args = sys.argv[1:]
env = {}
i = 0
while i < len(args):
    a = args[i]
    if a == '--':
        cmd = args[i + 1:]
        break
    if a == '--env':
        key, val = args[i + 1].split('=', 1)
        env[key] = val
        i += 2
    elif a in ('--cwd', '--bindmount', '--bindmount_ro'):
        i += 2
    else:
        i += 1
res = subprocess.run(
    cmd, capture_output=True, text=True, env={**os.environ, **env}
)
sys.stdout.write(res.stdout)
sys.stderr.write(res.stderr)
sys.exit(res.returncode)
"""
    )
    fake.chmod(0o755)

    runner = NSJailRunner(nsjail_path=str(fake))
    adapter = BinarySandboxAdapter(runner)
    code, out, err = adapter.run(binary)
    assert code == 0
    assert SANITIZER_ENV["ASAN_OPTIONS"] in out
    assert SANITIZER_ENV["UBSAN_OPTIONS"] in err


def test_binary_adapter_gvisor(tmp_path: Path) -> None:
    binary = _compile_env_printer(tmp_path)

    fake = tmp_path / "docker"
    fake.write_text(
        """#!/usr/bin/env python3
import os, sys, subprocess
args = sys.argv[1:]
args = args[1:]
env = {}
i = 0
while i < len(args):
    a = args[i]
    if a == '-e':
        key, val = args[i + 1].split('=', 1)
        env[key] = val
        i += 2
    elif a in ('-w', '-v'):
        i += 2
    elif a.startswith('-'):
        i += 1
    else:
        cmd = args[i + 1:]
        break
res = subprocess.run(
    cmd, capture_output=True, text=True, env={**os.environ, **env}
)
sys.stdout.write(res.stdout)
sys.stderr.write(res.stderr)
sys.exit(res.returncode)
"""
    )
    fake.chmod(0o755)

    runner = GVisorRunner(docker_path=str(fake), image="ubuntu:latest")
    adapter = BinarySandboxAdapter(runner)
    code, out, err = adapter.run(binary)
    assert code == 0
    assert SANITIZER_ENV["ASAN_OPTIONS"] in out
    assert SANITIZER_ENV["UBSAN_OPTIONS"] in err


def test_binary_adapter_passes_limits(tmp_path: Path) -> None:
    src = tmp_path / "main.cpp"
    src.write_text("int main(){return 0;}")
    res = compile_cpp(src)
    assert res.success and res.binary is not None

    class CaptureRunner:
        def __init__(self) -> None:
            self.kwargs = None

        def run(self, cmd, **kwargs):
            self.kwargs = kwargs
            return subprocess.CompletedProcess(cmd, 0, "", "")

    runner = CaptureRunner()
    adapter = BinarySandboxAdapter(runner)
    adapter.run(res.binary, timeout=3, memory_limit=4096)
    assert runner.kwargs is not None
    assert runner.kwargs["time_limit"] == 3
    assert runner.kwargs["wall_time"] == 3
    assert runner.kwargs["memory"] == 4  # 4096 bytes -> 4 KB
    assert runner.kwargs["network"] is False
    assert runner.kwargs["processes"] == 1

