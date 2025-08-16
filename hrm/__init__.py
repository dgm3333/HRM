"""Utility classes for HRM code tasks.

The package bundles small helpers used in Phase 6 of the development
roadmap.  In addition to a C++ tokenizer and naïve ``CodeEncoder`` it now
exposes :class:`~hrm.training_loop.HRMTrainer` which implements a minimal
training loop with supervised fine‑tuning and REINFORCE support.  These
utilities provide the scaffolding required to experiment with HRM models
on code tasks.
"""

from .code_tokenizer import CppTokenizer
from .code_encoder import CodeEncoder
from .ast_encoder import ASTEncoder
from .training_loop import HRMTrainer, HRMTrainingConfig

__all__ = [
    "CppTokenizer",
    "CodeEncoder",
    "ASTEncoder",
    "HRMTrainer",
    "HRMTrainingConfig",
]
