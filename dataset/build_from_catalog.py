"""Dataset build orchestration from a catalog.

This utility reads a dataset catalog JSON file and invokes the
appropriate builder for each listed dataset.  It optionally verifies
deterministic outputs and records hashes in a versions file, which
helps progress Phase 3's reproducible dataset pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict

from .build_atcoder_abc_dataset import build_dataset as build_atcoder
from .build_codeforces_intro_dataset import build_dataset as build_codeforces
from .build_humaneval_cpp_dataset import build_dataset as build_humaneval
from .build_kattis_micro_dataset import build_dataset as build_kattis
from .determinism import validate_build_determinism

# Map human-friendly dataset names to their builder functions.
BUILDERS: Dict[str, Callable[[str, str, int, str | None], None]] = {
    "HumanEval-CPP": build_humaneval,
    "Codeforces-Intro": build_codeforces,
    "AtCoder-ABC": build_atcoder,
    "Kattis-micro": build_kattis,
}


def build_from_catalog(
    catalog_path: str,
    output_root: str,
    versions_file: str,
    *,
    seed: int = 0,
    check_determinism: bool = True,
) -> None:
    """Build datasets listed in *catalog_path* into *output_root*.

    Parameters
    ----------
    catalog_path:
        Path to a JSON file following the format of
        ``docs/dataset_catalog.json``.
    output_root:
        Directory where processed datasets will be written. One
        subdirectory per dataset name is created.
    versions_file:
        Path to ``versions.yml`` where dataset hashes are recorded.
    seed:
        Random seed forwarded to each builder.
    check_determinism:
        If ``True``, the builder is run twice in temporary directories
        to confirm deterministic outputs before writing to ``output_root``.
    """

    catalog = json.loads(Path(catalog_path).read_text())
    out_root = Path(output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    for entry in catalog:
        name = entry.get("name")
        raw_path = entry.get("path")
        build_fn = BUILDERS.get(name)

        if not build_fn or raw_path is None:
            # Unknown dataset or missing path; skip silently for now.
            continue

        dataset_dir = out_root / name

        if check_determinism:
            validate_build_determinism(
                lambda rp, od, sd: build_fn(rp, od, sd), raw_path, seed=seed
            )

        build_fn(
            raw_path,
            str(dataset_dir),
            seed=seed,
            versions_path=versions_file,
        )


if __name__ == "__main__":  # pragma: no cover - CLI wrapper
    import argparse

    parser = argparse.ArgumentParser(
        description="Build one or more datasets defined in a catalog"
    )
    parser.add_argument("catalog", help="Path to dataset_catalog.json")
    parser.add_argument(
        "output_root", help="Directory to write processed datasets into"
    )
    parser.add_argument(
        "--versions",
        required=True,
        help="Path to versions.yml for hash locking",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Random seed for splits"
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Skip deterministic build check",
    )

    args = parser.parse_args()

    build_from_catalog(
        args.catalog,
        args.output_root,
        args.versions,
        seed=args.seed,
        check_determinism=not args.no_check,
    )
