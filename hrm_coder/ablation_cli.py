from __future__ import annotations

"""CLI entry point for generating ablation comparison reports.

This small utility loads its configuration from ``conf/ablation/default.yaml``
using :mod:`omegaconf`.  Paths can be overridden on the command line using
``key=value`` arguments.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from omegaconf import OmegaConf

from .ablation import generate_ablation_report


@dataclass
class AblationConfig:
    """Configuration for an ablation comparison job."""

    current_metrics: str
    baseline_metrics: str
    output_report: str


def load_ablation_config(overrides: Sequence[str] | None = None) -> AblationConfig:
    """Load ablation configuration from YAML and apply overrides."""

    config_path = Path(__file__).parent / "conf" / "ablation" / "default.yaml"
    cfg = OmegaConf.load(config_path)
    if overrides:
        override_cfg = OmegaConf.from_dotlist(list(overrides))
        cfg = OmegaConf.merge(cfg, override_cfg)
    cfg_dict = OmegaConf.to_container(cfg, resolve=True)
    return AblationConfig(**cfg_dict)  # type: ignore[arg-type]


def main(argv: Sequence[str] | None = None) -> None:
    """Generate an ablation report using Hydra-style overrides."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "overrides",
        nargs="*",
        help="Hydra-style overrides, e.g. current_metrics=path/to.json",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    cfg = load_ablation_config(args.overrides)
    generate_ablation_report(
        cfg.current_metrics, cfg.baseline_metrics, cfg.output_report
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
