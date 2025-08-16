"""Utility to generate the hrm-coder project skeleton."""
from __future__ import annotations

import argparse
from pathlib import Path

# Directory layout inspired by docs/hrmCoder_plan.md
LAYOUT = [
    "conf",
    "docker",
    "hrm",
    "runners",
    "cpp/harness",
    "cpp/cmake",
    "datasets",
    "orchestration",
    "scripts",
    "tests",
    "reports",
    "docs",
]


def create_scaffold(root: Path) -> None:
    """Create the directory tree under ``root``.

    Existing directories are left untouched.
    """
    for rel_path in LAYOUT:
        path = root / rel_path
        path.mkdir(parents=True, exist_ok=True)



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", type=Path, nargs="?", default=Path("hrm-coder"), help="Root path for scaffold"
    )
    args = parser.parse_args()
    create_scaffold(args.root)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
