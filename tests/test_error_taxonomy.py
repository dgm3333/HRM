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
    success, _, err, _ = compile_cpp(src, sanitize=False)
    assert not success
    assert classify_compile(success, err) == "compile_error"

    src2 = tmp_path / "link.cpp"
    src2.write_text("extern int foo(); int main(){return foo();}")
    success2, out2, err2, _ = compile_cpp(src2, sanitize=False)
    assert not success2
    assert classify_compile(success2, err2) == "link_error"


def test_classify_runtime_conditions(tmp_path: Path) -> None:
    """Classify runtime error types including timeout and sanitizers."""
    # Runtime error due to non-zero exit code
    src = tmp_path / "runtime.cpp"
    src.write_text("int main(){return 1;}")
    success, _, err, binary = compile_cpp(src, sanitize=False)
    assert success and binary is not None
    code, out, err = run_binary(binary)
    assert classify_runtime(code, err) == "runtime_error"

    # Timeout
    src_t = tmp_path / "loop.cpp"
    src_t.write_text("int main(){while(true){} }")
    success_t, _, _, binary_t = compile_cpp(src_t, sanitize=False)
    assert success_t and binary_t is not None
    try:
        run_binary(binary_t, timeout=0.1)
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
    success_s, _, _, binary_s = compile_cpp(src_s)
    assert success_s and binary_s is not None
    code_s, _, err_s = run_binary(binary_s)
    assert classify_runtime(code_s, err_s) == "sanitizer_error"
