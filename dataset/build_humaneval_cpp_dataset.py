"""Builder for the HumanEval-CPP dataset.

The real dataset will contain C++ translation of the original
HumanEval tasks.  This builder expects a JSONL file with the
following fields per line:

- ``task_id``: unique identifier
- ``prompt``: problem statement or starter code (C++)
- ``test``: unit tests or I/O harness in C++
- ``reference_solution``: canonical C++ solution (optional)

The script splits the tasks deterministically into train/val/test
subsets and writes each task to ``output_dir/<split>/<task_id>/``.
The layout is intentionally simple so later phases can plug in
CMake/GoogleTest harness generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .schemas import HumanEvalCPPRecord
from .split_manager import split_list


@dataclass
class HumanEvalCPPTask:
    task_id: str
    prompt: str
    test: str
    reference_solution: str | None = None


def load_tasks(path: Path) -> List[HumanEvalCPPTask]:
    """Load tasks from a JSONL file using the HumanEvalCPPRecord schema."""

    tasks: List[HumanEvalCPPTask] = []
    with path.open() as fh:
        for line in fh:
            record = HumanEvalCPPRecord.model_validate_json(line)
            tasks.append(
                HumanEvalCPPTask(
                    task_id=record.task_id,
                    prompt=record.prompt,
                    test=record.test,
                    reference_solution=record.reference_solution,
                )
            )
    return tasks


def write_task(task: HumanEvalCPPTask, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "prompt.cpp").write_text(task.prompt)
    (dest / "tests.cpp").write_text(task.test)
    if task.reference_solution:
        (dest / "reference.cpp").write_text(task.reference_solution)


def build_dataset(raw_path: str, output_dir: str, seed: int = 0) -> None:
    """Entry point for dataset conversion."""
    tasks = load_tasks(Path(raw_path))
    splits = split_list(tasks, seed)

    out_dir = Path(output_dir)
    for split_name, subset in splits.items():
        for task in subset:
            write_task(task, out_dir / split_name / task.task_id)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build HumanEval-CPP dataset"
    )
    parser.add_argument(
        "raw_path", help="Path to raw JSONL dataset"
    )
    parser.add_argument(
        "output_dir", help="Output directory for processed dataset"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for deterministic splits",
    )
    args = parser.parse_args()

    build_dataset(args.raw_path, args.output_dir, args.seed)
