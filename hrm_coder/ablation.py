from __future__ import annotations

"""Utilities for generating ablation comparison reports.

This module provides a small helper used in Phase 9 of the HRM Coder
roadmap.  It compares evaluation metrics from a current run against a
baseline (typically the token-based model) and writes a report whose format
is inferred from the output file extension.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Optional

from .evaluation import (
    compare_to_baseline,
    comparison_html_report,
    comparison_markdown_report,
)


def generate_ablation_report(
    current_metrics_path: str, baseline_metrics_path: str, output_path: str
) -> Dict[str, Dict[str, Optional[float]]]:
    """Generate a comparison report between ``current`` and ``baseline``.

    Parameters
    ----------
    current_metrics_path:
        Path to a JSON file containing metrics from the current run.
    baseline_metrics_path:
        Path to a JSON file with baseline metrics.
    output_path:
        Destination for the generated report.  The format is determined by the
        file extension: ``.md`` for Markdown, ``.html``/``.htm`` for HTML and
        JSON otherwise.
    """

    current = json.loads(Path(current_metrics_path).read_text())
    comparison = compare_to_baseline(current, baseline_metrics_path)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".md":
        out.write_text(comparison_markdown_report(comparison))
    elif out.suffix.lower() in {".html", ".htm"}:
        out.write_text(comparison_html_report(comparison))
    else:
        out.write_text(json.dumps(comparison))
    return comparison


def main() -> None:  # pragma: no cover - CLI entry point
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "current", help="JSON file with metrics from current run"
    )
    parser.add_argument(
        "baseline", help="JSON file with baseline metrics"
    )
    parser.add_argument(
        "output",
        help="Path to write comparison report (extension determines format)",
    )
    args = parser.parse_args()
    generate_ablation_report(args.current, args.baseline, args.output)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
