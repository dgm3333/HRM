"""Loader for HumanEval-CPP dataset with schema validation.

This module reads a processed HumanEval-CPP dataset directory and
returns structured objects for each task.  It validates that the
expected files are present in every task directory and uses
``pydantic`` models to enforce the schema.  The loader is intended for
Phase 3 where dataset schemas require explicit contracts and unit
 tests.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel


class HumanEvalCPPRecord(BaseModel):
    """Represents a single HumanEval-CPP task."""

    task_id: str
    prompt: str
    test: str
    reference_solution: Optional[str]
    split: str


def _load_task(task_dir: Path, split: str) -> HumanEvalCPPRecord:
    """Load a single task located at *task_dir*.

    Parameters
    ----------
    task_dir:
        Path to the task directory containing ``prompt.cpp`` and
        ``tests.cpp`` files.  ``reference.cpp`` is optional.
    split:
        Name of the dataset split (``train``, ``val`` or ``test``).
    """
    prompt_path = task_dir / "prompt.cpp"
    tests_path = task_dir / "tests.cpp"
    if not prompt_path.exists() or not tests_path.exists():
        missing = []
        if not prompt_path.exists():
            missing.append("prompt.cpp")
        if not tests_path.exists():
            missing.append("tests.cpp")
        raise FileNotFoundError(
            f"Missing required files in {task_dir}: {', '.join(missing)}"
        )

    reference_path = task_dir / "reference.cpp"
    reference = reference_path.read_text() if reference_path.exists() else None

    return HumanEvalCPPRecord(
        task_id=task_dir.name,
        prompt=prompt_path.read_text(),
        test=tests_path.read_text(),
        reference_solution=reference,
        split=split,
    )


def load_dataset(root: str | Path) -> Dict[str, List[HumanEvalCPPRecord]]:
    """Load all tasks from a processed HumanEval-CPP dataset.

    The function expects the directory layout produced by
    ``build_humaneval_cpp_dataset.py`` and returns a mapping of split
    name to a list of ``HumanEvalCPPRecord`` objects.
    """
    root_path = Path(root)
    splits: Dict[str, List[HumanEvalCPPRecord]] = {"train": [], "val": [], "test": []}
    for split in splits:
        split_dir = root_path / split
        if not split_dir.exists():
            continue
        for task_dir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
            record = _load_task(task_dir, split)
            splits[split].append(record)
    return splits
