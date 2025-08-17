import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from runners.codeforces_harness import (  # noqa: E402
    IOPair,
    run_io_harness,
    summarize_result,
)


def _write_program(path: pathlib.Path, code: str) -> pathlib.Path:
    path.write_text(code)
    return path


def test_multiple_tests(tmp_path: pathlib.Path) -> None:
    src = _write_program(
        tmp_path / "main.cpp",
        (
            "#include <iostream>\n"
            "int main(){int a,b; if(!(std::cin>>a>>b)) return 0; "
            "std::cout<<a+b;}\n"
        ),
    )
    tests = [
        IOPair("1 2\n", "3\n"),
        IOPair("10 30\n", "40\n"),
    ]
    result = run_io_harness([src], tests, sanitize=False)
    assert [r["passed"] for r in result["results"]] == [True, True]
    summary = summarize_result(result)
    assert summary["verdict"] == "OK"


def test_wrong_answer(tmp_path: pathlib.Path) -> None:
    src = _write_program(
        tmp_path / "wa.cpp",
        (
            "#include <iostream>\n"
            "int main(){int a,b; if(!(std::cin>>a>>b)) return 0; "
            "std::cout<<a+b-1;}\n"
        ),
    )
    tests = [IOPair("1 2\n", "3\n")]
    result = run_io_harness([src], tests, sanitize=False)
    summary = summarize_result(result)
    assert summary["verdict"] == "WA"


def test_time_limit_enforced(tmp_path: pathlib.Path) -> None:
    src = _write_program(tmp_path / "loop.cpp", "int main(){while(true){};}\n")
    tests = [IOPair("", "")]
    result = run_io_harness([src], tests, time_limit_ms=50, sanitize=False)
    assert result["results"][0]["error_type"] == "timeout"
    summary = summarize_result(result)
    assert summary["verdict"] == "TL"


def test_memory_limit_enforced(tmp_path: pathlib.Path) -> None:
    src = _write_program(
        tmp_path / "mem.cpp",
        (
            "#include <vector>\n"
            "int main(){std::vector<int> v(1<<26); return v.size();}\n"
        ),
    )
    tests = [IOPair("", "")]
    result = run_io_harness([src], tests, memory_limit_kb=1024, sanitize=False)
    assert not result["results"][0]["passed"]
    summary = summarize_result(result)
    assert summary["verdict"] in {"ML", "RE"}


def test_compile_error(tmp_path: pathlib.Path) -> None:
    src = _write_program(tmp_path / "bad.cpp", "int main() {\n")
    tests = [IOPair("", "")]
    result = run_io_harness([src], tests, sanitize=False)
    summary = summarize_result(result)
    assert summary["verdict"] == "CE"
