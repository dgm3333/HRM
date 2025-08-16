#!/usr/bin/env python3
"""Minimal 5-task smoke evaluation run for Phase 8.

This script trains a tiny model on synthetic data and reports accuracy.
It is intended for CI smoke tests to exercise the evaluation path.
"""

import json
import pathlib
import sys

import mlflow
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

# Ensure repository root is on the import path when executed directly.
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from hrm.training_loop import HRMTrainer, HRMTrainingConfig  # noqa: E402
from utils.mlflow_logger import (  # noqa: E402
    end_run,
    log_metrics,
    log_params,
    start_run,
)


class TinyModel(nn.Module):
    """Simple linear model used for smoke evaluation."""

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
    loader = DataLoader(dataset, batch_size=1, shuffle=False)

    model = TinyModel(vocab)
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    trainer = HRMTrainer(model, opt, HRMTrainingConfig())

    start_run("smoke-eval", tags={"phase": "8"})
    log_params({"model": "TinyModel", "dataset_size": len(dataset)})

    # Run a quick supervised epoch to initialise weights
    trainer.sft_epoch(loader)

    # Evaluate accuracy on the synthetic dataset
    model.eval()
    correct = 0
    with torch.no_grad():
        for inp, target in loader:
            logits, _ = model(inp)
            pred = logits.argmax(-1)
            correct += int(pred.eq(target).item())
    acc = correct / len(dataset)
    print(f"accuracy={acc:.2f}")
    log_metrics({"accuracy": acc})

    # Record run metadata for CI artifacts
    active = mlflow.active_run()
    summary = {
        "run_id": active.info.run_id if active else None,
        "accuracy": acc,
    }
    with open("smoke_eval_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh)

    end_run()


if __name__ == "__main__":
    main()
