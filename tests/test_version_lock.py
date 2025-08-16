import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from dataset.version_lock import (  # noqa: E402
    compute_dataset_hash,
    update_version,
    verify_version,
)


def test_update_version_writes_hash(tmp_path):
    ds = tmp_path / "dataset"
    ds.mkdir()
    (ds / "file.txt").write_text("hello")

    versions_file = tmp_path / "versions.yml"
    digest1 = update_version("demo", str(ds), str(versions_file))
    data = json.loads(versions_file.read_text())
    assert data["demo"] == digest1

    # Modify dataset and ensure hash changes
    (ds / "file.txt").write_text("world")
    digest2 = update_version("demo", str(ds), str(versions_file))
    assert digest2 != digest1
    data = json.loads(versions_file.read_text())
    assert data["demo"] == digest2


def test_compute_dataset_hash_matches_update(tmp_path):
    ds = tmp_path / "data"
    ds.mkdir()
    (ds / "a.txt").write_text("x")
    digest = compute_dataset_hash(ds)
    versions_file = tmp_path / "versions.yml"
    digest2 = update_version("sample", str(ds), str(versions_file))
    assert digest == digest2


def test_verify_version(tmp_path):
    ds = tmp_path / "ds"
    ds.mkdir()
    (ds / "f.txt").write_text("hello")
    versions_file = tmp_path / "versions.yml"
    update_version("demo", str(ds), str(versions_file))
    assert verify_version("demo", str(ds), str(versions_file))
    (ds / "f.txt").write_text("world")
    assert not verify_version("demo", str(ds), str(versions_file))
