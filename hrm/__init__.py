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
from .training_loop import HRMTrainer, HRMTrainingConfig

try:  # pragma: no cover - optional AST dependency
    from .ast_encoder import ASTEncoder, NodeTypeSchema
except Exception:  # pragma: no cover
    ASTEncoder = None  # type: ignore[assignment]
    NodeTypeSchema = None  # type: ignore[assignment]

__all__ = ["CppTokenizer", "CodeEncoder", "HRMTrainer", "HRMTrainingConfig"]
if ASTEncoder is not None:
    __all__ += ["ASTEncoder", "NodeTypeSchema"]
