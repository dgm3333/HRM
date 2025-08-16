"""Helpers for scoring build and static-analysis diagnostics."""

from __future__ import annotations

import re


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


def coverage_delta(previous: float, current: float) -> float:
    """Compute non-negative coverage improvement.

    Both ``previous`` and ``current`` are clipped to ``[0, 1]`` before the
    delta is taken.
    """
    prev = max(0.0, min(previous, 1.0))
    curr = max(0.0, min(current, 1.0))
    return max(0.0, curr - prev)

