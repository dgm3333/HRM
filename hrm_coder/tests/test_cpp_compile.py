from pathlib import Path
import subprocess

from hrm_coder.cpp_compile import (
    compile_cpp,
    compile_shared_library,
    compile_static_library,
)


def test_compile_success(tmp_path: Path) -> None:
    src = tmp_path / "main.cc"
    src.write_text("int main() { return 0; }\n")
    out = tmp_path / "a.out"
    result = compile_cpp([src], out)
    assert result.success
    assert result.errors == []
    assert result.warnings == []


def test_compile_failure(tmp_path: Path) -> None:
    src = tmp_path / "main.cc"
    src.write_text("int main() {\n")  # missing closing brace/semicolon
    out = tmp_path / "a.out"
    result = compile_cpp([src], out)
    assert not result.success
    assert result.errors  # expect at least one error line


def test_compile_with_warning(tmp_path: Path) -> None:
    src = tmp_path / "main.cc"
    src.write_text("int main() { int x = 0; return 0; }\n")
    out = tmp_path / "a.out"
    result = compile_cpp([src], out, flags=["-Wall"])
    assert result.success
    assert result.warnings  # unused variable x should trigger warning


def test_compile_with_include_and_lib(tmp_path: Path) -> None:
    inc = tmp_path / "inc"
    libdir = tmp_path / "lib"
    inc.mkdir()
    libdir.mkdir()

    # Create a simple library
    (inc / "foo.h").write_text("int foo();\n")
    lib_src = tmp_path / "foo.cc"
    lib_src.write_text("int foo() { return 0; }\n")
    obj = tmp_path / "foo.o"
    subprocess.run(["g++", "-c", str(lib_src), "-o", str(obj)], check=True)
    liba = libdir / "libfoo.a"
    subprocess.run(["ar", "rcs", str(liba), str(obj)], check=True)

    # Main program using the library
    main = tmp_path / "main.cc"
    main.write_text("#include \"foo.h\"\nint main(){return foo();}\n")
    out = tmp_path / "a.out"

    result = compile_cpp(
        [main],
        out,
        include_dirs=[inc],
        lib_dirs=[libdir],
        libs=["foo"],
        rpaths=[libdir],
    )

    assert result.success
    cmd_str = " ".join(result.cmd)
    assert "-I" in result.cmd and str(inc) in result.cmd
    assert "-L" in result.cmd and str(libdir) in result.cmd
    assert "-lfoo" in result.cmd
    assert f"-Wl,-rpath,{libdir}" in result.cmd


def test_shared_library_build_and_link(tmp_path: Path) -> None:
    """Build a shared library and link it into a main program."""
    lib_src = tmp_path / "double.cc"
    lib_src.write_text('extern "C" int times_two(int x){return 2*x;}\n')
    lib_out = tmp_path / "libdouble.so"
    lib_res = compile_shared_library([lib_src], lib_out)
    assert lib_res.success

    main = tmp_path / "main.cc"
    main.write_text(
        """
#include <iostream>
extern "C" int times_two(int);
int main(){std::cout<<times_two(5);}
"""
    )
    exe = tmp_path / "a.out"
    res = compile_cpp(
        [main],
        exe,
        lib_dirs=[tmp_path],
        libs=["double"],
        rpaths=[tmp_path],
    )
    assert res.success
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.stdout.strip() == "10"


def test_static_library_build_and_link(tmp_path: Path) -> None:
    """Build a static library and link it into a main program."""
    lib_src = tmp_path / "math.cc"
    lib_src.write_text("int add(int a,int b){return a+b;}\n")
    lib_out = tmp_path / "libmath.a"
    lib_res = compile_static_library([lib_src], lib_out)
    assert lib_res.success

    main = tmp_path / "main.cc"
    main.write_text(
        """
#include <iostream>
extern int add(int,int);
int main(){std::cout<<add(2,3);}
"""
    )
    exe = tmp_path / "a.out"
    res = compile_cpp([main], exe, lib_dirs=[tmp_path], libs=["math"])
    assert res.success
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.stdout.strip() == "5"
