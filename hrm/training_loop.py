from __future__ import annotations

"""Training helpers for Phase 6 HRM integration.

This module implements a light‑weight training loop that supports both
supervised fine‑tuning (SFT) and reinforcement learning (REINFORCE) with a
value baseline and entropy regularisation.  The goal is not to be feature
complete but to provide a concrete starting point that unblocks Phase 6
development.
"""

from dataclasses import asdict, dataclass
from typing import Callable, Dict, Iterable, Optional, Tuple

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
        A module returning ``(logits, value)`` when called.  ``logits`` are
        used for policy decisions while ``value`` estimates the baseline
        reward.
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
    # Checkpointing
    # ------------------------------------------------------------------
    def save_checkpoint(self, path: str) -> None:
        """Serialise ``model`` and ``optimizer`` state to ``path``.

        The configuration is stored alongside the state dictionaries so a
        resumed run can continue with identical hyper‑parameters.
        """

        state = {
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "config": asdict(self.config),
        }
        torch.save(state, path)

    def load_checkpoint(
        self, path: str, map_location: Optional[str] = None
    ) -> None:
        """Restore ``model`` and ``optimizer`` state from ``path``."""

        checkpoint = torch.load(path, map_location=map_location)
        self.model.load_state_dict(checkpoint["model"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        cfg_dict = checkpoint.get("config")
        if cfg_dict is not None:
            self.config = HRMTrainingConfig(**cfg_dict)

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

    def sft_epoch(
        self, dataloader: Iterable[Tuple[torch.Tensor, torch.Tensor]]
    ) -> float:
        """Run an SFT epoch over ``dataloader`` and return the average loss."""
        total_loss = 0.0
        count = 0
        for inputs, targets in dataloader:
            total_loss += self.sft_step(inputs, targets)
            count += 1
        return total_loss / max(1, count)

    # ------------------------------------------------------------------
    # Reinforcement learning (REINFORCE with baseline)
    # ------------------------------------------------------------------
    def reinforce_step(
        self,
        inputs: torch.Tensor,
        reward_fn: Callable[[torch.Tensor], torch.Tensor],
    ) -> Dict[str, float]:
        """Run a REINFORCE update using ``reward_fn``.

        The model is expected to output ``(logits, value)``.  ``reward_fn`` is
        a callable that receives sampled actions and returns a reward tensor.
        A dictionary containing basic metrics is returned to aid debugging.
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

    def reinforce_epoch(
        self,
        dataloader: Iterable[torch.Tensor],
        reward_fn: Callable[[torch.Tensor], torch.Tensor],
    ) -> Dict[str, float]:
        """Run a REINFORCE epoch and return averaged statistics."""
        agg = {
            "policy_loss": 0.0,
            "value_loss": 0.0,
            "entropy": 0.0,
            "reward": 0.0,
        }
        count = 0
        for inputs in dataloader:
            stats = self.reinforce_step(inputs, reward_fn)
            for k, v in stats.items():
                agg[k] += v
            count += 1
        return {k: v / max(1, count) for k, v in agg.items()}


__all__ = ["HRMTrainer", "HRMTrainingConfig"]
