from hrm_coder.acceptance import AcceptanceCriteria, evaluate_acceptance


def test_evaluate_acceptance_passes():
    criteria = AcceptanceCriteria(pass_at_1=0.5, pass_at_10=0.7, max_timeout_rate=0.1)
    metrics = {
        "pass@1": 0.6,
        "pass@10": 0.8,
        "timeout_rate": 0.05,
        "sanitizer_failures": 0,
    }
    result = evaluate_acceptance(metrics, criteria)
    assert result["overall"]
    assert all(result[k] for k in ["pass@1", "pass@10", "timeout_rate", "sanitizer_failures"])


def test_evaluate_acceptance_failure():
    criteria = AcceptanceCriteria(pass_at_1=0.5, pass_at_10=0.7, max_timeout_rate=0.1)
    metrics = {
        "pass@1": 0.4,
        "pass@10": 0.8,
        "timeout_rate": 0.05,
        "sanitizer_failures": 0,
    }
    result = evaluate_acceptance(metrics, criteria)
    assert not result["overall"]
    assert not result["pass@1"]
