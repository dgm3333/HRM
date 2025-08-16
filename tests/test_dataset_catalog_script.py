import os
import sys
import hashlib

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts import dataset_catalog  # noqa: E402


def test_sha256_of_path_file(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")
    expected = hashlib.sha256(b"hello").hexdigest()
    assert dataset_catalog.sha256_of_path(sample) == expected


def test_sha256_of_path_directory(tmp_path):
    directory = tmp_path / "dir"
    directory.mkdir()
    (directory / "a.txt").write_text("a")
    (directory / "b.txt").write_text("b")
    expected = hashlib.sha256()
    for file_path in sorted(p for p in directory.rglob("*") if p.is_file()):
        expected.update(file_path.relative_to(directory).as_posix().encode())
        expected.update(file_path.read_bytes())
    assert dataset_catalog.sha256_of_path(directory) == expected.hexdigest()


def test_build_catalog_with_custom_dataset(monkeypatch, tmp_path):
    data_file = tmp_path / "data.txt"
    data_file.write_text("data")
    sha = hashlib.sha256(b"data").hexdigest()
    monkeypatch.setattr(
        dataset_catalog,
        "DATASETS",
        [{"name": "tmp", "path": data_file, "license": "MIT"}],
    )
    catalog = dataset_catalog.build_catalog()
    assert catalog == [
        {
            "name": "tmp",
            "license": "MIT",
            "path": str(data_file),
            "sha256": sha,
        }
    ]


def test_validate_catalog_flags_mismatch(monkeypatch, tmp_path):
    data_file = tmp_path / "data.txt"
    data_file.write_text("data")
    sha = hashlib.sha256(b"data").hexdigest()
    catalog = [
        {
            "name": "tmp",
            "license": "MIT",
            "path": str(data_file),
            "sha256": sha,
        }
    ]
    catalog[0]["sha256"] = "bad"
    problems = dataset_catalog.validate_catalog(catalog)
    assert problems == ["tmp"]
