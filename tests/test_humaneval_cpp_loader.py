from pathlib import Path
import json
import pytest

from dataset.build_humaneval_cpp_dataset import build_dataset
from dataset.humaneval_cpp_loader import HumanEvalCPPRecord, load_dataset


def _write_sample_dataset(path: Path) -> None:
    tasks = [
        {
            "task_id": "task1",
            "prompt": "int add(int a,int b){return a+b;}\n",
            "test": "#include <cassert>\nint main(){assert(add(1,2)==3);}\n",
            "reference_solution": "int add(int a,int b){return a+b;}\n",
        },
        {
            "task_id": "task2",
            "prompt": "int sub(int a,int b){return a-b;}\n",
            "test": "#include <cassert>\nint main(){assert(sub(3,1)==2);}\n",
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
    first = next(t for t in all_tasks if t.task_id == "task1")
    assert isinstance(first, HumanEvalCPPRecord)
    assert "add" in first.prompt


def test_loader_missing_files(tmp_path):
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)
    out_dir = tmp_path / "out"
    build_dataset(str(raw), str(out_dir), seed=0)

    # remove tests.cpp from one task to trigger error
    task_dir = next((out_dir / "train").iterdir())
    (task_dir / "tests.cpp").unlink()
    with pytest.raises(FileNotFoundError):
        load_dataset(out_dir)
