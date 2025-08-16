import pathlib
import pytest

from runners.cpp_runner import compile_cpp_sources
from runners.io_judge import run_io_tests
from runners.sandbox_cache import SandboxCache


def test_run_io_tests_basic(tmp_path: pathlib.Path) -> None:
    src = tmp_path / "main.cpp"
    src.write_text(
        "#include <iostream>\n"
        "int main(){int a,b; if(!(std::cin>>a>>b)) return 0; "
        "std::cout<<a+b;}"
    )
    res = compile_cpp_sources([src])
    assert res.success and res.binary is not None

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "a.in").write_text("1 2\n")
    (tests_dir / "a.out").write_text("3   \n")

    results = run_io_tests(res.binary, tests_dir)
    assert results["results"][0]["passed"]


def test_run_io_tests_cache(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "main.cpp"
    src.write_text(
        "#include <iostream>\n"
        "int main(){int a,b; if(!(std::cin>>a>>b)) return 0; "
        "std::cout<<a+b;}"
    )
    res = compile_cpp_sources([src])
    assert res.success and res.binary is not None

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "a.in").write_text("1 2\n")
    (tests_dir / "a.out").write_text("3\n")

    cache = SandboxCache(tmp_path / "cache")

    calls = {"run": 0}
    original_run_binary = run_io_tests.__globals__["_run_binary"]

    def wrapped_run_binary(*args, **kwargs):
        calls["run"] += 1
        return original_run_binary(*args, **kwargs)

    monkeypatch.setitem(
        run_io_tests.__globals__, "_run_binary", wrapped_run_binary
    )

    first = run_io_tests(
        res.binary, tests_dir, cache=cache
    )
    second = run_io_tests(
        res.binary, tests_dir, cache=cache
    )
    assert first == second
    assert calls["run"] == 1
