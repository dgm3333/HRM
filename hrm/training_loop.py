from __future__ import annotations

"""Training helpers for Phase 6 HRM integration.

This module implements a light‑weight training loop that supports both
supervised fine‑tuning (SFT) and reinforcement learning (REINFORCE) with a
value baseline and entropy regularisation.  The goal is not to be feature
complete but to provide a concrete starting point that unblocks Phase 6
development.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional

import torch
from torch import nn
import torch.nn.functional as F


@dataclass
class HRMTrainingConfig:
    """Configuration values controlling the training loop."""

    baseline_coef: float = 0.5
    entropy_coef: float = 1e-4
    curriculum_stage: str = "visible"  # toggled between "visible" and "hidden"


class HRMTrainer:
    """Utility wrapper implementing common training operations.

    Parameters
    ----------
    model:
        A module returning ``(logits, value)`` when called.  ``logits`` are used
        for policy decisions while ``value`` estimates the baseline reward.
    optimizer:
        Optimiser used to update ``model`` parameters.
    config:
        ``HRMTrainingConfig`` controlling loss coefficients and curriculum
        stage.
    """

    def __init__(self, model: nn.Module, optimizer: torch.optim.Optimizer,
                 config: Optional[HRMTrainingConfig] = None) -> None:
        self.model = model
        self.optimizer = optimizer
        self.config = config or HRMTrainingConfig()

    # ------------------------------------------------------------------
    # Curriculum handling
    # ------------------------------------------------------------------
    def toggle_curriculum(self) -> None:
        """Switch between visible and hidden test stages."""
        if self.config.curriculum_stage == "visible":
            self.config.curriculum_stage = "hidden"
        else:
            self.config.curriculum_stage = "visible"

    # ------------------------------------------------------------------
    # Supervised fine‑tuning
    # ------------------------------------------------------------------
    def sft_step(self, inputs: torch.Tensor, targets: torch.Tensor) -> float:
        """Perform a single supervised fine‑tuning step.

        ``inputs`` and ``targets`` are expected to be tensor batches compatible
        with the wrapped model.  The method returns the scalar loss value for
        logging purposes.
        """
        self.model.train()
        logits, _ = self.model(inputs)
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)),
                               targets.view(-1),
                               ignore_index=-100)
        loss.backward()
        self.optimizer.step()
        self.optimizer.zero_grad(set_to_none=True)
        return float(loss.detach())

    # ------------------------------------------------------------------
    # Reinforcement learning (REINFORCE with baseline)
    # ------------------------------------------------------------------
    def reinforce_step(
        self,
        inputs: torch.Tensor,
        reward_fn: Callable[[torch.Tensor], torch.Tensor],
    ) -> Dict[str, float]:
        """Run a REINFORCE update using ``reward_fn``.

        The model is expected to output ``(logits, value)``.  ``reward_fn`` is a
        callable that receives sampled actions and returns a reward tensor.  A
        dictionary containing basic metrics is returned to aid debugging.
        """
        self.model.train()
        logits, value = self.model(inputs)
        log_probs = F.log_softmax(logits, dim=-1)
        probs = log_probs.exp()
        actions = torch.multinomial(probs, num_samples=1)
        selected_logp = log_probs.gather(-1, actions).squeeze(-1)
        reward = reward_fn(actions.squeeze(-1))

        advantage = reward - value.detach()
        policy_loss = -(advantage * selected_logp).mean()
        value_loss = F.mse_loss(value, reward)
        entropy = -(probs * log_probs).sum(-1).mean()

        total_loss = policy_loss + self.config.baseline_coef * value_loss
        total_loss -= self.config.entropy_coef * entropy
        total_loss.backward()
        self.optimizer.step()
        self.optimizer.zero_grad(set_to_none=True)

        return {
            "policy_loss": float(policy_loss.detach()),
            "value_loss": float(value_loss.detach()),
            "entropy": float(entropy.detach()),
            "reward": float(reward.detach().mean()),
        }


__all__ = ["HRMTrainer", "HRMTrainingConfig"]
