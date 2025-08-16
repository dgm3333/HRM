import json
import pathlib
import sys
import zipfile

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

import pytest  # noqa: E402

from utils.eval_harness import (  # noqa: E402
    bundle_and_upload,
    compare_to_baseline,
    generate_comparison_report,
)


def test_compare_to_baseline(tmp_path):
    baseline_metrics = {"pass@1": 0.5, "pass@10": 0.8}
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(json.dumps(baseline_metrics))

    current_metrics = {"pass@1": 0.6, "pass@10": 0.7}
    comparison = compare_to_baseline(current_metrics, str(baseline_file))

    assert comparison["pass@1"]["baseline"] == pytest.approx(0.5)
    assert comparison["pass@1"]["delta"] == pytest.approx(0.1)
    assert comparison["pass@10"]["delta"] == pytest.approx(-0.1)


def test_bundle_and_upload(tmp_path):
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("hello")
    file_b.write_text("world")

    bundle_path = tmp_path / "bundle.zip"
    dest_dir = tmp_path / "upload"
    uploaded_path = bundle_and_upload(
        [str(file_a), str(file_b)], str(bundle_path), str(dest_dir)
    )

    assert zipfile.is_zipfile(uploaded_path)
    with zipfile.ZipFile(uploaded_path) as zf:
        assert sorted(zf.namelist()) == ["a.txt", "b.txt"]


def test_generate_comparison_report(tmp_path):
    baseline_metrics = {"pass@1": 0.4}
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(json.dumps(baseline_metrics))

    current_metrics = {"pass@1": 0.6}
    report_file = tmp_path / "report.json"
    comparison = generate_comparison_report(
        current_metrics, str(baseline_file), str(report_file)
    )

    assert report_file.exists()
    assert json.loads(report_file.read_text()) == comparison
    assert comparison["pass@1"]["delta"] == pytest.approx(0.2)
