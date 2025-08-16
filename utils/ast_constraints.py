"""Constraint checking for AST edit actions.

The :class:`ConstraintChecker` applies an :class:`utils.ast_actions.AstAction`
to source code and verifies that the resulting code parses without errors.
It provides a lightweight guard against edits that would leave the C++ AST
in an invalid state, helping to keep Phase 9's action space well-behaved.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.ast_actions import AstAction
from utils.ast_edit import CppAst


@dataclass
class ConstraintChecker:
    """Validate edits produced by :mod:`utils.ast_actions`."""

    ast: CppAst

    def is_valid_edit(self, code: str, action: AstAction) -> bool:
        """Return ``True`` if applying ``action`` yields a parseable AST."""

        try:
            result = action.apply(self.ast, code)
        except Exception:
            return False
        if result.tree is None:
            try:
                return self.ast.is_valid(result.code)
            except Exception:
                return False
        return not result.tree.root_node.has_error
