import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from runners.codeforces_harness import IOPair, run_io_harness  # noqa: E402


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


def test_time_limit_enforced(tmp_path: pathlib.Path) -> None:
    src = _write_program(tmp_path / "loop.cpp", "int main(){while(true){};}\n")
    tests = [IOPair("", "")]
    result = run_io_harness([src], tests, time_limit_ms=50, sanitize=False)
    assert result["results"][0]["error_type"] == "timeout"


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
