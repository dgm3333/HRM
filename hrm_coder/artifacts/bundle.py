from __future__ import annotations

"""Utility helpers for bundling and uploading evaluation artifacts."""

from pathlib import Path
from typing import Sequence
import tarfile
import shutil


def bundle_artifacts(files: Sequence[str], bundle_path: str) -> str:
    """Create a gzipped tarball containing the given files.

    Parameters
    ----------
    files:
        Iterable of file paths to include in the archive. Non-existent
        paths are ignored.
    bundle_path:
        Destination path for the ``.tar.gz`` archive.

    Returns
    -------
    str
        The path to the created bundle.
    """

    bundle = Path(bundle_path)
    bundle.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle, "w:gz") as tar:
        for f in files:
            p = Path(f)
            if p.exists():
                tar.add(p, arcname=p.name)
    return str(bundle)


def upload_bundle(bundle_path: str, destination_dir: str) -> str:
    """Copy a bundle to a destination directory.

    This is a light-weight stand-in for uploading artifacts to remote
    storage.  It simply copies ``bundle_path`` into ``destination_dir`` and
    returns the path to the copied file.
    """

    bundle = Path(bundle_path)
    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / bundle.name
    shutil.copy2(bundle, dest)
    return str(dest)
