#!/usr/bin/env python3
"""Minimal smoke evaluation run for Phase 8.

This script exercises the evaluation utilities on a tiny synthetic set of
results. It writes Markdown and HTML reports to an ``artifacts`` directory so
CI can upload them as build artifacts.
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

# Ensure project root on sys.path so `hrm_coder` is importable when run as a script
sys.path.append(str(Path(__file__).resolve().parents[1]))

from hrm_coder.evaluation import (
    aggregate_pass_at_k,
    flaky_tasks,
    html_report,
    markdown_report,
)


def main() -> None:
    # Synthetic results for three tasks with three attempts each.
    results = {
        "task1": [True, False, True],
        "task2": [False, False, False],
        "task3": [True, True, True],
    }
    ks = [1, 2]
    metrics = aggregate_pass_at_k(results, ks)

    # Two deterministic runs to feed into flaky detection.
    runs = [
        {"task1": True, "task2": False, "task3": True},
        {"task1": True, "task2": False, "task3": True},
    ]
    flaky = flaky_tasks(runs)

    artifacts = Path("artifacts")
    artifacts.mkdir(exist_ok=True)
    artifacts.joinpath("metrics.json").write_text(json.dumps(metrics, indent=2))
    artifacts.joinpath("report.md").write_text(markdown_report(metrics, flaky))
    artifacts.joinpath("report.html").write_text(html_report(metrics, flaky))

    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
