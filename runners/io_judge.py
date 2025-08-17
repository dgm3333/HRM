"""Run binaries against I/O tests with optional sandbox and caching."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

from .error_taxonomy import classify_compile, classify_runtime
from .isolate import IsolateRunner
from .sandbox_cache import SandboxCache


def _run_binary(*args, **kwargs):
    from .cpp_runner import run_binary  # lazy import
    return run_binary(*args, **kwargs)


def _normalize(text: str) -> str:
    """Normalize whitespace for output comparison."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def run_io_tests(
    binary: Path,
    tests_dir: Path,
    *,
    timeout: float = 2.0,
    memory_limit: Optional[int] = None,
    env: Optional[Mapping[str, str]] = None,
    sandbox: Optional[IsolateRunner] = None,
    cache: Optional[SandboxCache] = None,
    stdout_limit: Optional[int] = None,
    stderr_limit: Optional[int] = None,
) -> Dict[str, object]:
    """Run ``binary`` against I/O testcases in ``tests_dir``.

    Parameters
    ----------
    binary:
        Path to the compiled executable to test.
    tests_dir:
        Directory containing ``*.in``/``*.out`` file pairs.
    timeout:
        Maximum wall-clock time in seconds for each test case.
    memory_limit:
        Optional memory limit in bytes.
    env:
        Additional environment variables for execution.
    sandbox:
        Optional :class:`IsolateRunner` enforcing resource limits.
    cache:
        Optional :class:`SandboxCache` to memoize results.
    stdout_limit, stderr_limit:
        Optional maximum sizes for captured stdout and stderr per test case.
        When provided these limits are forwarded to the sandbox runner or
        applied locally to the captured output.

    Returns
    -------
    dict
        Dictionary with a ``results`` key listing per-test outcomes.
    """

    key: Optional[str] = None
    if cache is not None:
        parts: List[bytes] = [binary.read_bytes(), str(timeout).encode()]
        if memory_limit is not None:
            parts.append(str(memory_limit).encode())
        if stdout_limit is not None:
            parts.append(f"out{stdout_limit}".encode())
        if stderr_limit is not None:
            parts.append(f"err{stderr_limit}".encode())
        for f in sorted(Path(tests_dir).glob("*")):
            if f.is_file():
                parts.append(f.read_bytes())
        key = cache.hash_parts(parts)
        cached = cache.load(key)
        if cached is not None:
            return cached

    results: List[Dict[str, object]] = []
    for input_file in sorted(Path(tests_dir).glob("*.in")):
        test_name = input_file.stem
        expected_file = input_file.with_suffix(".out")
        input_data = input_file.read_text()
        expected = expected_file.read_text() if expected_file.exists() else ""
        try:
            code, stdout, stderr = _run_binary(
                binary,
                input_data=input_data,
                timeout=timeout,
                memory_limit=memory_limit,
                env=env,
                sandbox=sandbox,
                stdout_limit=stdout_limit,
                stderr_limit=stderr_limit,
            )
            timed_out = False
        except subprocess.TimeoutExpired:
            code, stdout, stderr = -1, "", "TIMEOUT"
            timed_out = True
        passed = _normalize(stdout) == _normalize(expected) and code == 0
        error_type = classify_runtime(code, stderr, timed_out=timed_out)
        results.append(
            {
                "test": test_name,
                "passed": passed,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": code,
                "error_type": error_type,
            }
        )

    data = {"results": results}
    if cache is not None and key is not None:
        cache.store(key, data)
    return data


def compile_and_run_io_tests(
    sources: Sequence[Path],
    tests_dir: Path,
    *,
    compiler: str = "g++",
    flags: Optional[Sequence[str]] = None,
    sanitize: bool = True,
    sandbox: Optional[IsolateRunner] = None,
    cache: Optional[SandboxCache] = None,
    timeout: float = 2.0,
    memory_limit: Optional[int] = None,
    env: Optional[Mapping[str, str]] = None,
    stdout_limit: Optional[int] = None,
    stderr_limit: Optional[int] = None,
) -> Dict[str, object]:
    """Compile ``sources`` and run resulting binary against I/O tests.

    This helper advances Phase 4 by wiring the C++ build step to the
    :func:`run_io_tests` execution harness. Compilation diagnostics and the
    parsed I/O test results are returned in a single dictionary. Results can be
    memoized via :class:`SandboxCache` keyed by the source files, tests, and
    resource limits.
    """
    from .cpp_runner import compile_cpp_sources, DEFAULT_FLAGS

    compile_flags = list(flags) if flags is not None else list(DEFAULT_FLAGS)

    key: Optional[str] = None
    if cache is not None:
        parts = [Path(s).read_bytes() for s in sources]
        for f in sorted(compile_flags):
            parts.append(f.encode())
        parts.append(compiler.encode())
        parts.append(b"sanitize" if sanitize else b"no_sanitize")
        parts.append(str(timeout).encode())
        if memory_limit is not None:
            parts.append(str(memory_limit).encode())
        if stdout_limit is not None:
            parts.append(f"out{stdout_limit}".encode())
        if stderr_limit is not None:
            parts.append(f"err{stderr_limit}".encode())
        for f in sorted(Path(tests_dir).glob("*")):
            if f.is_file():
                parts.append(f.read_bytes())
        key = cache.hash_parts(parts)
        cached = cache.load(key)
        if cached is not None:
            return cached

    compile_res = compile_cpp_sources(
        sources,
        compiler=compiler,
        flags=compile_flags,
        sanitize=sanitize,
    )
    compile_status = classify_compile(compile_res.success, compile_res.stderr)
    data: Dict[str, object] = {
        "compile_stdout": compile_res.stdout,
        "compile_stderr": compile_res.stderr,
        "compile_warnings": compile_res.warnings,
        "compile_errors": compile_res.errors,
        "compile_status": compile_status,
    }

    if not compile_res.success or compile_res.binary is None:
        data["results"] = []
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
        cache=None,
        stdout_limit=stdout_limit,
        stderr_limit=stderr_limit,
    )
    data.update(run_res)
    if cache is not None and key is not None:
        cache.store(key, data)
    return data


__all__ = ["run_io_tests", "compile_and_run_io_tests"]
