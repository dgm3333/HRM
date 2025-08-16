import sys
from pathlib import Path

# Ensure repository root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataset.split_manager import split_list  # noqa: E402


def test_split_deterministic() -> None:
    items = list(range(10))
    splits_a = split_list(items, seed=123)
    splits_b = split_list(items, seed=123)
    assert splits_a == splits_b
    assert sum(len(v) for v in splits_a.values()) == len(items)
