import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataset.build_from_catalog import build_from_catalog  # noqa: E402
from dataset.version_lock import verify_catalog_versions  # noqa: E402


def _write_sample_humaneval(path: Path) -> None:
    tasks = [
        {
            "task_id": "task1",
            "prompt": "int add(int a,int b){return a+b;}\n",
            "test": "#include <cassert>\nint main(){assert(add(1,2)==3);}\n",
        }
    ]
    with path.open("w") as fh:
        for t in tasks:
            json.dump(t, fh)
            fh.write("\n")


def test_verify_catalog_versions(tmp_path):
    raw = tmp_path / "humaneval.jsonl"
    _write_sample_humaneval(raw)

    catalog = [
        {"name": "HumanEval-CPP", "path": str(raw), "license": "MIT"}
    ]
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(catalog))

    out_dir = tmp_path / "out"
    versions_file = tmp_path / "versions.yml"

    build_from_catalog(str(catalog_path), str(out_dir), str(versions_file))

    assert verify_catalog_versions(
        str(catalog_path), str(out_dir), str(versions_file)
    )

    # Corrupt the dataset and expect verification to fail
    prompt = out_dir / "HumanEval-CPP" / "train" / "task1" / "prompt.cpp"
    prompt.write_text("// modified\n")

    assert not verify_catalog_versions(
        str(catalog_path), str(out_dir), str(versions_file)
    )
