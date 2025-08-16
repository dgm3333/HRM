import json
from pathlib import Path
import sys

import pytest

# Ensure repository root is on import path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataset.build_atcoder_abc_dataset import build_dataset  # noqa: E402
from dataset.atcoder_abc_loader import (  # noqa: E402
    AtCoderRecord,
    load_dataset,
)


def _write_sample_dataset(path: Path) -> None:
    tasks = [
        {
            "task_id": "abc001",
            "prompt": "Echo input",
            "tests": [{"input": "42\n", "output": "42\n"}],
            "time_limit_ms": 2000,
            "memory_limit_kb": 65536,
        },
        {
            "task_id": "abc002",
            "prompt": "Add numbers",
            "tests": [{"input": "1 2\n", "output": "3\n"}],
        },
    ]
    with path.open("w") as fh:
        for t in tasks:
            json.dump(t, fh)
            fh.write("\n")


def test_loader_round_trip(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)
    out_dir = tmp_path / "out"
    build_dataset(str(raw), str(out_dir), seed=0)

    splits = load_dataset(out_dir)
    assert set(splits.keys()) == {"train", "val", "test"}
    all_tasks = [t for tasks in splits.values() for t in tasks]
    assert len(all_tasks) == 2
    first = next(t for t in all_tasks if t.task_id == "abc001")
    assert isinstance(first, AtCoderRecord)
    assert first.tests[0].output.strip() == "42"


def test_loader_missing_meta(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)
    out_dir = tmp_path / "out"
    build_dataset(str(raw), str(out_dir), seed=0)

    # remove meta.json from one task to trigger error
    task_dir = next((out_dir / "train").iterdir())
    (task_dir / "meta.json").unlink()
    with pytest.raises(FileNotFoundError):
        load_dataset(out_dir)
