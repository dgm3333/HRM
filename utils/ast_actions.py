"""Edit action representations for C++ AST manipulations.

This module defines simple dataclasses representing insert, replace and
delete operations on C++ source code.  Each action exposes an ``apply``
method which delegates to :class:`utils.ast_edit.CppAst` and returns an
:class:`utils.ast_edit.EditResult`.  The actions form a minimal "action
space" for Phase 9 of the HRM Coder roadmap.
"""

from __future__ import annotations

from dataclasses import dataclass
from tree_sitter import Node

from utils.ast_edit import CppAst, EditResult


class AstAction:
    """Abstract base class for AST edit actions."""

    def apply(self, ast: CppAst, code: str) -> EditResult:  # pragma: no cover - interface
        """Apply the action using ``ast`` and return the edit result."""
        raise NotImplementedError


@dataclass
class InsertAction(AstAction):
    """Insert ``text`` at ``position`` (byte offset)."""

    position: int
    text: str

    def apply(self, ast: CppAst, code: str) -> EditResult:
        return ast.insert(code, self.position, self.text)


@dataclass
class ReplaceAction(AstAction):
    """Replace the span covered by ``node`` with ``replacement``."""

    node: Node
    replacement: str

    def apply(self, ast: CppAst, code: str) -> EditResult:
        return ast.replace(code, self.node, self.replacement)


@dataclass
class DeleteAction(AstAction):
    """Remove the span covered by ``node``."""

    node: Node

    def apply(self, ast: CppAst, code: str) -> EditResult:
        return ast.delete(code, self.node)
