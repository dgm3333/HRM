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
class AppConfig:
    """Top-level application configuration."""
    model: ModelConfig = field(default_factory=ModelConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)


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
    )


__all__ = ["AppConfig", "DatasetConfig", "ModelConfig", "load_config"]
