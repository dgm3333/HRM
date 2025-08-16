"""Utility functions for evaluation and reporting of code generation results.

This module provides helpers for computing pass@k metrics, checking determinism,
identifying flaky tests, generating simple HTML/Markdown reports and bundling
artifacts. These utilities support Phase 7 of the HRM Coder project plan.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List
import zipfile


def pass_at_k(num_correct: int, num_samples: int, k: int) -> float:
    """Estimate pass@k for a single task.

    Args:
        num_correct: Number of successful solutions generated.
        num_samples: Total number of candidate solutions generated.
        k: Number of samples to draw when evaluating pass@k.

    Returns:
        Probability that at least one of ``k`` randomly drawn samples is
        correct. Implements the analytic estimator from HumanEval.
    """
    if num_samples == 0 or num_correct == 0:
        return 0.0
    k = min(k, num_samples)
    prod = 1.0
    for i in range(k):
        prod *= (num_samples - num_correct - i) / (num_samples - i)
    return 1.0 - prod


def compute_pass_at_k(task_results: Dict[str, Iterable[bool]], k: int) -> float:
    """Compute mean pass@k across many tasks.

    ``task_results`` maps task identifiers to iterables of booleans where
    ``True`` denotes a correct program.
    """
    scores: List[float] = []
    for results in task_results.values():
        results = list(results)
        score = pass_at_k(sum(results), len(results), k)
        scores.append(score)
    return sum(scores) / len(scores) if scores else 0.0


@dataclass
class DeterminismResult:
    deterministic: bool
    differences: Dict[str, List[Any]]


def check_determinism(run: Callable[[], Dict[str, Any]], repeats: int = 2) -> DeterminismResult:
    """Run ``run`` multiple times and verify outputs are identical.

    ``run`` should be a zero-argument callable returning a mapping of artifact
    names to serialisable values. The function returns a :class:`DeterminismResult`
    describing whether runs were identical and any differences found.
    """
    baseline = run()
    differences: Dict[str, List[Any]] = {}
    for _ in range(1, repeats):
        new = run()
        for key in set(baseline) | set(new):
            if baseline.get(key) != new.get(key):
                differences.setdefault(key, []).extend([baseline.get(key), new.get(key)])
    return DeterminismResult(deterministic=not differences, differences=differences)


def detect_flaky_tests(run_results: List[Dict[str, bool]]) -> List[str]:
    """Identify tests that exhibit both passing and failing outcomes."""
    if not run_results:
        return []
    tests = run_results[0].keys()
    flaky: List[str] = []
    for test in tests:
        outcomes = {results.get(test) for results in run_results}
        if len(outcomes) > 1:
            flaky.append(test)
    return flaky


def generate_report(metrics: Dict[str, Any], path: str) -> None:
    """Generate a simple report containing ``metrics``.

    The format is inferred from ``path`` extension: ``.md`` for Markdown,
    ``.html`` for HTML and any other extension for JSON.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() == ".md":
        lines = ["# Evaluation Report", ""]
        for key, value in metrics.items():
            lines.append(f"- **{key}**: {value}")
        p.write_text("\n".join(lines))
    elif p.suffix.lower() in {".html", ".htm"}:
        rows = "\n".join(f"<tr><th>{key}</th><td>{value}</td></tr>" for key, value in metrics.items())
        html = f"<html><body><table>{rows}</table></body></html>"
        p.write_text(html)
    else:
        p.write_text(json.dumps(metrics, indent=2))


def bundle_artifacts(paths: Iterable[str], bundle_path: str) -> None:
    """Create a zip archive containing the provided ``paths``.

    Args:
        paths: Iterable of file paths to include in the archive.
        bundle_path: Destination zip archive path.
    """
    bundle = Path(bundle_path)
    bundle.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle, "w") as zf:
        for p in paths:
            p = Path(p)
            if p.exists():
                zf.write(p, p.name)
