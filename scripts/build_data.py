from __future__ import annotations

"""Build processed datasets from the repository catalog."""

import argparse
from pathlib import Path

from dataset.build_from_catalog import build_from_catalog

DEFAULT_CATALOG = Path("docs/dataset_catalog.json")
DEFAULT_OUTPUT = Path("data/processed")
DEFAULT_VERSIONS = Path("data/versions.yml")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build datasets defined in docs/dataset_catalog.json",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="Path to the dataset catalog JSON file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory to write processed datasets into",
    )
    parser.add_argument(
        "--versions",
        type=Path,
        default=DEFAULT_VERSIONS,
        help="Path to versions.yml for hash locking",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed forwarded to dataset builders",
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Skip deterministic build validation",
    )
    args = parser.parse_args()

    build_from_catalog(
        str(args.catalog),
        str(args.output),
        str(args.versions),
        seed=args.seed,
        check_determinism=not args.no_check,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
