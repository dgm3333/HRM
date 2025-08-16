"""Builder for the Kattis micro dataset.

This builder expects a JSONL file where each line describes a single
Kattis-style programming problem. Each record follows the
:class:`dataset.schemas.KattisRecord` schema with fields:

- ``task_id``: unique identifier for the problem
- ``prompt``: textual description or starter code
- ``tests``: list of input/output pairs
- ``time_limit_ms``: optional time limit in milliseconds (default 2000)
- ``memory_limit_kb``: optional memory limit in kilobytes (default 256000)

The script splits tasks deterministically into train/val/test subsets and
writes each task to ``output_dir/<split>/<task_id>/``. The directory layout
mirrors the Codeforces and AtCoder builders so downstream tools can reuse the
same I/O judging infrastructure.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import List

from .schemas import KattisRecord
from .split_manager import split_list
from .version_lock import update_version


@dataclass
class IOPair:
    input: str
    output: str


@dataclass
class KattisTask:
    task_id: str
    prompt: str
    tests: List[IOPair]
    time_limit_ms: int = 2000
    memory_limit_kb: int = 256000


def load_tasks(path: Path) -> List[KattisTask]:
    """Load tasks from a JSONL file using :class:`KattisRecord`."""

    tasks: List[KattisTask] = []
    with path.open() as fh:
        for line in fh:
            record = KattisRecord.model_validate_json(line)
            tests = [
                IOPair(input=io.input, output=io.output) for io in record.tests
            ]
            tasks.append(
                KattisTask(
                    task_id=record.task_id,
                    prompt=record.prompt,
                    tests=tests,
                    time_limit_ms=record.time_limit_ms,
                    memory_limit_kb=record.memory_limit_kb,
                )
            )
    return tasks


def write_task(task: KattisTask, dest: Path) -> None:
    """Write ``task`` into ``dest`` directory."""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "prompt.txt").write_text(task.prompt)

    tests_dir = dest / "tests"
    tests_dir.mkdir(exist_ok=True)
    for idx, io in enumerate(task.tests):
        (tests_dir / f"{idx}.in").write_text(io.input)
        (tests_dir / f"{idx}.out").write_text(io.output)

    meta = {
        "time_limit_ms": task.time_limit_ms,
        "memory_limit_kb": task.memory_limit_kb,
    }
    (dest / "meta.json").write_text(json.dumps(meta))


DATASET_NAME = "kattis_micro"


def build_dataset(
    raw_path: str,
    output_dir: str,
    seed: int = 0,
    versions_path: str | None = None,
) -> None:
    """Entry point for converting raw Kattis data into structured tasks."""
    tasks = load_tasks(Path(raw_path))
    splits = split_list(tasks, seed)

    out_dir = Path(output_dir)
    for split_name, subset in splits.items():
        for task in subset:
            write_task(task, out_dir / split_name / task.task_id)

    if versions_path is not None:
        update_version(DATASET_NAME, str(out_dir), versions_path)


if __name__ == "__main__":  # pragma: no cover - CLI wrapper
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Kattis micro dataset"
    )
    parser.add_argument("raw_path", help="Path to raw JSONL dataset")
    parser.add_argument(
        "output_dir",
        help="Output directory for processed dataset",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Random seed for splits"
    )
    parser.add_argument(
        "--versions", help="Path to versions.yml for hash locking"
    )
    args = parser.parse_args()

    build_dataset(
        args.raw_path,
        args.output_dir,
        seed=args.seed,
        versions_path=args.versions,
    )
