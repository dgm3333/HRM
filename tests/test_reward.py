import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from utils.reward import RewardAggregator


def test_reward_aggregator_basic():
    agg = RewardAggregator(weights={'compile': 0.1, 'tests': 0.7, 'coverage': 0.2},
                           max_edit_penalty=0.05,
                           max_time_penalty=0.05,
                           max_memory_penalty=0.05)

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
