#!/usr/bin/env python3
"""Generate dataset catalog with license and SHA256 hashes.

This script enumerates key datasets and records their licensing
information and content hashes when available. The resulting catalog is
written to ``docs/dataset_catalog.json`` to support Phase 0 tracking.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

DATASETS = [
    {"name": "Codeforces-Intro", "path": Path("dataset/raw-data/codeforces_intro"), "license": "TBD"},
    {"name": "AtCoder-ABC", "path": Path("dataset/raw-data/atcoder_abc"), "license": "TBD"},
    {"name": "Kattis-micro", "path": Path("dataset/raw-data/kattis_micro"), "license": "TBD"},
    {"name": "HumanEval-CPP", "path": Path("dataset/raw-data/humaneval_cpp.jsonl"), "license": "MIT"},
]


def sha256_of_path(path: Path) -> str | None:
    """Return the SHA256 hash of ``path`` or ``None`` if it does not exist."""
    if not path.exists():
        return None
    hash_obj = hashlib.sha256()
    if path.is_file():
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                hash_obj.update(chunk)
    else:
        for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
            hash_obj.update(file_path.relative_to(path).as_posix().encode())
            with file_path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    hash_obj.update(chunk)
    return hash_obj.hexdigest()


def build_catalog() -> List[Dict[str, Any]]:
    catalog: List[Dict[str, Any]] = []
    for ds in DATASETS:
        path = ds["path"]
        digest = sha256_of_path(path)
        catalog.append(
            {
                "name": ds["name"],
                "license": ds["license"],
                "path": str(path),
                "sha256": digest or "TBD",
            }
        )
    return catalog


def main() -> None:
    catalog = build_catalog()
    out_path = Path("docs/dataset_catalog.json")
    out_path.write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
