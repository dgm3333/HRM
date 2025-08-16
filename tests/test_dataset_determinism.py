import json
from pathlib import Path

from dataset.build_humaneval_cpp_dataset import build_dataset
from dataset.determinism import validate_build_determinism


def _write_sample_dataset(path: Path) -> None:
    tasks = [
        {
            "task_id": "task1",
            "prompt": "int add(int a,int b){return a+b;}\n",
            "test": "#include <cassert>\nint main(){assert(add(1,2)==3);}\n",
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


def test_humaneval_cpp_build_is_deterministic(tmp_path):
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)

    assert validate_build_determinism(build_dataset, str(raw), seed=0)
