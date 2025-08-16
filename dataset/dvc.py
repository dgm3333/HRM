"""Helpers for generating DVC pipeline files for dataset builds.

This module provides a tiny utility for writing a ``dvc.yaml`` stage
that invokes :mod:`dataset.build_from_catalog`.  It is part of Phase 3
work toward a deterministic dataset pipeline with data version locks.
"""
from __future__ import annotations

from pathlib import Path
from typing import List


def generate_stage_yaml(
    catalog_path: str,
    output_dir: str,
    versions_file: str,
    *,
    stage_name: str = "build-datasets",
) -> str:
    """Return YAML for a DVC stage building datasets from a catalog.

    Parameters
    ----------
    catalog_path:
        Path to ``dataset_catalog.json``.
    output_dir:
        Directory where processed datasets will be written.
    versions_file:
        Path to ``versions.yml`` recording dataset hashes.
    stage_name:
        Name for the generated DVC stage. Defaults to ``"build-datasets"``.
    """
    cmd = (
        f"python -m dataset.build_from_catalog {catalog_path} "
        f"{output_dir} --versions {versions_file}"
    )

    lines: List[str] = [
        "stages:",
        f"  {stage_name}:",
        f"    cmd: {cmd}",
        "    deps:",
        f"      - {catalog_path}",
        "      - dataset/build_from_catalog.py",
        "    outs:",
        f"      - {output_dir}",
        f"      - {versions_file}",
    ]
    return "\n".join(lines) + "\n"


def write_dvc_yaml(
    catalog_path: str,
    output_dir: str,
    versions_file: str,
    *,
    yaml_path: str = "dvc.yaml",
    stage_name: str = "build-datasets",
) -> None:
    """Write a ``dvc.yaml`` file with a single dataset build stage."""
    content = generate_stage_yaml(
        catalog_path, output_dir, versions_file, stage_name=stage_name
    )
    path = Path(yaml_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
