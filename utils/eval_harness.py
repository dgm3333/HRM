"""Utility helpers for evaluating code generation.

The functions here compute pass@k metrics, check determinism, detect
flaky tests, generate simple HTML/Markdown reports, and bundle
artifacts. They support Phase 7 of the HRM Coder project plan.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
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


def compute_pass_at_k(
    task_results: Dict[str, Iterable[bool]], k: int
) -> float:
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


def check_determinism(
    run: Callable[[], Dict[str, Any]], repeats: int = 2
) -> DeterminismResult:
    """Run ``run`` multiple times and verify outputs are identical.

    ``run`` should be a zero-argument callable returning a mapping of artifact
    names to serialisable values. The function returns a
    :class:`DeterminismResult` describing whether runs were identical and any
      differences found.
      """
    baseline = run()
    differences: Dict[str, List[Any]] = {}
    for _ in range(1, repeats):
        new = run()
        for key in set(baseline) | set(new):
            if baseline.get(key) != new.get(key):
                differences.setdefault(key, []).extend(
                    [baseline.get(key), new.get(key)]
                )
    return DeterminismResult(
        deterministic=not differences, differences=differences
    )


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


def aggregate_cpp_metrics(data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate C++-specific metrics from per-task results.

    Parameters
    ----------
    data:
        Mapping from task identifier to dictionaries containing keys such as
        ``compile_status``, ``compile_warnings`` and ``coverage``.

    Returns
    -------
    Dict[str, float]
        Summary metrics including ``compile_success_rate``,
        ``avg_compile_warnings`` and ``avg_coverage``.
    """

    total = len(data)
    if total == 0:
        return {
            "compile_success_rate": 0.0,
            "avg_compile_warnings": 0.0,
            "avg_coverage": 0.0,
        }

    success = sum(
        1 for m in data.values() if m.get("compile_status") == "success"
    )
    warnings = sum(int(m.get("compile_warnings", 0)) for m in data.values())
    coverages = [
        float(m.get("coverage"))
        for m in data.values()
        if m.get("coverage") is not None
    ]
    avg_cov = sum(coverages) / len(coverages) if coverages else 0.0
    return {
        "compile_success_rate": success / total,
        "avg_compile_warnings": warnings / total,
        "avg_coverage": avg_cov,
    }


def generate_report(
    metrics: Dict[str, Any],
    path: str,
    extra_metrics: Dict[str, float] | None = None,
) -> None:
    """Generate a simple report containing ``metrics``.

    The format is inferred from ``path`` extension: ``.md`` for Markdown,
    ``.html`` for HTML and any other extension for JSON.
    ``extra_metrics`` can be provided to include additional metrics such as
    aggregated C++ outcomes.
    """
    data = dict(metrics)
    if extra_metrics:
        data.update(extra_metrics)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() == ".md":
        lines = ["# Evaluation Report", ""]
        for key, value in data.items():
            lines.append(f"- **{key}**: {value}")
        p.write_text("\n".join(lines))
    elif p.suffix.lower() in {".html", ".htm"}:
        rows = "\n".join(
            f"<tr><th>{key}</th><td>{value}</td></tr>" for key, value in data.items()
        )
        html = f"<html><body><table>{rows}</table></body></html>"
        p.write_text(html)
    else:
        p.write_text(json.dumps(data, indent=2))


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


def upload_bundle(bundle_path: str, dest_dir: str) -> str:
    """Upload a bundle to ``dest_dir`` by copying it.

    This simple uploader is intended for local file systems and is sufficient
    for tests and CI environments. Returns the destination path of the copied
    bundle.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / Path(bundle_path).name
    shutil.copy2(bundle_path, target)
    return str(target)


def bundle_and_upload(
    paths: Iterable[str], bundle_path: str, dest_dir: str
) -> str:
    """Bundle ``paths`` into ``bundle_path`` and upload to ``dest_dir``.

    Returns the path to the uploaded bundle.
    """
    bundle_artifacts(paths, bundle_path)
    return upload_bundle(bundle_path, dest_dir)


def compare_to_baseline(
    current: Dict[str, float], baseline_path: str
) -> Dict[str, Dict[str, float]]:
    """Compare ``current`` metrics to a JSON baseline.

    The ``baseline_path`` should point to a JSON file with metric names mapped
    to numeric values. The returned dictionary maps metric names to
    dictionaries with ``baseline``, ``current`` and ``delta`` fields. Missing
    baseline values yield ``None`` deltas.
    """
    p = Path(baseline_path)
    baseline = json.loads(p.read_text()) if p.exists() else {}
    comparison: Dict[str, Dict[str, float]] = {}
    for key, cur_val in current.items():
        base_val = baseline.get(key)
        delta = cur_val - base_val if base_val is not None else None
        comparison[key] = {
            "baseline": base_val,
            "current": cur_val,
            "delta": delta,
        }
    return comparison


def generate_comparison_report(
    current: Dict[str, float], baseline_path: str, report_path: str
) -> Dict[str, Dict[str, float]]:
    """Generate a report comparing ``current`` metrics to a baseline.

    The function loads ``baseline_path`` using :func:`compare_to_baseline` and
    writes a report to ``report_path``.  The output format mirrors
    :func:`generate_report`:

    * ``.md`` → Markdown table
    * ``.html``/``.htm`` → HTML table
    * any other extension → JSON

    The structured comparison dictionary is returned for further processing.
    """

    comparison = compare_to_baseline(current, baseline_path)

    p = Path(report_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() == ".md":
        lines = [
            "# Baseline Comparison",
            "",
            "| metric | baseline | current | delta |",
            "|---|---|---|---|",
        ]
        for metric, vals in comparison.items():
            lines.append(
                f"| {metric} | {vals['baseline']} | "
                f"{vals['current']} | {vals['delta']} |"
            )
        p.write_text("\n".join(lines))
    elif p.suffix.lower() in {".html", ".htm"}:
        rows = "\n".join(
            f"<tr><th>{metric}</th><td>{vals['baseline']}</td><td>"
            f"{vals['current']}</td><td>{vals['delta']}</td></tr>"
            for metric, vals in comparison.items()
        )
        html = (
            "<html><body><table><tr><th>metric</th><th>baseline</th>"
            "<th>current</th><th>delta</th></tr>"
            f"{rows}</table></body></html>"
        )
        p.write_text(html)
    else:
        p.write_text(json.dumps(comparison, indent=2))

    return comparison
