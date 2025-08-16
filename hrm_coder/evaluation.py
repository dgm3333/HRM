from __future__ import annotations

"""Evaluation utilities for HRM Coder.

This module provides helpers for Phase 7 of the project: computing
pass@k metrics, detecting nondeterministic behaviour, and generating
simple HTML/Markdown reports.  The implementation follows the
high-level plan laid out in the documentation.
"""

from dataclasses import dataclass
from typing import Dict, Sequence, Iterable, List
import math


@dataclass
class TaskEvaluation:
    """Container for the results of evaluating a single task.

    Attributes
    ----------
    attempts:
        Sequence of booleans indicating whether each attempt passed.
    """

    attempts: Sequence[bool]

    def pass_at_k(self, k: int) -> float:
        """Compute pass@k for this task.

        Implements the estimator used for code benchmarks
        ``1 - comb(n - c, k) / comb(n, k)`` where ``c`` is the number of
        correct samples and ``n`` the total number of attempts.
        """

        n = len(self.attempts)
        if k > n:
            raise ValueError("k cannot be larger than the number of attempts")
        c = sum(self.attempts)
        if c == 0:
            return 0.0
        if c == n:
            return 1.0
        # 1 - comb(n - c, k) / comb(n, k)
        return 1.0 - math.prod((n - c - i) / (n - i) for i in range(k))


def aggregate_pass_at_k(results: Dict[str, Sequence[bool]], ks: Sequence[int]) -> Dict[int, float]:
    """Aggregate pass@k across a set of tasks.

    Parameters
    ----------
    results:
        Mapping from task identifier to sequences of attempt outcomes.
    ks:
        Iterable of ``k`` values to compute.
    """

    aggregates: Dict[int, List[float]] = {k: [] for k in ks}
    for task_attempts in results.values():
        task_eval = TaskEvaluation(task_attempts)
        for k in ks:
            if k <= len(task_attempts):
                aggregates[k].append(task_eval.pass_at_k(k))
    return {k: (sum(v) / len(v) if v else 0.0) for k, v in aggregates.items()}


def check_determinism(runs: Sequence[Dict[str, bool]]) -> Dict[str, bool]:
    """Check whether each task result is deterministic across runs.

    Returns a mapping from task identifier to ``True`` if all runs agree on
    the outcome, ``False`` otherwise.
    """

    if not runs:
        return {}
    task_ids = runs[0].keys()
    determ = {}
    for task_id in task_ids:
        outcomes = {run.get(task_id) for run in runs}
        determ[task_id] = len(outcomes) == 1
    return determ


def flaky_tasks(runs: Sequence[Dict[str, bool]]) -> List[str]:
    """Return identifiers of tasks with inconsistent outcomes."""

    return [task for task, deterministic in check_determinism(runs).items() if not deterministic]


def markdown_report(metrics: Dict[int, float], flaky: Sequence[str]) -> str:
    """Generate a Markdown report for the evaluation metrics."""

    lines = ["# Evaluation Report", "", "| k | pass@k |", "|---|-------|"]
    for k, value in sorted(metrics.items()):
        lines.append(f"| {k} | {value:.3f} |")
    lines.append("")
    if flaky:
        lines.append("## Flaky Tasks")
        lines.extend(f"- {task}" for task in flaky)
    else:
        lines.append("No flaky tasks detected.")
    return "\n".join(lines)


def html_report(metrics: Dict[int, float], flaky: Sequence[str]) -> str:
    """Generate a minimal HTML report for the evaluation metrics."""

    rows = "".join(f"<tr><td>{k}</td><td>{value:.3f}</td></tr>" for k, value in sorted(metrics.items()))
    if flaky:
        flaky_html = "<ul>" + "".join(f"<li>{task}</li>" for task in flaky) + "</ul>"
    else:
        flaky_html = "<p>No flaky tasks detected.</p>"
    return (
        "<h1>Evaluation Report</h1>"
        "<table><tr><th>k</th><th>pass@k</th></tr>"
        f"{rows}</table>"
        f"{flaky_html}"
    )

