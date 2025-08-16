import json
from pathlib import Path

import pytest

from dataset.build_codeforces_intro_dataset import build_dataset
from dataset.codeforces_intro_loader import CodeforcesRecord, load_dataset


def _write_sample_dataset(path: Path) -> None:
    tasks = [
        {
            "task_id": "cf1",
            "prompt": "Sum two numbers",
            "tests": [{"input": "1 2\n", "output": "3\n"}],
            "time_limit_ms": 1000,
            "memory_limit_kb": 65536,
        },
        {
            "task_id": "cf2",
            "prompt": "Subtract numbers",
            "tests": [{"input": "3 1\n", "output": "2\n"}],
        },
    ]
    with path.open("w") as fh:
        for t in tasks:
            json.dump(t, fh)
            fh.write("\n")


def test_loader_round_trip(tmp_path):
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)
    out_dir = tmp_path / "out"
    build_dataset(str(raw), str(out_dir), seed=0)

    splits = load_dataset(out_dir)
    assert set(splits.keys()) == {"train", "val", "test"}
    all_tasks = [t for tasks in splits.values() for t in tasks]
    assert len(all_tasks) == 2
    first = next(t for t in all_tasks if t.task_id == "cf1")
    assert isinstance(first, CodeforcesRecord)
    assert first.tests[0].output.strip() == "3"


def test_loader_missing_meta(tmp_path):
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)
    out_dir = tmp_path / "out"
    build_dataset(str(raw), str(out_dir), seed=0)

    # remove meta.json from one task to trigger error
    task_dir = next((out_dir / "train").iterdir())
    (task_dir / "meta.json").unlink()
    with pytest.raises(FileNotFoundError):
        load_dataset(out_dir)
