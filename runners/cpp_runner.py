"""Utilities for compiling and executing C++ code for Codeforces-style tasks.

This module provides a minimal wrapper around the system C++ compiler and
runtime execution.  It is intended as an early step toward the full Phase 10
C++ runner described in the project roadmap.  The functions here support
compilation with common optimization and sanitizer flags and running binaries
against multiple input/output pairs with basic resource limits.  It also
includes basic compiler diagnostics parsing to report warning and error
counts, advancing the Phase 10 goal of richer feedback from the build step.
"""
from __future__ import annotations

import os
import json
import resource
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

from .error_taxonomy import classify_compile
from .io_judge import run_io_tests
from .isolate import IsolateRunner
from .sandbox_cache import SandboxCache
from .binary_adapter import BinarySandboxAdapter, SANITIZER_ENV
from utils.diagnostics import compiler_diagnostics


DEFAULT_FLAGS: List[str] = ["-std=c++17", "-O2", "-pipe"]
SANITIZER_FLAGS: List[str] = [
    "-fsanitize=address,undefined",
    "-fno-omit-frame-pointer",
]


@dataclass
class CompileResult:
    """Result of a compilation step."""

    success: bool
    stdout: str
    stderr: str
    binary: Optional[Path]
    warnings: int
    errors: int


def compile_cpp_sources(
    sources: Sequence[Path],
    output: Optional[Path] = None,
    *,
    compiler: str = "g++",
    flags: Optional[Iterable[str]] = None,
    include_dirs: Optional[Iterable[Path]] = None,
    sanitize: bool = True,
    static: bool = False,
    library_dirs: Optional[Iterable[Path]] = None,
    libraries: Optional[Iterable[str]] = None,
    rpath: Optional[Iterable[Path]] = None,
    use_ccache: bool = False,
) -> CompileResult:
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
    include_dirs:
        Extra directories to search for headers during compilation (``-I``).
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

    if include_dirs is not None:
        for d in include_dirs:
            cmd.extend(["-I", str(d)])
    if library_dirs is not None:
        for d in library_dirs:
            cmd.extend(["-L", str(d)])
    if libraries is not None:
        for lib in libraries:
            cmd.extend(["-l", lib])
    if rpath is not None:
        for p in rpath:
            cmd.append(f"-Wl,-rpath,{p}")

    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    success = proc.returncode == 0
    warnings, errors = compiler_diagnostics(proc.stdout, proc.stderr)
    return CompileResult(
        success,
        proc.stdout,
        proc.stderr,
        output_path if success else None,
        warnings,
        errors,
    )


def compile_shared_library(
    sources: Sequence[Path],
    output: Optional[Path] = None,
    *,
    compiler: str = "g++",
    flags: Optional[Iterable[str]] = None,
    include_dirs: Optional[Iterable[Path]] = None,
    library_dirs: Optional[Iterable[Path]] = None,
    libraries: Optional[Iterable[str]] = None,
    rpath: Optional[Iterable[Path]] = None,
    sanitize: bool = True,
    use_ccache: bool = False,
) -> CompileResult:
    """Compile ``sources`` into a shared library.

    This helper produces a ``.so`` suitable for linking against binaries
    compiled with :func:`compile_cpp_sources`.  It mirrors that function's
    support for optional sanitizers, include and library directories, rpath
    entries, and ``ccache`` to encourage deterministic yet repeatable builds.
    """

    if flags is None:
        flags = list(DEFAULT_FLAGS)
    else:
        flags = list(flags)
    if sanitize:
        flags = list(flags) + SANITIZER_FLAGS

    flags = ["-shared", "-fPIC"] + list(flags)

    if output is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".so", delete=False)
        output_path = Path(tmp.name)
        tmp.close()
    else:
        output_path = Path(output)

    cmd: List[str] = [compiler]
    if use_ccache and shutil.which("ccache") is not None:
        cmd = ["ccache", compiler]

    cmd += [str(s) for s in sources] + ["-o", str(output_path)] + list(flags)

    if include_dirs is not None:
        for d in include_dirs:
            cmd.extend(["-I", str(d)])
    if library_dirs is not None:
        for d in library_dirs:
            cmd.extend(["-L", str(d)])
    if libraries is not None:
        for lib in libraries:
            cmd.extend(["-l", lib])
    if rpath is not None:
        for p in rpath:
            cmd.append(f"-Wl,-rpath,{p}")
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    success = proc.returncode == 0
    warnings, errors = compiler_diagnostics(proc.stdout, proc.stderr)
    return CompileResult(
        success,
        proc.stdout,
        proc.stderr,
        output_path if success else None,
        warnings,
        errors,
    )


def compile_static_library(
    sources: Sequence[Path],
    output: Optional[Path] = None,
    *,
    compiler: str = "g++",
    flags: Optional[Iterable[str]] = None,
    include_dirs: Optional[Iterable[Path]] = None,
    sanitize: bool = True,
    use_ccache: bool = False,
) -> CompileResult:
    """Compile ``sources`` into a static ``.a`` library.

    This helper builds each source into an object file and archives them
    together using ``ar``.  It mirrors :func:`compile_shared_library` so that
    Phase 10 experiments can easily link against lightweight library stubs
    without relying on dynamic libraries. ``include_dirs`` allows headers to be
    referenced from external locations during compilation.
    """

    if flags is None:
        flags = list(DEFAULT_FLAGS)
    else:
        flags = list(flags)
    if sanitize:
        flags = list(flags) + SANITIZER_FLAGS

    if output is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".a", delete=False)
        output_path = Path(tmp.name)
        tmp.close()
    else:
        output_path = Path(output)

    objs: List[Path] = []
    stdout_parts: List[str] = []
    stderr_parts: List[str] = []
    total_warnings = 0
    total_errors = 0
    for src in sources:
        obj_tmp = tempfile.NamedTemporaryFile(suffix=".o", delete=False)
        obj_path = Path(obj_tmp.name)
        obj_tmp.close()
        cmd: List[str] = [compiler]
        if use_ccache and shutil.which("ccache") is not None:
            cmd = ["ccache", compiler]
        cmd += [str(src), "-c", "-o", str(obj_path)] + list(flags)
        if include_dirs is not None:
            for d in include_dirs:
                cmd.extend(["-I", str(d)])
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout_parts.append(proc.stdout)
        stderr_parts.append(proc.stderr)
        w, e = compiler_diagnostics(proc.stdout, proc.stderr)
        total_warnings += w
        total_errors += e
        if proc.returncode != 0:
            return CompileResult(
                False,
                "".join(stdout_parts),
                "".join(stderr_parts),
                None,
                total_warnings,
                total_errors,
            )
        objs.append(obj_path)

    ar_cmd = ["ar", "rcs", str(output_path)] + [str(o) for o in objs]
    ar_proc = subprocess.run(
        ar_cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout_parts.append(ar_proc.stdout)
    stderr_parts.append(ar_proc.stderr)
    success = ar_proc.returncode == 0
    return CompileResult(
        success,
        "".join(stdout_parts),
        "".join(stderr_parts),
        output_path if success else None,
        total_warnings,
        total_errors,
    )


def compile_cpp(
    source: Path,
    output: Optional[Path] = None,
    *,
    compiler: str = "g++",
    flags: Optional[Iterable[str]] = None,
    include_dirs: Optional[Iterable[Path]] = None,
    sanitize: bool = True,
) -> CompileResult:
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
        include_dirs=include_dirs,
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
    env: Optional[Mapping[str, str]] = None,
    sanitize_env: bool = True,
    sandbox: Optional[IsolateRunner] = None,
    cwd: Optional[Path] = None,
    stdout_limit: Optional[int] = None,
    stderr_limit: Optional[int] = None,
) -> Tuple[int, str, str]:
    """Execute a compiled ``binary`` with optional limits and environment.

    When ``sandbox`` is provided the binary is executed inside that sandbox
    runner.  Otherwise :func:`subprocess.run` is used directly with a simple
    address-space limit.

    Parameters
    ----------
    binary:
        Path to the executable to run.
    input_data:
        Data fed to ``stdin`` of the process.
    timeout:
        Maximum wall-clock time in seconds before termination.
    memory_limit:
        Optional address-space limit in bytes.  When a sandbox is supplied the
        value is converted to kilobytes for the adapter.
    env:
        Extra environment variables to inject. When a sandbox is provided
        the variables are forwarded to it, otherwise they are passed to
        :func:`subprocess.run` directly.
    sanitize_env:
        When ``True`` injects default ``ASAN_OPTIONS`` and ``UBSAN_OPTIONS``
        values via :data:`SANITIZER_ENV`.  Callers may set this to ``False``
        to disable injection or override variables via ``env``.
    sandbox:
        Optional :class:`~runners.isolate.IsolateRunner` used to enforce
        resource limits and disable networking.
    cwd:
        Working directory for execution. Defaults to the directory of
        ``binary`` so that coverage artifacts are written alongside the
        executable.
    stdout_limit, stderr_limit:
        Optional maximum sizes for captured stdout and stderr.  When a
        sandbox runner is used the limits are forwarded to it.  Otherwise the
        captured output is truncated locally.
    """

    if cwd is None:
        cwd = binary.parent

    if sandbox is not None:
        adapter = BinarySandboxAdapter(sandbox)
        return adapter.run(
            binary,
            input_data=input_data,
            timeout=timeout,
            memory_limit=memory_limit,
            env=env,
            sanitize_env=sanitize_env,
            cwd=cwd,
            stdout_limit=stdout_limit,
            stderr_limit=stderr_limit,
        )

    if sanitize_env:
        env_combined: Optional[Mapping[str, str]] = {
            **SANITIZER_ENV,
            **(env or {}),
        }
    else:
        env_combined = dict(env) if env is not None else None

    def preexec() -> None:
        _set_limits(memory_limit)

    proc = subprocess.run(
        [str(binary)],
        input=input_data,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        preexec_fn=preexec,
        env=(
            {**os.environ, **env_combined}
            if env_combined is not None
            else None
        ),
        cwd=str(cwd),
    )
    stdout = proc.stdout
    stderr = proc.stderr
    if stdout_limit is not None:
        stdout = stdout[:stdout_limit]
    if stderr_limit is not None:
        stderr = stderr[:stderr_limit]
    return proc.returncode, stdout, stderr


def _parse_gcov_file(path: Path) -> float:
    """Return line coverage ratio from a ``gcov`` report file."""
    executed = 0
    total = 0
    for line in path.read_text().splitlines():
        parts = line.split(":", 2)
        if len(parts) < 2:
            continue
        count = parts[0].strip()
        if count in ("-", "====="):
            continue
        if count == "#####":
            total += 1
            continue
        try:
            num = int(count)
        except ValueError:
            continue
        total += 1
        if num > 0:
            executed += 1
    return executed / total if total else 0.0


def _collect_coverage(sources: Sequence[Path], workdir: Path) -> float:
    """Run ``gcov`` on ``sources`` in ``workdir`` and average coverage."""
    if shutil.which("gcov") is None:
        return 0.0
    covs: List[float] = []
    for src in sources:
        subprocess.run(
            ["gcov", str(src), "-o", str(workdir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(workdir),
            check=False,
        )
        gcov_file = workdir / f"{src.name}.gcov"
        if gcov_file.exists():
            covs.append(_parse_gcov_file(gcov_file))
    return sum(covs) / len(covs) if covs else 0.0


def run_codeforces_tests(
    sources: Sequence[Path],
    tests_dir: Path,
    *,
    compiler: str = "g++",
    flags: Optional[Iterable[str]] = None,
    include_dirs: Optional[Iterable[Path]] = None,
    sanitize: bool = True,
    timeout: float = 2.0,
    memory_limit: Optional[int] = None,
    static: bool = False,
    library_dirs: Optional[Iterable[Path]] = None,
    libraries: Optional[Iterable[str]] = None,
    rpath: Optional[Iterable[Path]] = None,
    use_ccache: bool = False,
    env: Optional[Mapping[str, str]] = None,
    sandbox: Optional[IsolateRunner] = None,
    cache: Optional[SandboxCache] = None,
    stdout_limit: Optional[int] = None,
    stderr_limit: Optional[int] = None,
    collect_coverage: bool = False,
    shared_libs: Optional[Mapping[str, Sequence[Path]]] = None,
    static_libs: Optional[Mapping[str, Sequence[Path]]] = None,
) -> dict:
    """Compile ``sources`` and run them against all tests in ``tests_dir``.

    The directory is expected to contain pairs of ``*.in`` and ``*.out`` files.
    Optional ``shared_libs`` and ``static_libs`` mappings allow building
    auxiliary libraries from source prior to compiling the main program.
    Results include compilation diagnostics and a list of per-test outcomes
    with error classifications. When ``collect_coverage`` is ``True`` the
    program is instrumented with ``--coverage`` and ``gcov`` is used to compute
    a line coverage ratio.

    Parameters
    ----------
    stdout_limit, stderr_limit:
        Optional maximum sizes for captured stdout and stderr from each test
        case. Limits are forwarded to the sandbox runner or applied locally
        when no sandbox is used.
    """

    key: Optional[str] = None
    if cache is not None:
        parts = [Path(s).read_bytes() for s in sources]
        if shared_libs:
            for srcs in shared_libs.values():
                for p in srcs:
                    parts.append(Path(p).read_bytes())
        if static_libs:
            for srcs in static_libs.values():
                for p in srcs:
                    parts.append(Path(p).read_bytes())
        for f in sorted(Path(tests_dir).glob("*")):
            if f.is_file():
                parts.append(f.read_bytes())
        parts.append(compiler.encode())
        for f in sorted(flags or []):
            parts.append(f.encode())
        parts.append(b"sanitize" if sanitize else b"no_sanitize")
        parts.append(b"static" if static else b"dynamic")
        for d in sorted(str(p) for p in include_dirs or []):
            parts.append(d.encode())
        for d in sorted(str(p) for p in library_dirs or []):
            parts.append(d.encode())
        for lib in sorted(libraries or []):
            parts.append(lib.encode())
        for rp in sorted(str(p) for p in rpath or []):
            parts.append(rp.encode())
        parts.append(b"ccache" if use_ccache else b"no_ccache")
        if env:
            for k, v in sorted(env.items()):
                parts.append(f"{k}={v}".encode())
        parts.append(str(timeout).encode())
        if memory_limit is not None:
            parts.append(str(memory_limit).encode())
        if stdout_limit is not None:
            parts.append(f"out{stdout_limit}".encode())
        if stderr_limit is not None:
            parts.append(f"err{stderr_limit}".encode())
        if collect_coverage:
            parts.append(b"coverage")
        key = cache.hash_parts(parts)
        cached = cache.load(key)
        if cached is not None:
            return cached

    compile_flags = list(flags) if flags is not None else list(DEFAULT_FLAGS)
    if collect_coverage:
        compile_flags.append("--coverage")

    stdout_parts: List[str] = []
    stderr_parts: List[str] = []
    total_warnings = 0
    total_errors = 0

    with tempfile.TemporaryDirectory() as lib_tmp:
        lib_dirs: List[Path] = []
        lib_names: List[str] = []
        rpath_list: List[Path] = list(rpath) if rpath is not None else []

        if shared_libs:
            for name, srcs in shared_libs.items():
                out = Path(lib_tmp) / f"lib{name}.so"
                res = compile_shared_library(
                    srcs,
                    output=out,
                    compiler=compiler,
                    flags=compile_flags,
                    sanitize=sanitize,
                    use_ccache=use_ccache,
                )
                stdout_parts.append(res.stdout)
                stderr_parts.append(res.stderr)
                total_warnings += res.warnings
                total_errors += res.errors
                if not res.success or res.binary is None:
                    compile_status = classify_compile(res.success, res.stderr)
                    data = {
                        "compile_stdout": "".join(stdout_parts),
                        "compile_stderr": "".join(stderr_parts),
                        "compile_warnings": total_warnings,
                        "compile_errors": total_errors,
                        "compile_status": compile_status,
                        "results": [],
                    }
                    if cache is not None and key is not None:
                        cache.store(key, data)
                    return data
                lib_dirs.append(out.parent)
                lib_names.append(name)
                rpath_list.append(out.parent)

        if static_libs:
            for name, srcs in static_libs.items():
                out = Path(lib_tmp) / f"lib{name}.a"
                res = compile_static_library(
                    srcs,
                    output=out,
                    compiler=compiler,
                    flags=compile_flags,
                    sanitize=sanitize,
                    use_ccache=use_ccache,
                )
                stdout_parts.append(res.stdout)
                stderr_parts.append(res.stderr)
                total_warnings += res.warnings
                total_errors += res.errors
                if not res.success or res.binary is None:
                    compile_status = classify_compile(res.success, res.stderr)
                    data = {
                        "compile_stdout": "".join(stdout_parts),
                        "compile_stderr": "".join(stderr_parts),
                        "compile_warnings": total_warnings,
                        "compile_errors": total_errors,
                        "compile_status": compile_status,
                        "results": [],
                    }
                    if cache is not None and key is not None:
                        cache.store(key, data)
                    return data
                lib_dirs.append(out.parent)
                lib_names.append(name)

        if library_dirs is not None:
            library_dirs = list(library_dirs) + lib_dirs
        else:
            library_dirs = lib_dirs
        if libraries is not None:
            libraries = list(libraries) + lib_names
        else:
            libraries = lib_names
        if rpath is not None:
            rpath = list(rpath) + rpath_list
        else:
            rpath = rpath_list

        compile_res = compile_cpp_sources(
            sources,
            compiler=compiler,
            flags=compile_flags,
            include_dirs=include_dirs,
            sanitize=sanitize,
            static=static,
            library_dirs=library_dirs,
            libraries=libraries,
            rpath=rpath,
            use_ccache=use_ccache,
        )
        compile_status = classify_compile(
            compile_res.success, compile_res.stderr
        )
        stdout_parts.append(compile_res.stdout)
        stderr_parts.append(compile_res.stderr)
        total_warnings += compile_res.warnings
        total_errors += compile_res.errors
        if not compile_res.success or compile_res.binary is None:
            data = {
                "compile_stdout": "".join(stdout_parts),
                "compile_stderr": "".join(stderr_parts),
                "compile_warnings": total_warnings,
                "compile_errors": total_errors,
                "compile_status": compile_status,
                "results": [],
            }
            if cache is not None and key is not None:
                cache.store(key, data)
            return data

        run_res = run_io_tests(
            compile_res.binary,
            tests_dir,
            timeout=timeout,
            memory_limit=memory_limit,
            env=env,
            sandbox=sandbox,
            cache=cache,
            stdout_limit=stdout_limit,
            stderr_limit=stderr_limit,
        )
        coverage_ratio = 0.0
        if collect_coverage:
            coverage_ratio = _collect_coverage(
                sources, compile_res.binary.parent
            )
        data = {
            "compile_stdout": "".join(stdout_parts),
            "compile_stderr": "".join(stderr_parts),
            "compile_warnings": total_warnings,
            "compile_errors": total_errors,
            "compile_status": compile_status,
            "results": run_res["results"],
        }
        if collect_coverage:
            data["coverage"] = coverage_ratio
        if cache is not None and key is not None:
            cache.store(key, data)
        return data


def run_codeforces_task(
    sources: Sequence[Path],
    task_dir: Path,
    **kwargs,
) -> dict:
    """Compile ``sources`` and run them against a Codeforces task directory.

    The ``task_dir`` is expected to contain a ``tests`` subdirectory with
    ``*.in``/``*.out`` pairs and a ``meta.json`` file providing time and memory
    limits.  The limits are forwarded to :func:`run_codeforces_tests` unless
    explicitly overridden via ``kwargs``.
    """

    meta_path = task_dir / "meta.json"
    timeout = None
    memory_limit = None
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            timeout = meta.get("time_limit_ms", 2000) / 1000.0
            memory_limit = meta.get("memory_limit_kb", 256_000) * 1024
        except Exception:
            timeout = None
            memory_limit = None

    params = dict(kwargs)
    if timeout is not None:
        params.setdefault("timeout", timeout)
    if memory_limit is not None:
        params.setdefault("memory_limit", memory_limit)

    tests_dir = task_dir / "tests"
    return run_codeforces_tests(sources, tests_dir, **params)
