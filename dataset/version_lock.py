"""Dataset version locking utilities.

This module computes deterministic hashes of dataset directories and records
 them in a ``versions.yml`` file. The file uses JSON formatting for simplicity
 and is intended to be tracked in version control to ensure reproducible data
 builds.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .determinism import hash_directory


def compute_dataset_hash(dataset_dir: Path) -> str:
    """Return a SHA256 digest for the contents of *dataset_dir*.

    The hash is computed over the relative file paths and their individual
    SHA256 hashes as produced by :func:`hash_directory`.
    """
    mapping = hash_directory(dataset_dir)
    serialized = json.dumps(mapping, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def update_version(
    dataset_name: str, dataset_dir: str, versions_file: str
) -> str:
    """Update *versions_file* with the hash of *dataset_dir*.

    Parameters
    ----------
    dataset_name:
        Name used as the key in the versions file.
    dataset_dir:
        Directory containing the processed dataset.
    versions_file:
        Path to a YAML (JSON-formatted) file mapping dataset names to hashes.
        The file will be created if it does not exist.

    Returns
    -------
    str
        The computed hash for *dataset_dir*.
    """
    dataset_path = Path(dataset_dir)
    digest = compute_dataset_hash(dataset_path)

    versions_path = Path(versions_file)
    versions_path.parent.mkdir(parents=True, exist_ok=True)

    if versions_path.exists():
        versions = json.loads(versions_path.read_text() or "{}")
    else:
        versions = {}

    versions[dataset_name] = digest
    versions_path.write_text(
        json.dumps(versions, indent=2, sort_keys=True), encoding="utf-8"
    )
    return digest


def verify_version(
    dataset_name: str, dataset_dir: str, versions_file: str
) -> bool:
    """Check that *dataset_dir* matches the hash in *versions_file*.

    Parameters
    ----------
    dataset_name:
        Name of the dataset entry in the versions file.
    dataset_dir:
        Directory containing the processed dataset to verify.
    versions_file:
        Path to the versions file previously written by
        :func:`update_version`.

    Returns
    -------
    bool
        ``True`` if the dataset's current hash equals the recorded hash,
        ``False`` otherwise. ``False`` is also returned when the versions
        file or dataset entry does not exist.
    """

    versions_path = Path(versions_file)
    if not versions_path.exists():
        return False

    versions = json.loads(versions_path.read_text() or "{}")
    recorded = versions.get(dataset_name)
    if recorded is None:
        return False

    current = compute_dataset_hash(Path(dataset_dir))
    return current == recorded


def verify_catalog_versions(
    catalog_path: str, datasets_root: str, versions_file: str
) -> bool:
    """Verify that all datasets in *catalog_path* match recorded hashes.

    This helper loads a dataset catalog (same format as
    ``docs/dataset_catalog.json``) and ensures that each listed dataset has a
    corresponding entry in ``versions_file`` that matches the current contents
    of ``datasets_root/<name>``. Unknown catalog entries are ignored.

    Parameters
    ----------
    catalog_path:
        Path to the dataset catalog JSON file.
    datasets_root:
        Directory containing one subdirectory per dataset as produced by
        :mod:`dataset.build_from_catalog`.
    versions_file:
        Path to the versions file previously written by
        :func:`update_version`.

    Returns
    -------
    bool
        ``True`` if all datasets verify successfully, ``False`` otherwise.
    """

    from .build_from_catalog import BUILDERS  # local import to avoid cycle

    catalog = json.loads(Path(catalog_path).read_text() or "[]")
    root = Path(datasets_root)

    all_ok = True
    for entry in catalog:
        name = entry.get("name")
        builder_entry = BUILDERS.get(name)
        if not builder_entry:
            continue

        _, version_key = builder_entry
        ds_dir = root / name
        if not verify_version(version_key, str(ds_dir), versions_file):
            all_ok = False

    return all_ok


if __name__ == "__main__":  # pragma: no cover - convenience CLI
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Verify dataset versions for all entries in a catalog"
    )
    parser.add_argument("catalog", help="Path to dataset_catalog.json")
    parser.add_argument(
        "datasets_root", help="Directory containing built datasets"
    )
    parser.add_argument(
        "--versions", required=True, help="Path to versions.yml file"
    )
    args = parser.parse_args()

    ok = verify_catalog_versions(
        args.catalog, args.datasets_root, args.versions
    )
    sys.exit(0 if ok else 1)
