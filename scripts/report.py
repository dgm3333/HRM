#!/usr/bin/env python3
"""Generate evaluation reports from results JSON.

This lightweight wrapper feeds the Phase 7 reporting utilities so that
Phase 1 scaffolding can produce basic Markdown/HTML summaries.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from hrm_coder.evaluation import generate_reports


def main() -> None:  # pragma: no cover - simple CLI
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "results",
        type=Path,
        help="JSON file mapping task id to a list of attempt outcomes",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Directory to write generated reports",
    )
    parser.add_argument(
        "--k",
        dest="ks",
        type=int,
        nargs="*",
        default=[1, 10],
        help="k values for pass@k computation",
    )
    args = parser.parse_args()
    generate_reports(
        results_path=args.results,
        output_dir=args.output,
        ks=args.ks,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
