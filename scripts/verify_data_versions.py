from __future__ import annotations

"""Verify processed dataset hashes against the recorded versions file."""

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataset.version_lock import verify_catalog_versions  # noqa: E402

DEFAULT_CATALOG = Path("docs/dataset_catalog.json")
DEFAULT_DATA = Path("data/processed")
DEFAULT_VERSIONS = Path("data/versions.yml")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify dataset hashes match entries in versions.yml",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="Path to dataset_catalog.json",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA,
        help="Root directory containing processed datasets",
    )
    parser.add_argument(
        "--versions",
        type=Path,
        default=DEFAULT_VERSIONS,
        help="Path to versions.yml with recorded hashes",
    )
    args = parser.parse_args()

    ok = verify_catalog_versions(
        str(args.catalog), str(args.data), str(args.versions)
    )
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
