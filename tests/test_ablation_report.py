import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from hrm_coder.ablation import generate_ablation_report  # noqa: E402


def test_generate_ablation_report(tmp_path: Path) -> None:
    baseline = {"pass@1": 0.4}
    current = {"pass@1": 0.6}
    baseline_file = tmp_path / "baseline.json"
    current_file = tmp_path / "current.json"
    report_file = tmp_path / "report.json"
    baseline_file.write_text(json.dumps(baseline))
    current_file.write_text(json.dumps(current))

    comparison = generate_ablation_report(
        str(current_file), str(baseline_file), str(report_file)
    )

    assert report_file.exists()
    assert json.loads(report_file.read_text()) == comparison
    assert comparison["pass@1"]["delta"] == pytest.approx(0.2)
