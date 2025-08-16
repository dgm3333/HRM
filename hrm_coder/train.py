from __future__ import annotations

"""Minimal training entry point for Phase 6 integration.

The script exercises both supervised fine-tuning and a tiny
reinforcement-learning loop using :class:`hrm.training_loop.HRMTrainer`.
It intentionally operates on a synthetic five-sample dataset so that
CI can run it within tight runtime budgets.
"""

from dataclasses import asdict
import argparse
import os
from pprint import pformat

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from hrm.training_loop import HRMTrainer, HRMTrainingConfig

from .config import load_config
from .env import pin_environment


class TinyModel(nn.Module):
    """Simple linear policy/value model used for smoke training."""

    def __init__(self, vocab_size: int) -> None:
        super().__init__()
        self.linear = nn.Linear(vocab_size, vocab_size)
        self.value = nn.Linear(vocab_size, 1)

    def forward(self, x: torch.Tensor):  # type: ignore[override]
        logits = self.linear(x)
        value = self.value(x).squeeze(-1)
        return logits, value


def main() -> None:
    """Run a tiny end-to-end training demo."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override deterministic seed from configuration",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to save/load a checkpoint",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from --checkpoint if it exists",
    )
    parser.add_argument(
        "overrides",
        nargs="*",
        help="Hydra-style overrides, e.g. model.learning_rate=1e-4",
    )
    args = parser.parse_args()

    cfg = load_config(args.overrides)

    seed = args.seed if args.seed is not None else cfg.environment.seed
    pin_environment(seed, cfg.environment.timezone, cfg.environment.locale)
    torch.manual_seed(seed)

    print("Loaded configuration:")
    print(pformat(asdict(cfg)))

    # Build a toy dataset consisting of five one-hot samples.
    vocab = 8
    inputs = torch.eye(vocab)[:5]
    targets = torch.arange(5) % vocab
    dataset = TensorDataset(inputs, targets)
    g = torch.Generator()
    g.manual_seed(seed)
    loader = DataLoader(dataset, batch_size=1, shuffle=True, generator=g)

    # Initialise model and trainer.
    model = TinyModel(vocab)
    opt = torch.optim.SGD(model.parameters(), lr=cfg.model.learning_rate)
    train_cfg = HRMTrainingConfig(
        baseline_coef=cfg.training.baseline_coef,
        entropy_coef=cfg.training.entropy_coef,
        curriculum_stage=cfg.training.curriculum_stage,
    )
    trainer = HRMTrainer(model, opt, train_cfg)

    print(f"curriculum={trainer.config.curriculum_stage}")

    if args.resume and args.checkpoint and os.path.exists(args.checkpoint):
        trainer.load_checkpoint(args.checkpoint, map_location="cpu")
        print(f"Resumed from {args.checkpoint}")

    # --- Supervised fine-tuning ---------------------------------------
    avg_loss = trainer.sft_epoch(loader)
    print(f"avg_loss={avg_loss:.4f}")

    # Switch curriculum stage before RL to exercise the toggle logic.
    trainer.toggle_curriculum()
    print(f"curriculum={trainer.config.curriculum_stage}")

    # --- Reinforcement learning ---------------------------------------
    def reward_fn_factory(target: torch.Tensor):
        def reward_fn(actions: torch.Tensor) -> torch.Tensor:
            return torch.where(
                actions == target, torch.tensor(1.0), torch.tensor(0.0)
            )

        return reward_fn

    rl_stats = {
        "policy_loss": 0.0,
        "value_loss": 0.0,
        "entropy": 0.0,
        "reward": 0.0,
    }
    for inp, target in dataset:
        stats = trainer.reinforce_step(
            inp.unsqueeze(0), reward_fn_factory(target)
        )
        for k, v in stats.items():
            rl_stats[k] += v
    for k in rl_stats:
        rl_stats[k] /= len(dataset)
    print("reinforce:", " ".join(f"{k}={v:.4f}" for k, v in rl_stats.items()))

    if args.checkpoint:
        trainer.save_checkpoint(args.checkpoint)
        print(f"Checkpoint written to {args.checkpoint}")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
