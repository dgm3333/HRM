import json
import sys
from pathlib import Path

import pytest

# Ensure repository root on path for local imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from runners.codeforces_harness import (
    IOPair,
    build_io_harness,
    run_io_harness,
    summarize_result,
)


def test_build_io_harness_layout(tmp_path: Path) -> None:
    tests = [IOPair("1\n", "2\n"), IOPair("3\n", "4\n")]
    dest = tmp_path / "harness"
    build_io_harness(tests, dest, time_limit_ms=123, memory_limit_kb=456)

    tests_dir = dest / "tests"
    assert (tests_dir / "0.in").read_text() == "1\n"
    assert (tests_dir / "0.out").read_text() == "2\n"
    assert (tests_dir / "1.in").read_text() == "3\n"
    assert (tests_dir / "1.out").read_text() == "4\n"

    meta = json.loads((dest / "meta.json").read_text())
    assert meta["time_limit_ms"] == 123
    assert meta["memory_limit_kb"] == 456


def test_run_io_harness_pass(tmp_path: Path) -> None:
    src = tmp_path / "main.cpp"
    src.write_text(
        """
#include <bits/stdc++.h>
int main(){int a,b;if(!(std::cin>>a>>b)) return 0; std::cout<<a+b;}
"""
    )
    tests = [IOPair("1 2\n", "3\n"), IOPair("5 7\n", "12\n")]
    result = run_io_harness([src], tests, sanitize=False)
    summary = summarize_result(result)
    assert summary["verdict"] == "OK"
    assert summary["passed"]


def test_run_io_harness_wrong_answer(tmp_path: Path) -> None:
    src = tmp_path / "main.cpp"
    src.write_text(
        """
#include <bits/stdc++.h>
int main(){int a,b;if(!(std::cin>>a>>b)) return 0; std::cout<<a-b;}
"""
    )
    tests = [IOPair("1 2\n", "3\n"), IOPair("5 7\n", "12\n")]
    result = run_io_harness([src], tests, sanitize=False)
    summary = summarize_result(result)
    assert summary["verdict"] == "WA"
    assert not summary["passed"]


def test_run_io_harness_time_limit(tmp_path: Path) -> None:
    src = tmp_path / "main.cpp"
    src.write_text(
        """
#include <thread>
#include <chrono>
int main(){std::this_thread::sleep_for(std::chrono::milliseconds(100));}
"""
    )
    tests = [IOPair("\n", "\n")]
    result = run_io_harness([src], tests, time_limit_ms=10, sanitize=False)
    summary = summarize_result(result)
    assert summary["verdict"] == "TL"


def test_run_io_harness_memory_limit(tmp_path: Path) -> None:
    src = tmp_path / "main.cpp"
    src.write_text(
        """
#include <vector>
int main(){std::vector<int> v; v.resize(50'000'000);}
"""
    )
    tests = [IOPair("\n", "\n")]
    # Set memory limit to 64 MB which is below the allocation above (~200 MB)
    result = run_io_harness(
        [src],
        tests,
        memory_limit_kb=64_000,
        sanitize=False,
    )
    summary = summarize_result(result)
    assert summary["verdict"] == "ML"
