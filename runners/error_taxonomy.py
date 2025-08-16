from __future__ import annotations

"""Utilities for classifying compilation and execution outcomes.

This module implements a small error taxonomy used by Phase 4's sandbox
executor.  It distinguishes between compilation failures, linker issues,
run-time errors, timeouts, sanitizer crashes, and sandbox policy
violations.  The functions intentionally rely on simple substring
matches so they can operate on raw ``stderr`` output without requiring
compiler-specific knowledge.
"""

from typing import Iterable

# Patterns used to detect particular error categories.  All comparisons are
# performed on lower-cased ``stderr`` text.
_LINK_PATTERNS: Iterable[str] = [
    "undefined reference",
    "ld returned",
    "linker command failed",
]

_SANITIZER_PATTERNS: Iterable[str] = [
    "addresssanitizer",
    "undefinedbehaviorsanitizer",
    "ubsan",
    "asan",
]

_POLICY_PATTERNS: Iterable[str] = [
    "operation not permitted",
    "permission denied",
    "policy violation",
    "sandbox",
]


def classify_compile(success: bool, stderr: str) -> str:
    """Classify the result of a compilation step.

    Parameters
    ----------
    success:
        Boolean indicating whether the compiler exited with status code ``0``.
    stderr:
        ``stderr`` text produced by the compiler.

    Returns
    -------
    str
        One of ``"success"``, ``"link_error"``, or ``"compile_error"``.
    """

    if success:
        return "success"
    err = stderr.lower()
    for pat in _LINK_PATTERNS:
        if pat in err:
            return "link_error"
    return "compile_error"


def classify_runtime(
    returncode: int,
    stderr: str,
    *,
    timed_out: bool = False,
) -> str:
    """Classify the result of executing a binary.

    Parameters
    ----------
    returncode:
        Process return code from execution.
    stderr:
        ``stderr`` text produced by the process.
    timed_out:
        Whether execution exceeded the allotted wall time.

    Returns
    -------
    str
        One of ``"success"``, ``"timeout"``,
        ``"sanitizer_error"``, ``"policy_violation"``, or
        ``"runtime_error"``.
    """

    if timed_out:
        return "timeout"
    if returncode == 0:
        return "success"

    err = stderr.lower()
    for pat in _SANITIZER_PATTERNS:
        if pat in err:
            return "sanitizer_error"
    for pat in _POLICY_PATTERNS:
        if pat in err or returncode == 159:
            return "policy_violation"
    return "runtime_error"
