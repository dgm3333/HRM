from pathlib import Path

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
