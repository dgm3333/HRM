from pathlib import Path
import subprocess

from hrm_coder.cpp_compile import compile_cpp


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
