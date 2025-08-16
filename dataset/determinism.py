"""Helpers for verifying dataset build determinism.

This module provides utilities to hash dataset directories and to
validate that running a dataset build function with the same seed
produces identical artifacts.  It is intended for Phase 3 where a
stable dataset pipeline is required.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Dict
import tempfile


def _hash_file(path: Path) -> str:
    """Return the SHA256 hash of *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_directory(directory: Path) -> Dict[str, str]:
    """Hash all files under *directory* recursively.

    Returns a mapping of relative file paths (POSIX style) to their
    SHA256 hex digest.  The resulting dictionary can be compared across
    runs to ensure deterministic outputs.
    """
    hashes: Dict[str, str] = {}
    for file_path in sorted(p for p in directory.rglob("*") if p.is_file()):
        rel = file_path.relative_to(directory).as_posix()
        hashes[rel] = _hash_file(file_path)
    return hashes


def validate_build_determinism(
    build_fn: Callable[[str, str, int], None], raw_path: str, seed: int = 0
) -> bool:
    """Run *build_fn* twice and verify identical outputs.

    Parameters
    ----------
    build_fn:
        Callable accepting ``(raw_path, output_dir, seed)``. It should
        write the processed dataset to ``output_dir``.
    raw_path:
        Path to the raw dataset used by ``build_fn``.
    seed:
        Seed forwarded to ``build_fn`` to control randomness.

    Returns
    -------
    bool
        ``True`` if both runs produced identical directory hashes,
        ``False`` otherwise.
    """
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        build_fn(raw_path, d1, seed)
        build_fn(raw_path, d2, seed)
        return hash_directory(Path(d1)) == hash_directory(Path(d2))
