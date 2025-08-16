from pathlib import Path

import re
import subprocess

from runners.cpp_runner import (
    compile_cpp_sources,
    compile_shared_library,
    run_binary,
)


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

    success, out, err, binary = compile_cpp_sources([main, helper])
    assert success, f"compile failed: {out}\n{err}"
    assert binary is not None

    code, stdout, stderr = run_binary(binary)
    assert code == 0
    assert stdout.strip() == "3"


def test_shared_library_link(tmp_path: Path) -> None:
    """Build a shared library and link it into a main program."""
    lib_src = tmp_path / "double.cpp"
    lib_src.write_text(
        'extern "C" int times_two(int x){return 2*x;}\n'
    )

    lib_path = tmp_path / "libdouble.so"
    success, out, err, so = compile_shared_library([lib_src], output=lib_path)
    assert success, f"lib compile failed: {out}\n{err}"
    assert so is not None

    main = tmp_path / "main.cpp"
    main.write_text(
        """
#include <iostream>
extern "C" int times_two(int);
int main(){std::cout<<times_two(5);}
"""
    )

    success, out, err, binary = compile_cpp_sources(
        [main],
        library_dirs=[tmp_path],
        libraries=["double"],
        rpath=[tmp_path],
    )
    assert success, f"compile failed: {out}\n{err}"
    assert binary is not None

    code, stdout, stderr = run_binary(binary)
    assert code == 0
    assert stdout.strip() == "10"


def test_shared_library_env_link(tmp_path: Path) -> None:
    """Link a shared library and supply its path via ``LD_LIBRARY_PATH``."""
    lib_src = tmp_path / "double.cpp"
    lib_src.write_text(
        'extern "C" int times_two(int x){return 2*x;}\n'
    )

    lib_path = tmp_path / "libdouble.so"
    success, out, err, so = compile_shared_library([lib_src], output=lib_path)
    assert success, f"lib compile failed: {out}\n{err}"
    assert so is not None

    main = tmp_path / "main.cpp"
    main.write_text(
        """
#include <iostream>
extern "C" int times_two(int);
int main(){std::cout<<times_two(5);}
"""
    )

    success, out, err, binary = compile_cpp_sources(
        [main],
        library_dirs=[tmp_path],
        libraries=["double"],
    )
    assert success, f"compile failed: {out}\n{err}"
    assert binary is not None

    code, stdout, stderr = run_binary(
        binary, env={"LD_LIBRARY_PATH": str(tmp_path)}
    )
    assert code == 0
    assert stdout.strip() == "10"


def test_static_build(tmp_path: Path) -> None:
    """Request a static binary and verify it's not dynamically linked."""
    src = tmp_path / "main.cpp"
    src.write_text("int main(){return 0;}")

    success, out, err, binary = compile_cpp_sources(
        [src], static=True, sanitize=False
    )
    assert success, f"compile failed: {out}\n{err}"
    assert binary is not None

    ldd = subprocess.run(["ldd", str(binary)], capture_output=True, text=True)
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
