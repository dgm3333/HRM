"""Utilities for editing C++ code through its AST.

This module exposes a small wrapper around the `tree_sitter` parser that
allows basic edit operations on C++ source strings.  It is an early step
toward Phase 9 (AST-edit action space) of the HRM Coder roadmap.

The `CppAst` class offers:

* `parse` – parse code into a `tree_sitter` tree.
* `replace` – replace the text spanned by a node.
* `insert` – insert text at a byte offset.
* `delete` – remove the text spanned by a node.
* `is_valid` – check that edited code still forms a valid C++ AST.

The implementation intentionally keeps the API small; later phases can build
on top with node embeddings and higher level edit policies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

try:  # pragma: no cover - optional dependency
    from tree_sitter import Node, Tree
    from tree_sitter_languages import get_parser
    _PARSER_ERROR = None
except Exception as exc:  # pragma: no cover - Tree-sitter not installed
    Node = Tree = Any  # type: ignore[assignment]
    get_parser = None  # type: ignore[assignment]
    _PARSER_ERROR = exc


@dataclass
class EditResult:
    """Result of an edit operation.

    Attributes:
        code: The updated source string.
        tree: The parsed tree for ``code`` if ``reparse`` was requested.
    """

    code: str
    tree: Optional[Tree] = None


class CppAst:
    """Thin wrapper around a Tree-sitter C++ parser.

    The constructor attempts to load the pre-built C++ grammar from
    :mod:`tree_sitter_languages`.  In environments where the compiled
    grammars are unavailable (e.g. missing wheels for the running Python
    version) the object is still created but ``parse`` will raise a
    :class:`RuntimeError`.  This allows callers and tests to gracefully
    skip AST-edit features when the dependency is missing.
    """

    def __init__(self) -> None:
        self._init_error: Exception | None = None
        if get_parser is None:
            self.parser = None
            self._init_error = _PARSER_ERROR
        else:
            try:
                self.parser = get_parser("cpp")
            except Exception as exc:  # pragma: no cover - missing grammar
                self.parser = None
                self._init_error = exc

    def parse(self, code: str) -> Tree:
        """Parse ``code`` into a :class:`Tree`."""

        if self.parser is None:
            raise RuntimeError(
                "Tree-sitter C++ parser unavailable"
            ) from self._init_error
        return self.parser.parse(bytes(code, "utf8"))

    def replace(self, code: str, node: Node, replacement: str, *, reparse: bool = True) -> EditResult:
        """Replace the text covered by ``node`` with ``replacement``.

        Parameters
        ----------
        code:
            Original source code.
        node:
            Node whose span will be replaced.
        replacement:
            Text to insert in place of the node.
        reparse:
            Whether to reparse the updated code and include the new tree in
            the result.
        """

        new_code = code[: node.start_byte] + replacement + code[node.end_byte :]
        new_tree = self.parse(new_code) if reparse else None
        return EditResult(new_code, new_tree)

    def insert(self, code: str, position: int, text: str, *, reparse: bool = True) -> EditResult:
        """Insert ``text`` at ``position`` (byte offset).

        ``position`` must be a byte index into ``code``.  The new tree is
        returned when ``reparse`` is True.
        """

        new_code = code[:position] + text + code[position:]
        new_tree = self.parse(new_code) if reparse else None
        return EditResult(new_code, new_tree)

    def delete(self, code: str, node: Node, *, reparse: bool = True) -> EditResult:
        """Remove the text covered by ``node``."""

        return self.replace(code, node, "", reparse=reparse)

    def is_valid(self, code: str) -> bool:
        """Return True if ``code`` parses successfully as C++."""

        try:
            self.parse(code)
            return True
        except Exception:
            return False
