import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

from dataset.dvc import generate_stage_yaml  # noqa: E402


def test_generate_stage_yaml_basic():
    yaml = generate_stage_yaml(
        "catalog.json", "out", "versions.yml", stage_name="stage"
    )
    assert "stages:" in yaml
    assert "stage:" in yaml
    cmd_line = (
        "cmd: python -m dataset.build_from_catalog "
        "catalog.json out --versions versions.yml"
    )
    assert cmd_line in yaml
    assert "- catalog.json" in yaml
    assert "- dataset/build_from_catalog.py" in yaml
    assert "- out" in yaml
    assert "- versions.yml" in yaml


def test_cli_writes_dvc_yaml(tmp_path: Path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text("[]")
    out_dir = tmp_path / "out"
    versions = tmp_path / "versions.yml"
    dvc_yaml = tmp_path / "generated.yaml"

    cmd = [
        sys.executable,
        "-m",
        "dataset.dvc",
        str(catalog),
        str(out_dir),
        "--versions",
        str(versions),
        "--yaml",
        str(dvc_yaml),
        "--stage-name",
        "stage",
    ]
    subprocess.run(cmd, check=True)

    assert dvc_yaml.exists()
    content = dvc_yaml.read_text()
    expected_cmd = (
        f"cmd: python -m dataset.build_from_catalog {catalog} "
        f"{out_dir} --versions {versions}"
    )
    assert expected_cmd in content
    assert "  stage:" in content
    assert f"- {catalog}" in content
    assert f"- {out_dir}" in content
    assert f"- {versions}" in content
