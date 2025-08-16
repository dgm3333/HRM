import json
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from dataset.build_kattis_micro_dataset import build_dataset  # noqa: E402
from dataset.kattis_micro_loader import (  # noqa: E402
    KattisRecord,
    load_dataset,
)


def _write_sample_dataset(path: Path) -> None:
    tasks = [
        {
            "task_id": "kt1",
            "prompt": "Echo input",
            "tests": [{"input": "1\n", "output": "1\n"}],
            "time_limit_ms": 1000,
            "memory_limit_kb": 65536,
        },
        {
            "task_id": "kt2",
            "prompt": "Add numbers",
            "tests": [{"input": "1 2\n", "output": "3\n"}],
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
    first = next(t for t in all_tasks if t.task_id == "kt1")
    assert isinstance(first, KattisRecord)
    assert first.tests[0].output.strip() == "1"


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
