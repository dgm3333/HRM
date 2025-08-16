import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from dataset.build_kattis_micro_dataset import build_dataset  # noqa: E402
from dataset.determinism import validate_build_determinism  # noqa: E402


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


def test_kattis_micro_build_is_deterministic(tmp_path):
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)

    assert validate_build_determinism(build_dataset, str(raw), seed=123)
