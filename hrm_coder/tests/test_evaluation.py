import json
import pytest

from hrm_coder.evaluation import (
    TaskEvaluation,
    aggregate_pass_at_k,
    check_determinism,
    flaky_tasks,
    markdown_report,
    html_report,
    compare_to_baseline,
    comparison_markdown_report,
    comparison_html_report,
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
    report_md = markdown_report(metrics, ['t2'])
    assert '| 1 | 0.500 |' in report_md
    assert 'Flaky Tasks' in report_md

    report_html = html_report(metrics, [])
    assert '<td>1</td><td>0.500</td>' in report_html
    assert 'No flaky tasks' in report_html


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
