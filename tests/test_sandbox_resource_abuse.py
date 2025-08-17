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


def _run(binary: Path, *, timeout: float = 1.0):
    runner = IsolateRunner()
    return run_binary(binary, sandbox=runner, timeout=timeout)


def test_memory_limit_enforced(tmp_path: Path) -> None:
    code = r"""
#include <vector>
#include <cstddef>
int main() {
    std::vector<int> v;
    try {
        v.resize((size_t)1 << 29); // ~512MB
    } catch (...) {
        return 1;
    }
    for (size_t i = 0; i < v.size(); ++i) v[i] = 0;
    return 0;
}
"""
    binary = _compile(code, tmp_path)
    rc, _out, err = _run(binary)
    assert rc != 0
    assert classify_runtime(rc, err) in {"runtime_error", "policy_violation"}


def test_cpu_time_limit_enforced(tmp_path: Path) -> None:
    code = r"""
int main() {
    while (1) {}
    return 0;
}
"""
    binary = _compile(code, tmp_path)
    rc, _out, err = _run(binary, timeout=1)
    assert rc != 0
    assert classify_runtime(rc, err) in {"runtime_error", "policy_violation"}


def test_ptrace_denied(tmp_path: Path) -> None:
    code = r"""
#include <sys/ptrace.h>
int main() {
    return ptrace(PTRACE_TRACEME, 0, nullptr, nullptr);
}
"""
    binary = _compile(code, tmp_path)
    rc, _out, err = _run(binary)
    assert rc != 0
    assert classify_runtime(rc, err) == "policy_violation"
