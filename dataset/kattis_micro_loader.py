"""Loader for the processed Kattis micro dataset.

This module reads a dataset directory produced by
``build_kattis_micro_dataset.py`` and returns structured objects for each
task.  It validates required files and uses ``pydantic`` models to enforce the
schema.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel


class IOPair(BaseModel):
    """Container for a single input/output example."""

    input: str
    output: str


class KattisRecord(BaseModel):
    """Represents one Kattis micro task."""

    task_id: str
    prompt: str
    tests: List[IOPair]
    time_limit_ms: int
    memory_limit_kb: int
    split: str


def _load_task(task_dir: Path, split: str) -> KattisRecord:
    """Load a single task from ``task_dir``."""
    prompt_path = task_dir / "prompt.txt"
    tests_dir = task_dir / "tests"
    meta_path = task_dir / "meta.json"
    missing = [
        p.name for p in [prompt_path, tests_dir, meta_path] if not p.exists()
    ]
    if missing:
        raise FileNotFoundError(
            f"Missing required paths in {task_dir}: {', '.join(missing)}"
        )

    prompt = prompt_path.read_text()
    meta = json.loads(meta_path.read_text())

    tests: List[IOPair] = []
    for in_file in sorted(tests_dir.glob("*.in")):
        out_file = in_file.with_suffix(".out")
        if not out_file.exists():
            raise FileNotFoundError(f"Missing expected output file {out_file}")
        tests.append(
            IOPair(input=in_file.read_text(), output=out_file.read_text())
        )

    return KattisRecord(
        task_id=task_dir.name,
        prompt=prompt,
        tests=tests,
        time_limit_ms=meta.get("time_limit_ms", 2000),
        memory_limit_kb=meta.get("memory_limit_kb", 256000),
        split=split,
    )


def load_dataset(root: str | Path) -> Dict[str, List[KattisRecord]]:
    """Load all tasks from a processed Kattis micro dataset."""
    root_path = Path(root)
    splits: Dict[str, List[KattisRecord]] = {
        "train": [],
        "val": [],
        "test": [],
    }
    for split in splits:
        split_dir = root_path / split
        if not split_dir.exists():
            continue
        for task_dir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
            record = _load_task(task_dir, split)
            splits[split].append(record)
    return splits
