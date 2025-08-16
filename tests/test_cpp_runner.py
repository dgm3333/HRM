from pathlib import Path

from runners.cpp_runner import compile_cpp_sources, run_binary


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
