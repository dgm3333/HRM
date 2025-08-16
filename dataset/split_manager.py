"""Utility functions for deterministic dataset splits.

This module provides a simple helper to split a sequence of
items into train/validation/test subsets using a fixed random seed.
The function avoids non-determinism so that repeated calls with the
same parameters always produce identical splits.  Ratios are provided
as fractions that sum to 1.0.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Sequence
import random


def split_list(
    items: Sequence,
    seed: int,
    ratios: Dict[str, float] | None = None,
) -> Dict[str, List]:
    """Split *items* into train/val/test subsets deterministically.

    Parameters
    ----------
    items:
        Sequence of items to split.
    seed:
        Seed for shuffling the input deterministically.
    ratios:
        Mapping of split name to ratio. If ``None`` a default of
        ``{"train": 0.8, "val": 0.1, "test": 0.1}`` is used.

    Returns
    -------
    dict
        Dictionary mapping split names to lists of items.
    """

    if ratios is None:
        ratios = {"train": 0.8, "val": 0.1, "test": 0.1}

    if abs(sum(ratios.values()) - 1.0) > 1e-8:
        raise ValueError("Split ratios must sum to 1.0")

    rng = random.Random(seed)
    indices = list(range(len(items)))
    rng.shuffle(indices)

    counts = {name: int(ratio * len(items)) for name, ratio in ratios.items()}
    assigned = sum(counts.values())
    # Assign remaining items (due to rounding) to the largest split
    remaining = len(items) - assigned
    if remaining:
        largest = max(ratios, key=ratios.get)
        counts[largest] += remaining

    splits: Dict[str, List] = {name: [] for name in ratios}
    pos = 0
    for name in ratios:
        c = counts[name]
        for idx in indices[pos:pos + c]:
            splits[name].append(items[idx])
        pos += c

    return splits
