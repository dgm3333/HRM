"""Draft interface for an AST-based code encoder."""

from __future__ import annotations

from typing import Iterable, List, Protocol


class ASTEncoder(Protocol):
    """Protocol describing an AST-based encoder interface.

    The concrete implementation will convert source code into an abstract
    syntax tree (AST) representation and provide utilities to encode the
    tree into model-ready tensors.  Only the method signatures are defined
    here to unblock Phase 6 development while a full implementation is
    designed.
    """

    def encode(self, code: str) -> List[int]:  # pragma: no cover - interface
        """Encode *code* into a sequence of token ids."""
        raise NotImplementedError

    def decode(self, ids: Iterable[int]) -> str:  # pragma: no cover - interface
        """Reconstruct code from *ids* representing an AST traversal."""
        raise NotImplementedError


__all__ = ["ASTEncoder"]
