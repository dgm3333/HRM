import json
import sys
from pathlib import Path

import pytest

# Ensure repository root is on the import path so the local ``dataset`` package
# is used instead of the similarly named third-party library.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataset.build_atcoder_abc_dataset import (  # noqa: E402
    load_tasks as load_atcoder,
)
from dataset.build_codeforces_intro_dataset import (  # noqa: E402
    load_tasks as load_codeforces,
)
from dataset.build_humaneval_cpp_dataset import (  # noqa: E402
    load_tasks as load_humaneval,
)
from pydantic import ValidationError  # noqa: E402


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w") as fh:
        for rec in records:
            json.dump(rec, fh)
            fh.write("\n")


def test_humaneval_schema_enforced(tmp_path: Path) -> None:
    good = {"task_id": "t1", "prompt": "//", "test": "//"}
    good_path = tmp_path / "good_he.jsonl"
    _write_jsonl(good_path, [good])
    tasks = load_humaneval(good_path)
    assert tasks[0].task_id == "t1"

    bad = {"task_id": "t1", "prompt": "//"}  # missing test field
    bad_path = tmp_path / "bad_he.jsonl"
    _write_jsonl(bad_path, [bad])
    with pytest.raises(ValidationError):
        load_humaneval(bad_path)


def test_codeforces_schema_enforced(tmp_path: Path) -> None:
    good = {
        "task_id": "cf1",
        "prompt": "p",
        "tests": [{"input": "1\n", "output": "1\n"}],
    }
    good_path = tmp_path / "good_cf.jsonl"
    _write_jsonl(good_path, [good])
    tasks = load_codeforces(good_path)
    assert tasks[0].tests[0].output == "1\n"

    bad = {
        "task_id": "cf2",
        "prompt": "p",
        "tests": [{"input": "1\n"}],  # missing output
    }
    bad_path = tmp_path / "bad_cf.jsonl"
    _write_jsonl(bad_path, [bad])
    with pytest.raises(ValidationError):
        load_codeforces(bad_path)


def test_atcoder_schema_enforced(tmp_path: Path) -> None:
    good = {
        "task_id": "ac1",
        "prompt": "p",
        "tests": [{"input": "1\n", "output": "1\n"}],
    }
    good_path = tmp_path / "good_ac.jsonl"
    _write_jsonl(good_path, [good])
    tasks = load_atcoder(good_path)
    assert tasks[0].tests[0].input == "1\n"

    bad = {
        "task_id": "ac2",
        "prompt": "p",
        "tests": [{"input": "1\n"}],  # missing output
    }
    bad_path = tmp_path / "bad_ac.jsonl"
    _write_jsonl(bad_path, [bad])
    with pytest.raises(ValidationError):
        load_atcoder(bad_path)
