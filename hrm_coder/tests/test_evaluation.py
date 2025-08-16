import json

import pytest

from hrm_coder.evaluation import (
    aggregate_pass_at_k,
    check_determinism,
    flaky_tasks,
    incident_rates,
    markdown_report,
    html_report,
    compare_to_baseline,
    comparison_markdown_report,
    comparison_html_report,
    generate_reports,
)


def test_pass_at_k_and_aggregate():
    results = {
        'a': [True, False, False],
        'b': [False, False, False],
    }
    metrics = aggregate_pass_at_k(results, ks=[1, 2])
    # Task a: pass@1 = 1/3, pass@2 = 2/3
    # Task b: pass@1 = 0, pass@2 = 0
    assert metrics[1] == pytest.approx((1/3 + 0) / 2)
    assert metrics[2] == pytest.approx((2/3 + 0) / 2)


def test_determinism_and_flaky_detection():
    runs = [
        {'t1': True, 't2': False},
        {'t1': True, 't2': True},
    ]
    determinism = check_determinism(runs)
    assert determinism == {'t1': True, 't2': False}
    assert flaky_tasks(runs) == ['t2']


def test_report_generation():
    metrics = {1: 0.5}
    incidents = {"timeout": 0.1}
    report_md = markdown_report(metrics, ['t2'], incidents)
    assert '| 1 | 0.500 |' in report_md
    assert 'Flaky Tasks' in report_md
    assert 'timeout' in report_md

    report_html = html_report(metrics, [], incidents)
    assert '<td>1</td><td>0.500</td>' in report_html
    assert 'No flaky tasks' in report_html
    assert 'timeout' in report_html


def test_baseline_comparison(tmp_path):
    baseline = {"pass@1": 0.4}
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(json.dumps(baseline))

    current = {"pass@1": 0.6}
    comparison = compare_to_baseline(current, str(baseline_file))

    assert comparison["pass@1"]["delta"] == pytest.approx(0.2)

    report_md = comparison_markdown_report(comparison)
    assert "| pass@1 | 0.400 | 0.600 | 0.200 |" in report_md

    report_html = comparison_html_report(comparison)
    assert "<td>0.600</td>" in report_html


def test_incident_rates():
    runs = [
        {"a": "timeout", "b": "pass"},
        {"a": "sanitizer", "b": "timeout"},
    ]
    rates = incident_rates(runs)
    assert rates["timeout"] == pytest.approx(2 / 4)
    assert rates["sanitizer"] == pytest.approx(1 / 4)


def test_generate_reports(tmp_path):
    results = {"t1": [True, False], "t2": [False, False]}
    results_file = tmp_path / "results.json"
    results_file.write_text(json.dumps(results))

    run1_file = tmp_path / "run1.json"
    run2_file = tmp_path / "run2.json"
    run1_file.write_text(json.dumps({"t1": True, "t2": False}))
    run2_file.write_text(json.dumps({"t1": True, "t2": True}))

    incident1_file = tmp_path / "inc1.json"
    incident2_file = tmp_path / "inc2.json"
    incident1_file.write_text(json.dumps({"t1": "timeout", "t2": "pass"}))
    incident2_file.write_text(json.dumps({"t1": "pass", "t2": "timeout"}))

    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(json.dumps({"pass@1": 0.0, "pass@2": 0.0}))

    metrics = generate_reports(
        results_path=str(results_file),
        output_dir=str(tmp_path),
        ks=[1, 2],
        run_paths=[str(run1_file), str(run2_file)],
        baseline_path=str(baseline_file),
        incident_paths=[str(incident1_file), str(incident2_file)],
    )

    assert metrics[1] == pytest.approx(0.25)
    report_md = (tmp_path / "report.md").read_text()
    assert "Flaky Tasks" in report_md and "t2" in report_md
    assert "Incident Rates" in report_md
    assert (tmp_path / "report.html").exists()
    assert (tmp_path / "baseline.md").exists()
    assert (tmp_path / "baseline.html").exists()
