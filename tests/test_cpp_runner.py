from pathlib import Path
import re
import subprocess
import sys

import pytest  # noqa: F401

sys.path.append(str(Path(__file__).resolve().parents[1]))

import runners.cpp_runner as cpp_runner  # noqa: E402
from runners.cpp_runner import (  # noqa: E402
    compile_cpp_sources,
    compile_shared_library,
    compile_static_library,
    run_binary,
    run_codeforces_tests,
)
from runners.sandbox_cache import SandboxCache  # noqa: E402


def test_compile_multi_file(tmp_path: Path) -> None:
    """Compile and run a simple two-file C++ project."""
    main = tmp_path / "main.cpp"
    helper = tmp_path / "helper.cpp"

    main.write_text(
        """
#include <iostream>
extern int add(int a, int b);
int main() { std::cout << add(1, 2); }
"""
    )
    helper.write_text("int add(int a, int b) { return a + b; }\n")

    res = compile_cpp_sources([main, helper])
    assert res.success, f"compile failed: {res.stdout}\n{res.stderr}"
    assert res.binary is not None

    code, stdout, stderr = run_binary(res.binary)
    assert code == 0
    assert stdout.strip() == "3"


def test_shared_library_link(tmp_path: Path) -> None:
    """Build a shared library and link it into a main program."""
    lib_src = tmp_path / "double.cpp"
    lib_src.write_text(
        'extern "C" int times_two(int x){return 2*x;}\n'
    )

    lib_path = tmp_path / "libdouble.so"
    lib_res = compile_shared_library([lib_src], output=lib_path)
    assert lib_res.success, (
        f"lib compile failed: {lib_res.stdout}\n{lib_res.stderr}"
    )
    assert lib_res.binary is not None

    main = tmp_path / "main.cpp"
    main.write_text(
        """
#include <iostream>
extern "C" int times_two(int);
int main(){std::cout<<times_two(5);}
"""
    )

    main_res = compile_cpp_sources(
        [main],
        library_dirs=[tmp_path],
        libraries=["double"],
        rpath=[tmp_path],
    )
    assert main_res.success, (
        f"compile failed: {main_res.stdout}\n{main_res.stderr}"
    )
    assert main_res.binary is not None

    code, stdout, stderr = run_binary(main_res.binary)
    assert code == 0
    assert stdout.strip() == "10"


def test_shared_library_env_link(tmp_path: Path) -> None:
    """Link a shared library and supply its path via ``LD_LIBRARY_PATH``."""
    lib_src = tmp_path / "double.cpp"
    lib_src.write_text(
        'extern "C" int times_two(int x){return 2*x;}\n'
    )

    lib_path = tmp_path / "libdouble.so"
    lib_res = compile_shared_library([lib_src], output=lib_path)
    assert lib_res.success, (
        f"lib compile failed: {lib_res.stdout}\n{lib_res.stderr}"
    )
    assert lib_res.binary is not None

    main = tmp_path / "main.cpp"
    main.write_text(
        """
#include <iostream>
extern "C" int times_two(int);
int main(){std::cout<<times_two(5);}
"""
    )

    main_res = compile_cpp_sources(
        [main],
        library_dirs=[tmp_path],
        libraries=["double"],
    )
    assert main_res.success, (
        f"compile failed: {main_res.stdout}\n{main_res.stderr}"
    )
    assert main_res.binary is not None

    code, stdout, stderr = run_binary(
        main_res.binary, env={"LD_LIBRARY_PATH": str(tmp_path)}
    )
    assert code == 0
    assert stdout.strip() == "10"


def test_static_library_link(tmp_path: Path) -> None:
    """Build a static library and link it into a main program."""
    lib_src = tmp_path / "math.cpp"
    lib_src.write_text("int add(int a,int b){return a+b;}\n")

    lib_path = tmp_path / "libmath.a"
    lib_res = compile_static_library([lib_src], output=lib_path)
    assert lib_res.success, (
        f"lib compile failed: {lib_res.stdout}\n{lib_res.stderr}"
    )
    assert lib_res.binary is not None

    main = tmp_path / "main.cpp"
    main.write_text(
        """
#include <iostream>
extern int add(int, int);
int main(){std::cout<<add(2,3);}
"""
    )

    main_res = compile_cpp_sources(
        [main], library_dirs=[tmp_path], libraries=["math"]
    )
    assert main_res.success, (
        f"compile failed: {main_res.stdout}\n{main_res.stderr}"
    )
    assert main_res.binary is not None

    code, stdout, stderr = run_binary(main_res.binary)
    assert code == 0
    assert stdout.strip() == "5"


def test_static_build(tmp_path: Path) -> None:
    """Request a static binary and verify it's not dynamically linked."""
    src = tmp_path / "main.cpp"
    src.write_text("int main(){return 0;}")

    res = compile_cpp_sources([src], static=True, sanitize=False)
    assert res.success, f"compile failed: {res.stdout}\n{res.stderr}"
    assert res.binary is not None

    ldd = subprocess.run(
        ["ldd", str(res.binary)], capture_output=True, text=True
    )
    assert "not a dynamic executable" in (ldd.stdout + ldd.stderr)


def test_ccache_hit(tmp_path: Path) -> None:
    """Ensure that invoking ``use_ccache`` results in cache hits."""
    src = tmp_path / "foo.cpp"
    src.write_text("int add(int a,int b){return a+b;}")
    obj = tmp_path / "foo.o"

    subprocess.run(["ccache", "-z"], check=True)
    compile_cpp_sources([src], output=obj, flags=["-c"], use_ccache=True)
    compile_cpp_sources([src], output=obj, flags=["-c"], use_ccache=True)
    stats = subprocess.run(
        ["ccache", "-s", "-v"], capture_output=True, text=True
    )
    m = re.search(r"Hits:\s+(\d+)", stats.stdout)
    assert m and int(m.group(1)) >= 1


def test_warning_count(tmp_path: Path) -> None:
    """Compile code with a warning and ensure it is reported."""
    src = tmp_path / "warn.cpp"
    src.write_text("int main(){int x; return 0;}")
    res = compile_cpp_sources([
        src
    ], flags=["-std=c++17", "-Wall"], sanitize=False)
    assert res.success
    assert res.warnings >= 1


def test_run_binary_passes_env_to_sandbox(tmp_path: Path) -> None:
    lib_src = tmp_path / "double.cpp"
    lib_src.write_text('extern "C" int times_two(int x){return 2*x;}\n')
    lib_path = tmp_path / "libdouble.so"
    lib_res = compile_shared_library([lib_src], output=lib_path)
    assert lib_res.success

    main = tmp_path / "main.cpp"
    main.write_text(
        """
#include <iostream>
extern "C" int times_two(int);
int main(){std::cout<<times_two(7);}
"""
    )
    main_res = compile_cpp_sources(
        [main], library_dirs=[tmp_path], libraries=["double"]
    )
    assert main_res.success and main_res.binary is not None

    class EnvRunner:
        def __init__(self) -> None:
            self.env = None

        def run(self, cmd, **kwargs):
            self.env = kwargs.get("env")
            return subprocess.run(
                cmd,
                input=kwargs.get("stdin"),
                capture_output=True,
                text=True,
                check=False,
                env=self.env,
            )

    runner = EnvRunner()
    code, stdout, stderr = run_binary(
        main_res.binary,
        env={"LD_LIBRARY_PATH": str(tmp_path)},
        sandbox=runner,
    )
    assert code == 0
    assert stdout.strip() == "14"
    assert runner.env == {"LD_LIBRARY_PATH": str(tmp_path)}


class SpyRunner:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, cmd, **kwargs):
        self.calls += 1
        return subprocess.run(
            cmd,
            input=kwargs.get("stdin"),
            capture_output=True,
            text=True,
            check=False,
        )


def test_run_codeforces_tests_cache(tmp_path: Path, monkeypatch):
    src = tmp_path / "main.cpp"
    src.write_text(
        "#include <iostream>\nint main(){int a,b; if(!(std::cin>>a>>b)) return 0; std::cout<<a+b;}"  # noqa: E501
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "a.in").write_text("1 2\n")
    (tests_dir / "a.out").write_text("3\n")

    cache = SandboxCache(tmp_path / "cache")
    spy = SpyRunner()

    calls = {"compile": 0}

    original_compile = cpp_runner.compile_cpp_sources

    def wrapped_compile(*args, **kwargs):
        calls["compile"] += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(cpp_runner, "compile_cpp_sources", wrapped_compile)

    first = run_codeforces_tests([src], tests_dir, sandbox=spy, cache=cache)
    assert calls["compile"] == 1
    second = run_codeforces_tests([src], tests_dir, sandbox=spy, cache=cache)
    assert calls["compile"] == 1
    assert spy.calls == 1
    assert first == second


def test_run_codeforces_tests_coverage(tmp_path: Path) -> None:
    """Ensure coverage metrics are returned when requested."""
    src = tmp_path / "main.cpp"
    src.write_text(
        """
#include <iostream>
int main(){int x; if(!(std::cin>>x)) return 0;
if(x>0) std::cout<<1; else std::cout<<0;}
"""  # noqa: E501
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "a.in").write_text("1\n")
    (tests_dir / "a.out").write_text("1\n")

    res = run_codeforces_tests([src], tests_dir, collect_coverage=True)
    assert "coverage" in res
    assert 0.0 <= res["coverage"] <= 1.0
    assert res["coverage"] < 1.0
