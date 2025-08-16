"""Utilities for compiling and executing C++ code for Codeforces-style tasks.

This module provides a minimal wrapper around the system C++ compiler and
runtime execution.  It is intended as an early step toward the full Phase 10
C++ runner described in the project roadmap.  The functions here support
compilation with common optimization and sanitizer flags and running binaries
against multiple input/output pairs with basic resource limits.
"""
from __future__ import annotations

import resource
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


DEFAULT_FLAGS: List[str] = ["-std=c++17", "-O2", "-pipe"]
SANITIZER_FLAGS: List[str] = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]


def compile_cpp_sources(
    sources: Sequence[Path],
    output: Optional[Path] = None,
    *,
    compiler: str = "g++",
    flags: Optional[Iterable[str]] = None,
    sanitize: bool = True,
    static: bool = False,
    library_dirs: Optional[Iterable[Path]] = None,
    libraries: Optional[Iterable[str]] = None,
    rpath: Optional[Iterable[Path]] = None,
    use_ccache: bool = False,
) -> Tuple[bool, str, str, Optional[Path]]:
    """Compile one or more C++ ``sources`` into a single binary.

    This helper expands the simple single-file ``compile_cpp`` function to
    support the Phase 10 roadmap goals of linking multi-file projects and
    honoring optional dynamic linking settings.  A subset of features such as
    rpath handling and optional static builds are exposed for experimentation
    with more complex judges.

    Parameters
    ----------
    sources:
        Iterable of paths to C++ source files to be compiled and linked
        together.
    output:
        Optional path to the produced binary.  A temporary file is created
        when omitted.
    compiler:
        Which compiler to invoke, e.g. ``g++`` or ``clang++``.
    flags:
        Additional compiler flags.
    sanitize:
        Whether to include address and undefined behaviour sanitizers.
    static:
        Request a static build by passing ``-static`` when True.
    library_dirs:
        Extra directories to search for libraries during linking (``-L``).
    libraries:
        Additional libraries to link against (``-l``).
    rpath:
        Runtime search paths to embed into the binary via ``-Wl,-rpath``.
    use_ccache:
        Prepend ``ccache`` to the compile command when available to speed up
        iterative builds.
    """

    if flags is None:
        flags = list(DEFAULT_FLAGS)
    else:
        flags = list(flags)
    if sanitize:
        flags = list(flags) + SANITIZER_FLAGS
    if static:
        flags.append("-static")

    if output is None:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        output_path = Path(tmp.name)
        tmp.close()
    else:
        output_path = Path(output)

    cmd: List[str] = [compiler]
    if use_ccache and shutil.which("ccache") is not None:
        cmd = ["ccache", compiler]

    cmd += [str(s) for s in sources] + ["-o", str(output_path)] + list(flags)

    if library_dirs is not None:
        for d in library_dirs:
            cmd.extend(["-L", str(d)])
    if libraries is not None:
        for lib in libraries:
            cmd.extend(["-l", lib])
    if rpath is not None:
        for p in rpath:
            cmd.append(f"-Wl,-rpath,{p}")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    success = proc.returncode == 0
    return success, proc.stdout, proc.stderr, output_path if success else None


def compile_cpp(
    source: Path,
    output: Optional[Path] = None,
    *,
    compiler: str = "g++",
    flags: Optional[Iterable[str]] = None,
    sanitize: bool = True,
) -> Tuple[bool, str, str, Optional[Path]]:
    """Compile a single C++ ``source`` file.

    This is a thin wrapper around :func:`compile_cpp_sources` for backwards
    compatibility.  The implementation simply delegates to the more general
    multi-file helper with a one-element source list.
    """

    return compile_cpp_sources(
        [source],
        output,
        compiler=compiler,
        flags=flags,
        sanitize=sanitize,
    )


def _set_limits(memory_limit: Optional[int]) -> None:
    if memory_limit is not None:
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))


def run_binary(
    binary: Path,
    *,
    input_data: str = "",
    timeout: float = 2.0,
    memory_limit: Optional[int] = None,
) -> Tuple[int, str, str]:
    """Execute a compiled binary with optional resource limits."""

    def preexec() -> None:
        _set_limits(memory_limit)

    proc = subprocess.run(
        [str(binary)],
        input=input_data,
        capture_output=True,
        text=True,
        timeout=timeout,
        preexec_fn=preexec,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_codeforces_tests(
    source: Path,
    tests_dir: Path,
    *,
    compiler: str = "g++",
    flags: Optional[Iterable[str]] = None,
    sanitize: bool = True,
    timeout: float = 2.0,
    memory_limit: Optional[int] = None,
) -> dict:
    """Compile ``source`` and run it against all tests in ``tests_dir``.

    The directory is expected to contain pairs of ``*.in`` and ``*.out`` files.
    Results are returned as a mapping with compile diagnostics and a list of
    per-test outcomes.
    """

    success, out, err, binary = compile_cpp(
        source, compiler=compiler, flags=flags, sanitize=sanitize
    )
    results = []
    if not success or binary is None:
        return {"compile_stdout": out, "compile_stderr": err, "results": results}

    for input_file in sorted(Path(tests_dir).glob("*.in")):
        test_name = input_file.stem
        expected_file = input_file.with_suffix(".out")
        input_data = input_file.read_text()
        expected = expected_file.read_text() if expected_file.exists() else ""
        try:
            code, stdout, stderr = run_binary(
                binary,
                input_data=input_data,
                timeout=timeout,
                memory_limit=memory_limit,
            )
        except subprocess.TimeoutExpired:
            code, stdout, stderr = -1, "", "TIMEOUT"
        passed = stdout.strip() == expected.strip() and code == 0
        results.append(
            {
                "test": test_name,
                "passed": passed,
                "stdout": stdout,
                "stderr": stderr,
            }
        )

    return {"compile_stdout": out, "compile_stderr": err, "results": results}
