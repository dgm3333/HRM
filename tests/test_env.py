import random
import sys
from pathlib import Path

# Ensure repository root is on sys.path for module resolution
sys.path.append(str(Path(__file__).resolve().parents[1]))

from hrm_coder.env import pin_environment


def test_random_seed_reproducibility():
    pin_environment(42)
    first = random.random()
    pin_environment(42)
    second = random.random()
    assert first == second
