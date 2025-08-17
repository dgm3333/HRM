import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from runners.cpp_runner import compile_cpp_sources  # noqa: E402
from runners.error_taxonomy import classify_runtime  # noqa: E402
from runners.gvisor import GVisorRunner  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("docker") is None or shutil.which("runsc") is None,
    reason="docker or runsc not available",
)


def _compile(code: str, tmp_path: Path) -> Path:
    src = tmp_path / "prog.cpp"
    src.write_text(code)
    res = compile_cpp_sources([src], sanitize=False, static=True)
    assert res.success and res.binary is not None
    return res.binary


def _run(binary: Path):
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")
    cmd = runner.build_command(
        [str(binary)],
        memory=64 * 1024,
        processes=2,
        network=False,
        readonly_dirs=[str(binary.parent)],
    )
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired as exc:
        return -1, exc.stdout or "", (exc.stderr or "") + "timeout"
    return proc.returncode, proc.stdout, proc.stderr


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
