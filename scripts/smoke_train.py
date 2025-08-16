#!/usr/bin/env python3
"""Minimal 5-task smoke training run for Phase 6.

This script exercises the HRMTrainer's supervised fine-tuning **and**
reinforcement-learning paths on a small synthetic dataset.  It is
intended for CI smoke tests and runs in under a second on CPU.
"""

import pathlib
import sys

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

# Ensure repository root is on the import path when executed directly.
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from hrm.training_loop import HRMTrainer, HRMTrainingConfig  # noqa: E402


class TinyModel(nn.Module):
    """Simple linear model used for smoke training."""

    def __init__(self, vocab_size: int = 8) -> None:
        super().__init__()
        self.linear = nn.Linear(vocab_size, vocab_size)
        self.value = nn.Linear(vocab_size, 1)

    def forward(self, x: torch.Tensor):  # type: ignore[override]
        logits = self.linear(x)
        value = self.value(x).squeeze(-1)
        return logits, value


def main() -> None:
    torch.manual_seed(0)
    vocab = 8
    inputs = torch.eye(vocab)[:5]
    targets = torch.arange(5) % vocab
    dataset = TensorDataset(inputs, targets)
    loader = DataLoader(dataset, batch_size=1, shuffle=True)

    model = TinyModel(vocab)
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    trainer = HRMTrainer(model, opt, HRMTrainingConfig())

    # --- Supervised fine-tuning epoch ---------------------------------
    avg_loss = trainer.sft_epoch(loader)
    print(f"avg_loss={avg_loss:.4f}")

    # --- Reinforcement learning epoch ---------------------------------
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
    print(
        "reinforce:",
        " ".join(f"{k}={v:.4f}" for k, v in rl_stats.items()),
    )


if __name__ == "__main__":
    main()
