#!/usr/bin/env python3
"""Minimal smoke evaluation script for CI.

This script exercises the evaluation harness on a small
synthetic set of task results.  It generates a report and
bundles the artifacts so CI can upload them.
"""
from __future__ import annotations

import pathlib

import sys

# Ensure repository root is on the import path when executed directly.
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from utils import eval_harness  # noqa: E402


def main() -> None:
    # Synthetic results: two tasks with a couple of candidate outcomes.
    task_results = {
        "task_a": [True, False, False],
        "task_b": [False, False],
    }
    metrics = {
        "pass@1": eval_harness.compute_pass_at_k(task_results, k=1),
        "pass@10": eval_harness.compute_pass_at_k(task_results, k=10),
    }

    out_dir = pathlib.Path("smoke_eval")
    out_dir.mkdir(exist_ok=True)

    report_path = out_dir / "report.json"
    eval_harness.generate_report(metrics, str(report_path))

    # Bundle and "upload" to a local directory for CI artifact collection.
    bundle_path = out_dir / "artifacts.zip"
    upload_dir = out_dir / "upload"
    eval_harness.bundle_and_upload(
        [str(report_path)], str(bundle_path), str(upload_dir)
    )


if __name__ == "__main__":
    main()
