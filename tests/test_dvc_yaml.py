import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

from dataset.dvc import write_dvc_yaml  # noqa: E402


def test_write_dvc_yaml(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text("[]")
    out_dir = tmp_path / "out"
    versions = tmp_path / "versions.yml"
    yaml_path = tmp_path / "dvc.yaml"

    write_dvc_yaml(
        str(catalog),
        str(out_dir),
        str(versions),
        yaml_path=str(yaml_path),
    )

    cmd = (
        "python -m dataset.build_from_catalog "
        f"{catalog} {out_dir} --versions {versions}"
    )
    expected = (
        "stages:\n"
        "  build-datasets:\n"
        f"    cmd: {cmd}\n"
        "    deps:\n"
        f"      - {catalog}\n"
        "      - dataset/build_from_catalog.py\n"
        "    outs:\n"
        f"      - {out_dir}\n"
        f"      - {versions}\n"
    )
    assert yaml_path.read_text() == expected
