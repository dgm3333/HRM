import json
from pathlib import Path

from dataset.build_codeforces_intro_dataset import build_dataset
from dataset.determinism import validate_build_determinism


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


def test_codeforces_intro_build_is_deterministic(tmp_path):
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)

    assert validate_build_determinism(build_dataset, str(raw), seed=123)
