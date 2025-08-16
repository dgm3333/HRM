from __future__ import annotations

"""Utility functions for compiling C++ sources.

This module provides a thin wrapper around ``g++`` or ``clang++``
invocations. It captures diagnostics so that later phases can integrate
warning and error counts into reward shaping or reporting pipelines.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence
import shutil
import subprocess

# Default compile flags aimed at reasonably optimized yet deterministic
# builds. These can be extended by callers for sanitizers or additional
# warnings.
DEFAULT_FLAGS: List[str] = ["-std=c++17", "-O2", "-pipe"]


@dataclass
class CompileResult:
    """Result of a C++ compilation command."""

    cmd: List[str]
    returncode: int
    stdout: str
    stderr: str
    warnings: List[str]
    errors: List[str]

    @property
    def success(self) -> bool:
        """Whether the compilation finished without errors."""

        return self.returncode == 0


def compile_cpp(
    sources: Sequence[Path],
    output: Path,
    *,
    compiler: str = "g++",
    flags: Iterable[str] | None = None,
    include_dirs: Iterable[Path] | None = None,
    lib_dirs: Iterable[Path] | None = None,
    libs: Iterable[str] | None = None,
    rpaths: Iterable[Path] | None = None,
    static: bool = False,
    use_ccache: bool = False,
) -> CompileResult:
    """Compile C++ ``sources`` into ``output`` using ``compiler``.

    Parameters
    ----------
    sources:
        Sequence of C++ source file paths to compile.
    output:
        Path to the output binary.
    compiler:
        Which compiler executable to invoke. Defaults to ``g++``.
    flags:
        Additional flags to pass to the compiler. ``DEFAULT_FLAGS`` are
        prepended automatically.
    include_dirs:
        Optional include directories passed as ``-I``.
    lib_dirs:
        Optional library search paths passed as ``-L``.
    libs:
        Optional libraries to link against (``-l<name>``).
    rpaths:
        Runtime library search paths encoded via ``-Wl,-rpath``.
    static:
        If ``True``, add ``-static`` to request a fully static binary.
    use_ccache:
        If ``True`` and ``ccache`` is available, prefix the compile command
        with it to leverage caching.
    """

    src_args = [str(Path(s)) for s in sources]
    cmd: List[str] = []
    if use_ccache and shutil.which("ccache"):
        cmd.append("ccache")
    cmd.extend([compiler, *DEFAULT_FLAGS])
    if static:
        cmd.append("-static")
    if flags:
        cmd.extend(list(flags))
    if include_dirs:
        for d in include_dirs:
            cmd.extend(["-I", str(d)])
    if lib_dirs:
        for d in lib_dirs:
            cmd.extend(["-L", str(d)])
    cmd.extend(src_args)
    if libs:
        for lib in libs:
            cmd.append(f"-l{lib}")
    if rpaths:
        for rp in rpaths:
            cmd.append(f"-Wl,-rpath,{rp}")
    cmd.extend(["-o", str(output)])

    proc = subprocess.run(cmd, capture_output=True, text=True)

    stderr_lines = proc.stderr.splitlines()
    warnings = [line for line in stderr_lines if "warning:" in line]
    errors = [line for line in stderr_lines if "error:" in line]

    return CompileResult(
        cmd=cmd,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        warnings=warnings,
        errors=errors,
    )
