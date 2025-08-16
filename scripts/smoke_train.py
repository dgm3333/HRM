#!/usr/bin/env python3
"""Minimal 5-task smoke training run for Phase 6.

This script exercises the HRMTrainer's supervised fine-tuning path on a
small synthetic dataset.  It is intended for CI smoke tests and runs in
under a second on CPU.
"""

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from hrm.training_loop import HRMTrainer, HRMTrainingConfig


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

    avg_loss = trainer.sft_epoch(loader)
    print(f"avg_loss={avg_loss:.4f}")


if __name__ == "__main__":
    main()
