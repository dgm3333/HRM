from __future__ import annotations

"""Utilities to build and execute Codeforces-style I/O test harnesses.

These helpers create a temporary directory layout mirroring the
``build_codeforces_intro_dataset`` output so that compiled C++ sources can be
run against multiple ``*.in``/``*.out`` pairs. Time and memory limits are
stored in ``meta.json`` and honoured by
``runners.cpp_runner.run_codeforces_task``.
"""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .cpp_runner import run_codeforces_task


@dataclass
class IOPair:
    """Simple container for an input/output example."""

    input: str
    output: str


def build_io_harness(
    tests: Sequence[IOPair],
    dest: Path,
    *,
    time_limit_ms: int = 2000,
    memory_limit_kb: int = 256_000,
) -> Path:
    """Write ``tests`` to ``dest`` in the Codeforces task layout.

    Parameters
    ----------
    tests:
        Sequence of :class:`IOPair` examples.
    dest:
        Destination directory that will contain a ``tests`` subdirectory and
        ``meta.json`` with time and memory limits.
    time_limit_ms, memory_limit_kb:
        Limits stored alongside the test files to mirror the dataset format.
    """

    dest = Path(dest)
    tests_dir = dest / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    for idx, io in enumerate(tests):
        (tests_dir / f"{idx}.in").write_text(io.input)
        (tests_dir / f"{idx}.out").write_text(io.output)
    meta = {"time_limit_ms": time_limit_ms, "memory_limit_kb": memory_limit_kb}
    (dest / "meta.json").write_text(json.dumps(meta))
    return dest


def run_io_harness(
    sources: Sequence[Path],
    tests: Sequence[IOPair],
    *,
    time_limit_ms: int = 2000,
    memory_limit_kb: int = 256_000,
    **kwargs,
) -> dict:
    """Compile ``sources`` and execute them against ``tests``.

    A temporary harness directory is created under the hood using
    :func:`build_io_harness` and discarded after execution.
    Additional keyword arguments are forwarded to
    :func:`~runners.cpp_runner.run_codeforces_task`.
    """

    with tempfile.TemporaryDirectory() as tmp:
        task_dir = build_io_harness(
            tests,
            Path(tmp),
            time_limit_ms=time_limit_ms,
            memory_limit_kb=memory_limit_kb,
        )
        return run_codeforces_task(sources, task_dir, **kwargs)


def summarize_result(result: dict) -> dict:
    """Summarize a Codeforces harness execution result.

    Parameters
    ----------
    result:
        Dictionary produced by :func:`run_io_harness` or
        :func:`~runners.cpp_runner.run_codeforces_task`.

    Returns
    -------
    dict
        Summary containing an overall ``verdict`` (``"OK"``, ``"WA"``,
        ``"TL"``, ``"ML"``, ``"RE"``, or ``"CE"``), whether all tests
        ``passed``, and counts of passed versus total tests.
    """

    compile_status = result.get("compile_status", "")
    tests = result.get("results", [])
    passed_tests = sum(1 for t in tests if t.get("passed"))
    total_tests = len(tests)

    verdict = "OK"
    if compile_status != "success":
        verdict = "CE"
    else:
        for t in tests:
            err = t.get("error_type")
            if err == "timeout":
                verdict = "TL"
                break
            if err in {"policy_violation", "sanitizer_error"}:
                verdict = "RE"
                break
            if err == "runtime_error":
                stderr = t.get("stderr", "").lower()
                if "memory" in stderr or "bad_alloc" in stderr:
                    verdict = "ML"
                else:
                    verdict = "RE"
                break
            if not t.get("passed"):
                verdict = "WA"
                break

    return {
        "verdict": verdict,
        "passed": verdict == "OK",
        "passed_tests": passed_tests,
        "total_tests": total_tests,
    }


__all__ = [
    "IOPair",
    "build_io_harness",
    "run_io_harness",
    "summarize_result",
]
