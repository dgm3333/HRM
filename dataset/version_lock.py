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
