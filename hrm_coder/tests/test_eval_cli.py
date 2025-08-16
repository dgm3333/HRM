import json
import sys

from hrm_coder import eval_cli


def test_eval_cli_generates_reports(tmp_path, monkeypatch):
    results = {"t1": [True]}
    results_file = tmp_path / "results.json"
    results_file.write_text(json.dumps(results))

    incident_file = tmp_path / "inc.json"
    incident_file.write_text(json.dumps({"t1": "pass"}))

    out_dir = tmp_path / "out"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eval_cli",
            str(results_file),
            str(out_dir),
            "--incidents",
            str(incident_file),
            "--overrides",
            "acceptance.pass_at_1=0.0",
            "acceptance.pass_at_10=0.0",
        ],
    )

    eval_cli.main()

    assert (out_dir / "report.md").exists()
