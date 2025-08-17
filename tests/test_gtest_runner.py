from pathlib import Path
import sys
import subprocess
import shutil

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

import runners.gtest_runner as gtest_runner  # noqa: E402
from runners.gtest_runner import (  # noqa: E402
    compile_and_run_gtests,
    run_gtests,
)
from runners.sandbox_cache import SandboxCache  # noqa: E402

if shutil.which("g++") is None or not Path(
    "/usr/include/gtest/gtest.h"
).exists():
    pytest.skip("gtest headers not available", allow_module_level=True)


def build_sample_test(
    tmpdir: Path, *, coverage: bool = False
) -> tuple[Path, Path]:
    code = (
        "#include <gtest/gtest.h>\n"
        "TEST(Sample, Adds){EXPECT_EQ(2+2,4);}\n"
        "int main(int argc,char**argv){::testing::InitGoogleTest(&argc, "
        "argv);return RUN_ALL_TESTS();}\n"
    )
    src = tmpdir / "sample_test.cpp"
    src.write_text(code)
    binary = tmpdir / "sample_test"
    cmd = [
        "g++",
        str(src),
        "-lgtest",
        "-lgtest_main",
        "-pthread",
        "-o",
        str(binary),
    ]
    if coverage:
        cmd.insert(1, "--coverage")
    subprocess.check_call(cmd)
    return binary, src


def test_run_gtests(tmp_path):
    binary, _ = build_sample_test(tmp_path)
    result = run_gtests(binary)
    assert result["tests"] == 1
    assert result["failures"] == 0
    assert result["cases"][0]["name"] == "Adds"
    assert result["cases"][0]["passed"]


def test_run_gtests_sandbox(tmp_path):
    binary, _ = build_sample_test(tmp_path)
    runner = SpyRunner()
    run_gtests(binary, sandbox=runner)
    assert runner.kwargs is not None
    assert runner.kwargs["readonly_dirs"] == [str(binary.parent)]
    assert runner.kwargs["workdir"] is not None


class SpyRunner:
    def __init__(self) -> None:
        self.calls = 0
        self.kwargs = None

    def run(self, cmd, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=kwargs.get("workdir"),
        )


def test_run_gtests_cache(tmp_path):
    binary, _ = build_sample_test(tmp_path)
    cache = SandboxCache(tmp_path / "cache")
    spy = SpyRunner()
    first = run_gtests(binary, sandbox=spy, cache=cache)
    assert spy.calls == 1
    second = run_gtests(binary, sandbox=spy, cache=cache)
    assert spy.calls == 1
    assert first == second


def test_run_gtests_coverage(tmp_path):
    binary, src = build_sample_test(tmp_path, coverage=True)
    result = run_gtests(binary, collect_coverage=True, sources=[src])
    assert "coverage" in result
    assert 0.0 <= result["coverage"] <= 1.0


def test_compile_and_run_gtests(tmp_path):
    src = tmp_path / "sample.cpp"
    src.write_text(
        "#include <gtest/gtest.h>\n"
        "int add(int a,int b){return a+b;}\n"
        "TEST(Sample, Adds){EXPECT_EQ(add(2,2),4);}\n"
        "int main(int argc,char** argv){::testing::InitGoogleTest(&argc,argv);"
        "return RUN_ALL_TESTS();}\n"
    )
    result = compile_and_run_gtests([src])
    assert result["compile_status"] == "success"
    assert result["tests"] == 1
    assert result["failures"] == 0
    assert result["cases"][0]["name"] == "Adds"
    assert result["cases"][0]["passed"]


def test_compile_and_run_gtests_cache(tmp_path, monkeypatch):
    src = tmp_path / "sample.cpp"
    src.write_text(
        "#include <gtest/gtest.h>\n"
        "TEST(Sample, Foo){EXPECT_EQ(1,1);}\n"
        "int main(int argc,char** argv){::testing::InitGoogleTest(&argc,argv);"
        "return RUN_ALL_TESTS();}\n"
    )
    cache = SandboxCache(tmp_path / "cache_compile")
    calls = {"compile": 0}
    original_compile = gtest_runner.compile_cpp_sources

    def wrapped_compile(*args, **kwargs):
        calls["compile"] += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(gtest_runner, "compile_cpp_sources", wrapped_compile)
    spy = SpyRunner()
    first = compile_and_run_gtests([src], sandbox=spy, cache=cache)
    assert calls["compile"] == 1
    second = compile_and_run_gtests([src], sandbox=spy, cache=cache)
    assert calls["compile"] == 1
    assert spy.calls == 1
    assert first == second
