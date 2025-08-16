import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from hrm_coder.ablation_cli import main  # noqa: E402


def test_ablation_cli_generates_report(tmp_path: Path) -> None:
    baseline = {"pass@1": 0.4}
    current = {"pass@1": 0.6}
    baseline_file = tmp_path / "baseline.json"
    current_file = tmp_path / "current.json"
    report_file = tmp_path / "report.json"
    baseline_file.write_text(json.dumps(baseline))
    current_file.write_text(json.dumps(current))

    main(
        [
            f"current_metrics={current_file}",
            f"baseline_metrics={baseline_file}",
            f"output_report={report_file}",
        ]
    )

    assert report_file.exists()
    data = json.loads(report_file.read_text())
    assert data["pass@1"]["delta"] == pytest.approx(0.2)

