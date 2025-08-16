"""Builder for the Codeforces-Intro dataset.

This builder expects a JSONL file where each line describes a single
Codeforces-style problem with the following fields:

- ``task_id``: unique identifier
- ``prompt``: problem statement or description
- ``tests``: list of input/output pairs, e.g.,
  ``{"input": "1 2\n", "output": "3\n"}``
- ``time_limit_ms``: optional time limit in milliseconds (default 2000)
- ``memory_limit_kb``: optional memory limit in kilobytes (default 256000)

The script splits the tasks deterministically into train/val/test
subsets and writes each task to ``output_dir/<split>/<task_id>/``. Each
task directory contains:

- ``prompt.txt`` -- the textual problem statement
- ``tests/`` -- directory of numbered ``*.in``/``*.out`` files
- ``meta.json`` -- metadata such as time and memory limits
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import List

from .split_manager import split_list


@dataclass
class IOPair:
    input: str
    output: str


@dataclass
class CodeforcesTask:
    task_id: str
    prompt: str
    tests: List[IOPair]
    time_limit_ms: int = 2000
    memory_limit_kb: int = 256000


def load_tasks(path: Path) -> List[CodeforcesTask]:
    tasks: List[CodeforcesTask] = []
    with path.open() as fh:
        for line in fh:
            raw = json.loads(line)
            tests = [IOPair(**t) for t in raw["tests"]]
            tasks.append(
                CodeforcesTask(
                    task_id=raw["task_id"],
                    prompt=raw["prompt"],
                    tests=tests,
                    time_limit_ms=raw.get("time_limit_ms", 2000),
                    memory_limit_kb=raw.get("memory_limit_kb", 256000),
                )
            )
    return tasks


def write_task(task: CodeforcesTask, dest: Path) -> None:
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


def build_dataset(raw_path: str, output_dir: str, seed: int = 0) -> None:
    tasks = load_tasks(Path(raw_path))
    splits = split_list(tasks, seed)

    out_dir = Path(output_dir)
    for split_name, subset in splits.items():
        for task in subset:
            write_task(task, out_dir / split_name / task.task_id)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Codeforces-Intro dataset")
    parser.add_argument("raw_path", help="Path to raw JSONL dataset")
    parser.add_argument("output_dir", help="Output directory for processed dataset")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for deterministic splits")
    args = parser.parse_args()

    build_dataset(args.raw_path, args.output_dir, args.seed)
