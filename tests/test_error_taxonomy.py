from __future__ import annotations

import subprocess
from pathlib import Path

from runners.cpp_runner import compile_cpp, run_binary
from runners.error_taxonomy import classify_compile, classify_runtime


def test_classify_compile_errors(tmp_path: Path) -> None:
    """Detect compile-time and link-time failures."""
    src = tmp_path / "syntax.cpp"
    src.write_text(
        "#include <nonexistent_header.h>\n"
        "int main(){}"
    )
    res = compile_cpp(src, sanitize=False)
    assert not res.success
    assert classify_compile(res.success, res.stderr) == "compile_error"

    src2 = tmp_path / "link.cpp"
    src2.write_text("extern int foo(); int main(){return foo();}")
    res2 = compile_cpp(src2, sanitize=False)
    assert not res2.success
    assert classify_compile(res2.success, res2.stderr) == "link_error"


def test_classify_runtime_conditions(tmp_path: Path) -> None:
    """Classify runtime error types including timeout and sanitizers."""
    # Runtime error due to non-zero exit code
    src = tmp_path / "runtime.cpp"
    src.write_text("int main(){return 1;}")
    res = compile_cpp(src, sanitize=False)
    assert res.success and res.binary is not None
    code, out, err = run_binary(res.binary)
    assert classify_runtime(code, err) == "runtime_error"

    # Timeout
    src_t = tmp_path / "loop.cpp"
    src_t.write_text("int main(){while(true){} }")
    res_t = compile_cpp(src_t, sanitize=False)
    assert res_t.success and res_t.binary is not None
    try:
        run_binary(res_t.binary, timeout=0.1)
        timed_out = False
        code, _, err_t = 0, "", ""
    except subprocess.TimeoutExpired:
        timed_out = True
        code, err_t = -1, ""
    assert classify_runtime(code, err_t, timed_out=timed_out) == "timeout"

    # Sanitizer error
    src_s = tmp_path / "asan.cpp"
    src_s.write_text(
        "#include <iostream>\nint main(){int *p=new int[1];delete[] p;"
        "std::cout<<p[0];}"
    )
    res_s = compile_cpp(src_s)
    assert res_s.success and res_s.binary is not None
    code_s, _, err_s = run_binary(res_s.binary)
    assert classify_runtime(code_s, err_s) == "sanitizer_error"
