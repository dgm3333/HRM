from __future__ import annotations

"""Command line interface for the evaluation harness.

This tool wraps the Phase 7 evaluation utilities to compute pass@k metrics,
detect incidents and flakiness, generate HTML/Markdown reports and check
acceptance criteria defined in the configuration.
"""

import argparse
import json
from pathlib import Path
from typing import Sequence

from .config import load_config
from .env import pin_environment
from .evaluation import generate_reports, incident_rates
from .acceptance import AcceptanceCriteria, evaluate_acceptance


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "results",
        help="JSON file mapping task id → list[bool] attempts",
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
        help="k values for pass@k computation",
    )
    parser.add_argument(
        "--runs",
        nargs="*",
        default=None,
        help="JSON files of run outcomes for flakiness detection",
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
        help="JSON files mapping task id → status string for incident rates",
    )
    parser.add_argument(
        "--bundle",
        default=None,
        help="Path to write a bundled tar.gz of reports and raw JSON",
    )
    parser.add_argument(
        "--upload",
        default=None,
        help="Directory to copy the bundle to (artifact upload)",
    )
    parser.add_argument(
        "--overrides",
        nargs="*",
        default=None,
        help="Hydra-style configuration overrides",
    )
    return parser.parse_args()


def _load_incident_runs(paths: Sequence[str] | None) -> Sequence[dict[str, str]]:
    return [json.loads(Path(p).read_text()) for p in paths] if paths else []


def main() -> None:  # pragma: no cover - exercised via tests
    args = _parse_args()
    cfg = load_config(args.overrides)
    pin_environment()

    # Generate reports and compute metrics
    metrics = generate_reports(
        results_path=args.results,
        output_dir=args.output,
        ks=args.ks,
        run_paths=args.runs,
        baseline_path=args.baseline,
        incident_paths=args.incidents,
        bundle_path=args.bundle,
        upload_dir=args.upload,
    )

    # Prepare acceptance evaluation
    incident_runs = _load_incident_runs(args.incidents)
    incident_summary = incident_rates(incident_runs) if incident_runs else {}
    sanitizer_failures = sum(
        status == "sanitizer"
        for run in incident_runs
        for status in run.values()
    )

    acceptance_metrics = {
        "pass@1": metrics.get(1, 0.0),
        "pass@10": metrics.get(10, 0.0),
        "timeout_rate": incident_summary.get("timeout", 0.0),
        "sanitizer_failures": sanitizer_failures,
    }

    criteria = AcceptanceCriteria(
        pass_at_1=cfg.acceptance.pass_at_1,
        pass_at_10=cfg.acceptance.pass_at_10,
        max_timeout_rate=cfg.acceptance.max_timeout_rate,
        max_sanitizer_failures=cfg.acceptance.max_sanitizer_failures,
    )

    results = evaluate_acceptance(acceptance_metrics, criteria)
    print("Acceptance results:")
    for key, value in results.items():
        print(f"{key}: {value}")

    if not results["overall"]:
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

