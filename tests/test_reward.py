import pathlib
import sys
import logging

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from utils.reward import RewardAggregator  # noqa: E402
from utils.diagnostics import clang_tidy_score, cppcheck_score  # noqa: E402


def test_reward_aggregator_basic():
    agg = RewardAggregator(
        weights={'compile': 0.1, 'tests': 0.7, 'coverage': 0.2},
        max_edit_penalty=0.05,
        max_time_penalty=0.05,
        max_memory_penalty=0.05,
    )

    # Perfect run within limits
    r1 = agg.compute(
        compile_success=True,
        tests_passed=5,
        tests_total=5,
        coverage=1.0,
        edit_cost=0,
        time_used=1.0,
        memory_used=1.0,
        time_limit=2.0,
        memory_limit=2.0,
    )
    assert abs(r1 - 1.0) < 1e-6

    # Failure with penalties
    r2 = agg.compute(
        compile_success=False,
        tests_passed=0,
        tests_total=5,
        coverage=0.0,
        edit_cost=10.0,
        time_used=3.0,
        memory_used=3.0,
        time_limit=2.0,
        memory_limit=2.0,
    )
    assert r2 <= -0.1

    hist = agg.histogram()
    assert sum(hist) == 2


def test_reward_with_lint_static_and_coverage_delta():
    agg = RewardAggregator(
        weights={
            'compile': 0.1,
            'tests': 0.3,
            'coverage': 0.2,
            'coverage_delta': 0.2,
            'lint': 0.1,
            'static': 0.1,
        },
        max_edit_penalty=0.0,
        max_time_penalty=0.0,
        max_memory_penalty=0.0,
    )

    r = agg.compute(
        compile_success=True,
        tests_passed=3,
        tests_total=4,
        coverage=0.6,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        lint_score=0.5,
        static_score=0.8,
        prev_coverage=0.4,
    )

    assert abs(r - 0.615) < 1e-6


def test_compute_from_outputs_matches_manual_scores():
    agg = RewardAggregator(
        weights={
            'compile': 0.1,
            'tests': 0.3,
            'coverage': 0.2,
            'coverage_delta': 0.2,
            'lint': 0.1,
            'static': 0.1,
        },
        max_edit_penalty=0.0,
        max_time_penalty=0.0,
        max_memory_penalty=0.0,
    )

    clang_output = "foo.cpp:1:1: warning: thing [misc]"
    cppcheck_output = "[warning] variable unused"

    r1 = agg.compute_from_outputs(
        compile_success=True,
        tests_passed=2,
        tests_total=4,
        coverage=0.5,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        clang_output=clang_output,
        cppcheck_output=cppcheck_output,
        prev_coverage=0.3,
    )

    r2 = agg.compute(
        compile_success=True,
        tests_passed=2,
        tests_total=4,
        coverage=0.5,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        lint_score=clang_tidy_score(clang_output),
        static_score=cppcheck_score(cppcheck_output),
        prev_coverage=0.3,
    )

    assert abs(r1 - r2) < 1e-6


def test_compile_diagnostics_penalty():
    agg = RewardAggregator(
        weights={"compile": 0.1, "diagnostics": 0.3},
        max_edit_penalty=0.0,
        max_time_penalty=0.0,
        max_memory_penalty=0.0,
    )

    clean = agg.compute(
        compile_success=True,
        tests_passed=0,
        tests_total=0,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        warnings=0,
        errors=0,
    )

    noisy = agg.compute(
        compile_success=True,
        tests_passed=0,
        tests_total=0,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        warnings=2,
        errors=1,
    )

    assert noisy < clean

    r = agg.compute_from_outputs(
        compile_success=True,
        tests_passed=0,
        tests_total=0,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        clang_output="",
        cppcheck_output="",
        compiler_stdout="a.cpp:1:1: warning: w\n",
        compiler_stderr="a.cpp:2:2: error: e\n",
    )

    manual = agg.compute(
        compile_success=True,
        tests_passed=0,
        tests_total=0,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        warnings=1,
        errors=1,
    )

    assert abs(r - manual) < 1e-6


def test_compute_from_outputs_uses_junit():
    agg = RewardAggregator(
        weights={'compile': 0.1, 'tests': 0.2},
        max_edit_penalty=0.0,
        max_time_penalty=0.0,
        max_memory_penalty=0.0,
    )
    junit = '<testsuite tests="2" failures="1"></testsuite>'
    r = agg.compute_from_outputs(
        compile_success=True,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        junit_xml=junit,
    )
    manual = agg.compute(
        compile_success=True,
        tests_passed=1,
        tests_total=2,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
    )
    assert abs(r - manual) < 1e-6


def test_sanitizer_bonus_and_penalty():
    agg = RewardAggregator(
        weights={'compile': 0.1, 'tests': 0.2, 'sanitizer': 0.1},
        max_edit_penalty=0.0,
        max_time_penalty=0.0,
        max_memory_penalty=0.0,
    )

    clean = agg.compute(
        compile_success=True,
        tests_passed=1,
        tests_total=1,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        sanitizer_clean=True,
    )

    crash = agg.compute(
        compile_success=True,
        tests_passed=1,
        tests_total=1,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        sanitizer_clean=False,
    )

    clean2 = agg.compute_from_outputs(
        compile_success=True,
        tests_passed=1,
        tests_total=1,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        sanitizer_output="",
    )

    crash2 = agg.compute_from_outputs(
        compile_success=True,
        tests_passed=1,
        tests_total=1,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        sanitizer_output="ERROR: AddressSanitizer: heap-buffer-overflow",
    )

    assert clean > crash
    assert abs(clean - 0.4) < 1e-6
    assert abs(crash - 0.2) < 1e-6
    assert abs(clean - clean2) < 1e-6
    assert abs(crash - crash2) < 1e-6


def test_all_green_bonus_and_compile_gate():
    agg = RewardAggregator(
        weights={"compile": 0.1, "tests": 0.2},
        all_green_bonus=0.5,
        max_edit_penalty=0.0,
        max_time_penalty=0.0,
        max_memory_penalty=0.0,
    )

    # All tests pass → bonus applied
    all_green = agg.compute(
        compile_success=True,
        tests_passed=3,
        tests_total=3,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
    )
    assert abs(all_green - 0.8) < 1e-6

    # Partial pass → no bonus
    partial = agg.compute(
        compile_success=True,
        tests_passed=2,
        tests_total=3,
        coverage=0.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
    )
    assert partial < all_green

    # Compile failure should gate tests/coverage contributions
    gated = agg.compute(
        compile_success=False,
        tests_passed=3,
        tests_total=3,
        coverage=1.0,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
    )
    assert gated == 0.0


def test_log_histogram_warns_on_out_of_range(caplog):
    agg = RewardAggregator(weights={'compile': 1.0}, max_edit_penalty=2.0)
    agg.compute(
        compile_success=False,
        tests_passed=0,
        tests_total=0,
        coverage=0.0,
        edit_cost=10.0,
        time_used=0.0,
        memory_used=0.0,
    )
    with caplog.at_level(logging.WARNING):
        agg.log_histogram()
    assert any(
        "reward out of expected [-1,1] range" in r.message
        for r in caplog.records
    )


def test_drift_check_detects_mean_shift(caplog):
    agg = RewardAggregator(weights={'compile': 1.0}, max_edit_penalty=2.0)
    # Populate history with positive rewards within range
    for _ in range(5):
        agg.compute(
            compile_success=True,
            tests_passed=1,
            tests_total=1,
            coverage=0.0,
            edit_cost=0.0,
            time_used=0.0,
            memory_used=0.0,
        )
    with caplog.at_level(logging.WARNING):
        assert not agg.check_drift((0.0, 1.0))

    # Add negative rewards to shift mean below range
    for _ in range(5):
        agg.compute(
            compile_success=False,
            tests_passed=0,
            tests_total=0,
            coverage=0.0,
            edit_cost=10.0,
            time_used=0.0,
            memory_used=0.0,
        )
    with caplog.at_level(logging.WARNING):
        assert agg.check_drift((0.0, 1.0))
    assert any(
        "outside expected range" in r.message for r in caplog.records
    )


def test_compute_from_dir(tmp_path):
    agg = RewardAggregator(
        weights={
            'compile': 0.1,
            'tests': 0.3,
            'coverage': 0.2,
            'coverage_delta': 0.2,
            'lint': 0.1,
            'static': 0.1,
        },
        max_edit_penalty=0.0,
        max_time_penalty=0.0,
        max_memory_penalty=0.0,
    )

    (tmp_path / 'junit.xml').write_text(
        '<testsuite tests="2" failures="0"></testsuite>'
    )
    (tmp_path / 'coverage.json').write_text('{"line": 0.5}')
    (tmp_path / 'clang_tidy.log').write_text(
        'a.cpp:1:1: warning: thing [misc]'
    )
    (tmp_path / 'cppcheck.log').write_text('[warning] x')
    (tmp_path / 'compile.stdout').write_text('a.cpp:1:1: warning: w')
    (tmp_path / 'compile.stderr').write_text('')
    (tmp_path / 'sanitizer.log').write_text('')

    meta = {
        'compile_success': True,
        'edit_cost': 0.0,
        'time_used': 0.0,
        'memory_used': 0.0,
        'prev_coverage': 0.3,
    }

    r_dir = agg.compute_from_dir(tmp_path, meta=meta)
    r_manual = agg.compute_from_outputs(
        compile_success=True,
        tests_passed=2,
        tests_total=2,
        coverage=0.5,
        edit_cost=0.0,
        time_used=0.0,
        memory_used=0.0,
        clang_output='a.cpp:1:1: warning: thing [misc]',
        cppcheck_output='[warning] x',
        compiler_stdout='a.cpp:1:1: warning: w',
        compiler_stderr='',
        sanitizer_output='',
        prev_coverage=0.3,
    )

    assert abs(r_dir - r_manual) < 1e-6
