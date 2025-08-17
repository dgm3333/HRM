from __future__ import annotations

"""Generate a dvc.yaml stage for dataset builds."""

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataset.dvc import write_dvc_yaml  # noqa: E402

DEFAULT_CATALOG = Path("docs/dataset_catalog.json")
DEFAULT_OUTPUT = Path("data/processed")
DEFAULT_VERSIONS = Path("data/versions.yml")
DEFAULT_DVC_YAML = Path("dvc.yaml")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a dvc.yaml stage for building datasets",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="Path to dataset_catalog.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory for processed datasets",
    )
    parser.add_argument(
        "--versions",
        type=Path,
        default=DEFAULT_VERSIONS,
        help="Path to versions.yml with dataset hashes",
    )
    parser.add_argument(
        "--yaml",
        type=Path,
        default=DEFAULT_DVC_YAML,
        help="Where to write the generated dvc.yaml",
    )
    parser.add_argument(
        "--stage-name",
        default="build-datasets",
        help="Name of the generated DVC stage",
    )
    args = parser.parse_args()

    write_dvc_yaml(
        str(args.catalog),
        str(args.output),
        str(args.versions),
        yaml_path=str(args.yaml),
        stage_name=args.stage_name,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
