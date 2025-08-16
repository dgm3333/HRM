from __future__ import annotations

"""Phase 1 evaluation stub for HRM Coder.

Loads configuration and pins the environment in preparation for
future evaluation routines.
"""

import argparse
from dataclasses import asdict
from pprint import pformat

from .config import load_config
from .env import pin_environment


def main() -> None:
    """Entry point for the evaluation stub."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "overrides", nargs="*", help="Hydra-style overrides for evaluation"
    )
    args = parser.parse_args()

    cfg = load_config(args.overrides)
    pin_environment()

    print("Loaded configuration:")
    print(pformat(asdict(cfg)))
    print("Evaluation loop not yet implemented – Phase 1 placeholder")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
