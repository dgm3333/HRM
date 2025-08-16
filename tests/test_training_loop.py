import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import torch
from torch import nn

from hrm.training_loop import HRMTrainer, HRMTrainingConfig


class DummyModel(nn.Module):
    """Tiny model returning logits and a value estimate."""

    def __init__(self, vocab_size: int = 2):
        super().__init__()
        self.linear = nn.Linear(vocab_size, vocab_size)
        self.value = nn.Linear(vocab_size, 1)

    def forward(self, x):
        logits = self.linear(x)
        baseline = self.value(x).squeeze(-1)
        return logits, baseline


def test_reinforce_step_updates_model():
    torch.manual_seed(0)
    model = DummyModel()
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    trainer = HRMTrainer(model, opt, HRMTrainingConfig())

    inputs = torch.eye(2)

    def reward_fn(actions: torch.Tensor) -> torch.Tensor:
        # Reward action 1, penalise action 0
        return torch.where(actions == 1, torch.tensor(1.0), torch.tensor(0.0))

    before = model.linear.weight.clone()
    info = trainer.reinforce_step(inputs, reward_fn)
    after = model.linear.weight

    assert not torch.allclose(before, after)
    assert "policy_loss" in info and "value_loss" in info


def test_curriculum_toggle():
    model = DummyModel()
    opt = torch.optim.SGD(model.parameters(), lr=0.1)
    trainer = HRMTrainer(model, opt)
    assert trainer.config.curriculum_stage == "visible"
    trainer.toggle_curriculum()
    assert trainer.config.curriculum_stage == "hidden"
