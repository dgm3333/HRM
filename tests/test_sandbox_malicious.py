import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from runners.cpp_runner import compile_cpp, run_binary
from runners.error_taxonomy import classify_runtime
from runners.isolate import IsolateRunner

pytestmark = pytest.mark.skipif(
    shutil.which("isolate") is None, reason="isolate not available"
)


def _compile(code: str, tmp_path: Path) -> Path:
    src = tmp_path / "prog.cpp"
    src.write_text(code)
    res = compile_cpp(src)
    assert res.success and res.binary is not None
    return res.binary


def _run(binary: Path):
    runner = IsolateRunner()
    return run_binary(binary, sandbox=runner)


def test_file_read_denied(tmp_path):
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
    binary = _compile(code, tmp_path)
    rc, _out, err = _run(binary)
    assert rc != 0
    assert classify_runtime(rc, err) == "policy_violation"


def test_socket_open_denied(tmp_path):
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
    binary = _compile(code, tmp_path)
    rc, _out, err = _run(binary)
    assert rc != 0
    assert classify_runtime(rc, err) == "policy_violation"


def test_fork_bomb_blocked(tmp_path):
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
    binary = _compile(code, tmp_path)
    rc, _out, err = _run(binary)
    assert rc != 0
    assert classify_runtime(rc, err) in {"policy_violation", "runtime_error"}


def test_excessive_forks_blocked(tmp_path):
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
    binary = _compile(code, tmp_path)
    rc, _out, err = _run(binary)
    assert rc != 0
    assert classify_runtime(rc, err) in {"policy_violation", "runtime_error"}

