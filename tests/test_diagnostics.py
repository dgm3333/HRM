import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from utils.diagnostics import (
    clang_tidy_score,
    cppcheck_score,
    coverage_delta,
    compiler_diagnostics,
    diagnostics_score,
    parse_compiler_diagnostics,
)


def test_clang_tidy_score():
    output = "foo.cpp:1:1: warning: something [misc]"
    assert clang_tidy_score(output) == 0.9
    assert clang_tidy_score("") == 1.0


def test_cppcheck_score():
    output = "[warning] variable unused\n[error] something bad"
    assert cppcheck_score(output) == 0.8


def test_coverage_delta():
    assert coverage_delta(0.2, 0.5) == 0.3
    assert coverage_delta(0.6, 0.2) == 0.0


def test_compiler_diagnostics():
    stdout = "main.cpp:1:1: warning: stuff\n"
    stderr = "main.cpp:2:2: error: oops\n"
    warnings, errors = compiler_diagnostics(stdout, stderr)
    assert warnings == 1
    assert errors == 1


def test_parse_compiler_diagnostics():
    stdout = ""
    stderr = "main.cpp:3:4: warning: foo\nmain.cpp:5:6: error: bar\n"
    diags = parse_compiler_diagnostics(stdout, stderr)
    levels = {d.level for d in diags}
    assert "warning" in levels and "error" in levels
    assert diags[0].file == "main.cpp"


def test_diagnostics_score():
    assert diagnostics_score(0, 0) == 1.0
    assert diagnostics_score(2, 1) == 0.7
