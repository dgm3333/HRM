"""Run binaries against I/O tests with optional sandbox and caching."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from .error_taxonomy import classify_runtime
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
                "error_type": error_type,
            }
        )

    data = {"results": results}
    if cache is not None and key is not None:
        cache.store(key, data)
    return data
