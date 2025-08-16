from __future__ import annotations

"""Acceptance checks for Phase 0.

Phase 0 of the HRM Coder project defines basic success criteria for C++
experiments.  This module provides a small utility to evaluate whether a
set of metrics meets those criteria.  It is intentionally lightweight and
will be expanded in later phases.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class AcceptanceCriteria:
    """Thresholds used to judge run acceptance.

    Attributes
    ----------
    pass_at_1:
        Minimum required pass@1 value.
    pass_at_10:
        Minimum required pass@10 value.
    max_timeout_rate:
        Maximum tolerated fraction of timeouts.
    max_sanitizer_failures:
        Maximum number of sanitizer failures allowed.
    """

    pass_at_1: float = 0.0
    pass_at_10: float = 0.0
    max_timeout_rate: float = 1.0
    max_sanitizer_failures: int = 0


def evaluate_acceptance(
    metrics: Dict[str, float], criteria: AcceptanceCriteria
) -> Dict[str, bool]:
    """Evaluate ``metrics`` against ``criteria``.

    Parameters
    ----------
    metrics:
        Mapping of metric name to value.  Expected keys are ``"pass@1"``,
        ``"pass@10"``, ``"timeout_rate"`` and ``"sanitizer_failures"``.
    criteria:
        :class:`AcceptanceCriteria` describing the thresholds.

    Returns
    -------
    Dict[str, bool]
        Mapping of check name to a boolean result.  Includes an
        ``"overall"`` key indicating whether all checks passed.
    """

    results = {
        "pass@1": metrics.get("pass@1", 0.0) >= criteria.pass_at_1,
        "pass@10": metrics.get("pass@10", 0.0) >= criteria.pass_at_10,
        "timeout_rate": metrics.get("timeout_rate", 1.0)
        <= criteria.max_timeout_rate,
        "sanitizer_failures": metrics.get("sanitizer_failures", 0)
        <= criteria.max_sanitizer_failures,
    }
    results["overall"] = all(results.values())
    return results


__all__ = ["AcceptanceCriteria", "evaluate_acceptance"]
