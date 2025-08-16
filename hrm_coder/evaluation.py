from __future__ import annotations

"""Evaluation utilities for HRM Coder.

This module provides helpers for Phase 7 of the project: computing
pass@k metrics, detecting nondeterministic behaviour, and generating
simple HTML/Markdown reports.  The implementation follows the
high-level plan laid out in the documentation.
"""

from dataclasses import dataclass
import json
import math
import argparse
from pathlib import Path
from typing import Dict, Sequence, List, Optional

from .artifacts.bundle import bundle_artifacts, upload_bundle


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


def aggregate_pass_at_k(
    results: Dict[str, Sequence[bool]], ks: Sequence[int]
) -> Dict[int, float]:
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

    return [
        task for task, deterministic in check_determinism(runs).items()
        if not deterministic
    ]


def incident_rates(
    runs: Sequence[Dict[str, str]],
    incident_types: Sequence[str] = ("timeout", "sanitizer"),
) -> Dict[str, float]:
    """Compute rates of specified incident types across runs.

    Parameters
    ----------
    runs:
        Sequence of mappings from task identifier to a status string.
    incident_types:
        Iterable of status values to measure. Defaults to ``("timeout",
        "sanitizer")``.
    """

    counts = {inc: 0 for inc in incident_types}
    total = 0
    for run in runs:
        for status in run.values():
            total += 1
            for inc in incident_types:
                if status == inc:
                    counts[inc] += 1
    return {
        inc: (counts[inc] / total if total else 0.0)
        for inc in incident_types
    }


def markdown_report(
    metrics: Dict[int, float],
    flaky: Sequence[str],
    incidents: Dict[str, float] | None = None,
) -> str:
    """Generate a Markdown report for the evaluation metrics."""

    lines = ["# Evaluation Report", "", "| k | pass@k |", "|---|-------|"]
    for k, value in sorted(metrics.items()):
        lines.append(f"| {k} | {value:.3f} |")
    lines.append("")
    if incidents:
        lines.append("## Incident Rates")
        lines.extend(
            f"- {name}: {rate:.3f}" for name, rate in incidents.items()
        )
        lines.append("")
    if flaky:
        lines.append("## Flaky Tasks")
        lines.extend(f"- {task}" for task in flaky)
    else:
        lines.append("No flaky tasks detected.")
    return "\n".join(lines)


def html_report(
    metrics: Dict[int, float],
    flaky: Sequence[str],
    incidents: Dict[str, float] | None = None,
) -> str:
    """Generate a minimal HTML report for the evaluation metrics."""

    rows = "".join(
        f"<tr><td>{k}</td><td>{value:.3f}</td></tr>"
        for k, value in sorted(metrics.items())
    )
    if flaky:
        flaky_html = "<ul>" + "".join(
            f"<li>{task}</li>" for task in flaky
        ) + "</ul>"
    else:
        flaky_html = "<p>No flaky tasks detected.</p>"
    if incidents:
        incidents_html = (
            "<ul>"
            + "".join(
                f"<li>{name}: {rate:.3f}</li>"
                for name, rate in incidents.items()
            )
            + "</ul>"
        )
    else:
        incidents_html = "<p>No incidents recorded.</p>"
    return (
        "<h1>Evaluation Report</h1>"
        "<table><tr><th>k</th><th>pass@k</th></tr>"
        f"{rows}</table>"
        f"{incidents_html}"
        f"{flaky_html}"
    )


def compare_to_baseline(
    current: Dict[str, float], baseline_path: str
) -> Dict[str, Dict[str, Optional[float]]]:
    """Compare ``current`` metrics to a JSON baseline.

    Parameters
    ----------
    current:
        Mapping of metric name to value for the current run.
    baseline_path:
        Path to a JSON file containing the baseline metrics with the
        same keys as ``current``.

    Returns
    -------
    Dict[str, Dict[str, Optional[float]]]
        Mapping metric name → {"baseline", "current", "delta"}.
        ``delta`` is ``None`` when the metric is missing from the baseline.
    """

    p = Path(baseline_path)
    baseline = json.loads(p.read_text()) if p.exists() else {}
    comparison: Dict[str, Dict[str, Optional[float]]] = {}
    for key, cur_val in current.items():
        base_val = baseline.get(key)
        delta = cur_val - base_val if base_val is not None else None
        comparison[key] = {
            "baseline": base_val,
            "current": cur_val,
            "delta": delta,
        }
    return comparison


def comparison_markdown_report(
    comparison: Dict[str, Dict[str, Optional[float]]]
) -> str:
    """Render a baseline comparison as a Markdown table."""

    lines = [
        "# Baseline Comparison",
        "",
        "| metric | baseline | current | delta |",
        "|---|---|---|---|",
    ]

    def fmt(val: Optional[float]) -> str:
        return f"{val:.3f}" if isinstance(val, float) else str(val)

    for metric, vals in comparison.items():
        lines.append(
            "| {m} | {b} | {c} | {d} |".format(
                m=metric,
                b=fmt(vals['baseline']),
                c=fmt(vals['current']),
                d=fmt(vals['delta']),
            )
        )
    return "\n".join(lines)


def comparison_html_report(
    comparison: Dict[str, Dict[str, Optional[float]]]
) -> str:
    """Render a baseline comparison as HTML."""

    def fmt(val: Optional[float]) -> str:
        return f"{val:.3f}" if isinstance(val, float) else str(val)

    rows = "".join(
        (
            f"<tr><td>{metric}</td><td>{fmt(vals['baseline'])}</td>"
            f"<td>{fmt(vals['current'])}</td>"
            f"<td>{fmt(vals['delta'])}</td></tr>"
        )
        for metric, vals in comparison.items()
    )
    return (
        "<h1>Baseline Comparison</h1>"
        "<table><tr><th>metric</th><th>baseline</th>"
        "<th>current</th><th>delta</th></tr>"
        f"{rows}</table>"
    )


def generate_reports(
    results_path: str,
    output_dir: str,
    ks: Sequence[int] = (1, 10),
    run_paths: Sequence[str] | None = None,
    baseline_path: str | None = None,
    incident_paths: Sequence[str] | None = None,
    bundle_path: str | None = None,
    upload_dir: str | None = None,
) -> Dict[int, float]:
    """Compute metrics and emit Markdown/HTML reports.

    Parameters
    ----------
    results_path:
        JSON file mapping task id → list[bool] of attempt outcomes.
    output_dir:
        Directory where reports will be written.
    ks:
        Values of ``k`` for which ``pass@k`` will be computed.
    run_paths:
        Optional JSON files mapping task id → bool, used for flakiness
        detection across independent runs.
    baseline_path:
        Optional path to a JSON file containing baseline metrics for
        comparison.  Baseline keys should be of the form ``"pass@k"``.
    incident_paths:
        Optional JSON files mapping task id → status string, used to
        compute incident rates such as timeouts and sanitizer failures.
    bundle_path:
        Optional path for a bundled ``.tar.gz`` archive containing the
        generated reports and raw JSON. If ``None`` the bundle is skipped
        unless ``upload_dir`` is provided.
    upload_dir:
        Optional destination directory to copy the bundle to. If
        provided, a bundle will be created even when ``bundle_path`` is
        ``None``.

    Returns
    -------
    Dict[int, float]
        The aggregated ``pass@k`` metrics.
    """

    results = json.loads(Path(results_path).read_text())
    metrics = aggregate_pass_at_k(results, ks)

    runs = (
        [json.loads(Path(p).read_text()) for p in run_paths]
        if run_paths
        else []
    )
    flaky = flaky_tasks(runs) if runs else []

    incidents = (
        incident_rates(
            [json.loads(Path(p).read_text()) for p in incident_paths]
        )
        if incident_paths
        else None
    )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Persist raw results and aggregated metrics for bundling
    (out_dir / "results.json").write_text(json.dumps(results))
    (out_dir / "metrics.json").write_text(
        json.dumps({str(k): v for k, v in metrics.items()})
    )

    (out_dir / "report.md").write_text(
        markdown_report(metrics, flaky, incidents)
    )
    (out_dir / "report.html").write_text(
        html_report(metrics, flaky, incidents)
    )

    bundle_file: str | None = None

    if baseline_path is not None:
        named_metrics = {f"pass@{k}": v for k, v in metrics.items()}
        comparison = compare_to_baseline(named_metrics, baseline_path)
        (out_dir / "baseline.md").write_text(
            comparison_markdown_report(comparison)
        )
        (out_dir / "baseline.html").write_text(
            comparison_html_report(comparison)
        )

    if bundle_path is not None or upload_dir is not None:
        bundle_file = bundle_path or str(out_dir / "artifacts.tar.gz")
        files = [
            out_dir / "report.md",
            out_dir / "report.html",
            out_dir / "results.json",
            out_dir / "metrics.json",
        ]
        if baseline_path is not None:
            files.extend(
                [out_dir / "baseline.md", out_dir / "baseline.html"]
            )
        bundle_artifacts([str(f) for f in files], bundle_file)
        if upload_dir is not None:
            upload_bundle(bundle_file, upload_dir)

    return metrics


def main() -> None:  # pragma: no cover - CLI entry point
    parser = argparse.ArgumentParser(description="Generate evaluation reports")
    parser.add_argument(
        "results",
        help="JSON file with task → [bool] attempts",
    )
    parser.add_argument(
        "output",
        help="Directory for generated reports",
    )
    parser.add_argument(
        "--k",
        dest="ks",
        type=int,
        nargs="*",
        default=[1, 10],
        help="k values for pass@k",
    )
    parser.add_argument(
        "--runs",
        nargs="*",
        default=None,
        help="JSON files of individual run outcomes for flakiness detection",
    )
    parser.add_argument(
        "--baseline",
        default=None,
        help="JSON file with baseline metrics for comparison",
    )
    parser.add_argument(
        "--incidents",
        nargs="*",
        default=None,
        help="JSON files of run status strings for incident rate computation",
    )
    parser.add_argument(
        "--bundle",
        default=None,
        help="Path to write a bundled tar.gz of reports and JSON",
    )
    parser.add_argument(
        "--upload",
        default=None,
        help="Directory to copy the bundle to (artifact upload)",
    )
    args = parser.parse_args()
    generate_reports(
        results_path=args.results,
        output_dir=args.output,
        ks=args.ks,
        run_paths=args.runs,
        baseline_path=args.baseline,
        incident_paths=args.incidents,
        bundle_path=args.bundle,
        upload_dir=args.upload,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
