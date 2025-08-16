import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from dataset.build_atcoder_abc_dataset import build_dataset as build_atcoder  # noqa: E402


def _write_sample_dataset(path: Path) -> None:
    tasks = [
        {
            "task_id": "abc001",
            "prompt": "Echo input",
            "tests": [{"input": "1\n", "output": "1\n"}],
        }
    ]
    with path.open("w") as fh:
        for t in tasks:
            json.dump(t, fh)
            fh.write("\n")


def test_builder_updates_versions_file(tmp_path):
    raw = tmp_path / "raw.jsonl"
    _write_sample_dataset(raw)

    out_dir = tmp_path / "out"
    versions_file = tmp_path / "versions.yml"
    build_atcoder(str(raw), str(out_dir), seed=0, versions_path=str(versions_file))

    data = json.loads(versions_file.read_text())
    assert "atcoder_abc" in data
