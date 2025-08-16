from __future__ import annotations

"""Phase 1 training stub for HRM Coder.

This module demonstrates how training scripts will load Hydra
configuration and pin the runtime environment for determinism.
Actual training logic will be implemented in later phases.
"""

from dataclasses import asdict
import argparse
from pprint import pformat

from .config import load_config
from .env import pin_environment


def main() -> None:
    """Entry point for the training stub.

    Parameters
    ----------
    None
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "overrides",
        nargs="*",
        help="Hydra-style overrides, e.g. model.learning_rate=1e-4",
    )
    args = parser.parse_args()

    cfg = load_config(args.overrides)
    pin_environment()

    print("Loaded configuration:")
    print(pformat(asdict(cfg)))
    print("Training loop not yet implemented – Phase 1 placeholder")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
