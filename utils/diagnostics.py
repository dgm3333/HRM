"""Helpers for scoring build and static-analysis diagnostics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


def clang_tidy_score(output: str) -> float:
    """Return a normalized score from clang-tidy/clang diagnostics.

    Parameters
    ----------
    output:
        Raw stderr/stdout produced by clang-tidy or clang++ with
        ``-Wall -Wextra -Werror`` enabled.
    """
    problems = len(re.findall(r": (?:warning|error|note):", output))
    return max(0.0, 1.0 - 0.1 * problems)


def cppcheck_score(output: str) -> float:
    """Return a normalized score from cppcheck output.

    Each ``[warning]`` or ``[error]`` decreases the score by 0.1.
    """
    problems = len(re.findall(r"\[(?:error|warning)\]", output))
    return max(0.0, 1.0 - 0.1 * problems)


@dataclass
class Diagnostic:
    """Single compiler diagnostic entry."""

    file: str
    line: int
    column: int
    level: str
    message: str


_DIAG_RE = re.compile(r"^(.*?):(\d+):(\d+): (warning|error|note): (.*)$")


def parse_compiler_diagnostics(stdout: str, stderr: str) -> List[Diagnostic]:
    """Parse ``stdout``/``stderr`` into structured diagnostics."""

    text = f"{stdout}\n{stderr}"
    diags: List[Diagnostic] = []
    for line in text.splitlines():
        m = _DIAG_RE.match(line.strip())
        if not m:
            continue
        file, line_no, col_no, level, msg = m.groups()
        diags.append(
            Diagnostic(
                file=file,
                line=int(line_no),
                column=int(col_no),
                level=level,
                message=msg,
            )
        )
    return diags


def compiler_diagnostics(stdout: str, stderr: str) -> tuple[int, int]:
    """Return counts of warnings and errors from compiler output."""

    diags = parse_compiler_diagnostics(stdout, stderr)
    warnings = sum(d.level == "warning" for d in diags)
    errors = sum(d.level == "error" for d in diags)
    return warnings, errors


def diagnostics_score(warnings: int, errors: int) -> float:
    """Return a normalized score from warning and error counts.

    Each compiler warning reduces the score by ``0.05`` and each error by
    ``0.2``.  The result is clipped to the ``[0, 1]`` interval.
    """

    penalty = 0.05 * warnings + 0.2 * errors
    return max(0.0, 1.0 - penalty)


def sanitizer_clean(output: str) -> bool:
    """Return True when no sanitizer issues are detected.

    A very small heuristic is used for now: any occurrence of the word
    ``"Sanitizer"`` or the phrase ``"runtime error"`` is treated as evidence
    of a sanitizer-triggered crash.  This keeps the interface simple while the
    full sandbox executor is still in development.
    """

    return re.search(r"Sanitizer|runtime error", output) is None


def coverage_delta(previous: float, current: float) -> float:
    """Compute non-negative coverage improvement.

    Both ``previous`` and ``current`` are clipped to ``[0, 1]`` before the
    delta is taken.
    """
    prev = max(0.0, min(previous, 1.0))
    curr = max(0.0, min(current, 1.0))
    return max(0.0, curr - prev)

