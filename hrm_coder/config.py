"""Hydra configuration loader for HRM Coder."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf


@dataclass
class ModelConfig:
    """Configuration for the model/training setup."""
    name: str = "small"
    learning_rate: float = 1e-3


@dataclass
class DatasetConfig:
    """Configuration for dataset selection."""
    name: str = "humaneval-cpp"


@dataclass
class RunnerConfig:
    """Configuration for the sandbox runner.

    These defaults are intentionally lightweight but provide a
    foundation for Phase 1 deterministic execution. They will be
    expanded in later phases to cover additional runner options.
    """

    compiler: str = "g++"
    sandbox: str = "nsjail"
    timeout: int = 5


@dataclass
class AcceptanceConfig:
    """Acceptance metric thresholds for Phase 0.

    These values represent the minimum quality bar for C++ experiments.
    Later phases may expand this structure with additional metrics.
    """

    pass_at_1: float = 0.5
    pass_at_10: float = 0.7
    max_timeout_rate: float = 0.05
    max_sanitizer_failures: int = 0


@dataclass
class AppConfig:
    """Top-level application configuration."""
    model: ModelConfig = field(default_factory=ModelConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    runner: RunnerConfig = field(default_factory=RunnerConfig)
    acceptance: AcceptanceConfig = field(default_factory=AcceptanceConfig)


def load_config(overrides: Sequence[str] | None = None) -> AppConfig:
    """Load the Hydra configuration from the ``conf`` directory.

    Parameters
    ----------
    overrides:
        Optional sequence of Hydra override strings.
    """
    config_dir = Path(__file__).parent / "conf"
    with initialize_config_dir(version_base=None, config_dir=str(config_dir)):
        cfg = compose(
            config_name="config",
            overrides=list(overrides) if overrides else [],
        )
    cfg_dict = OmegaConf.to_container(cfg, resolve=True)
    return AppConfig(
        model=ModelConfig(**cfg_dict["model"]),
        dataset=DatasetConfig(**cfg_dict["dataset"]),
        runner=RunnerConfig(**cfg_dict["runner"]),
        acceptance=AcceptanceConfig(**cfg_dict["acceptance"]),
    )


__all__ = [
    "AppConfig",
    "DatasetConfig",
    "ModelConfig",
    "RunnerConfig",
    "AcceptanceConfig",
    "load_config",
]
