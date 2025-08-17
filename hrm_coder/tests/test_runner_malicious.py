import shutil
from pathlib import Path

import pytest

from runners.cpp_runner import compile_cpp
from runners.error_taxonomy import classify_runtime
from hrm_coder.config import RunnerConfig
from hrm_coder.runner import run_in_sandbox

# Determine which sandboxes are available for testing.
available_sandboxes = []
if shutil.which("isolate"):
    available_sandboxes.append("isolate")
if shutil.which("nsjail"):
    available_sandboxes.append("nsjail")

if not available_sandboxes:
    pytest.skip("isolate and nsjail not available", allow_module_level=True)


def _compile(code: str, tmp_path: Path, sandbox: str) -> Path:
    src = tmp_path / "prog.cpp"
    src.write_text(code)
    res = compile_cpp(src)
    assert res.success and res.binary is not None
    return res.binary


def _run(binary: Path, sandbox: str):
    cfg = RunnerConfig(
        sandbox=sandbox,
        timeout=5,
        memory_limit=64,
        cpus=2,
        network=False,
    )
    proc = run_in_sandbox([str(binary)], cfg)
    return proc.returncode, proc.stdout, proc.stderr


@pytest.mark.parametrize("sandbox", available_sandboxes)
def test_file_read_denied(tmp_path: Path, sandbox: str) -> None:
    code = r"""
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main() {
    int fd = open("/proc/self/mem", O_RDONLY);
    if (fd == -1) {
        perror("open");
        return 1;
    }
    close(fd);
    return 0;
}
"""
    binary = _compile(code, tmp_path, sandbox)
    rc, _out, err = _run(binary, sandbox)
    assert rc != 0
    assert classify_runtime(rc, err) == "policy_violation"


@pytest.mark.parametrize("sandbox", available_sandboxes)
def test_socket_open_denied(tmp_path: Path, sandbox: str) -> None:
    code = r"""
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

int main() {
    int s = socket(AF_INET, SOCK_STREAM, 0);
    if (s == -1) {
        perror("socket");
        return 1;
    }
    close(s);
    return 0;
}
"""
    binary = _compile(code, tmp_path, sandbox)
    rc, _out, err = _run(binary, sandbox)
    assert rc != 0
    assert classify_runtime(rc, err) == "policy_violation"


@pytest.mark.parametrize("sandbox", available_sandboxes)
def test_fork_bomb_blocked(tmp_path: Path, sandbox: str) -> None:
    code = r"""
#include <unistd.h>

int main() {
    while (1) {
        if (fork() == 0) {
            // child sleeps to keep process alive
            sleep(10);
        }
    }
    return 0;
}
"""
    binary = _compile(code, tmp_path, sandbox)
    rc, _out, err = _run(binary, sandbox)
    assert rc != 0
    assert classify_runtime(rc, err) in {"policy_violation", "runtime_error"}


@pytest.mark.parametrize("sandbox", available_sandboxes)
def test_excessive_forks_blocked(tmp_path: Path, sandbox: str) -> None:
    code = r"""
#include <unistd.h>

int main() {
    for (int i = 0; i < 5; ++i) {
        if (fork() == 0) {
            sleep(10);
        }
    }
    return 0;
}
"""
    binary = _compile(code, tmp_path, sandbox)
    rc, _out, err = _run(binary, sandbox)
    assert rc != 0
    assert classify_runtime(rc, err) in {"policy_violation", "runtime_error"}
