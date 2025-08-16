"""AST-based encoder for C++ source code.

This module provides a minimal :class:`ASTEncoder` used in Phase 9 of the
HRM Coder roadmap.  It converts the Tree-sitter parse tree of a C++ source
string into a sequence of integer node-type ids.  The mapping from node type
strings to ids is managed by :class:`NodeTypeSchema` and is populated lazily
as new node kinds are encountered.

The encoder is deliberately lightweight – it captures node types in a
pre-order traversal and can optionally emit structural information like
node depth and the parent node type.  Future iterations can extend this to
richer embeddings (e.g. typed edges or siblings).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from tree_sitter import Node, Parser, Tree

try:  # pragma: no cover - optional dependency may be missing
    from tree_sitter_languages import get_parser
except Exception as exc:  # pragma: no cover
    get_parser = None  # type: ignore[assignment]
    _PARSER_ERROR = exc


class NodeTypeSchema:
    """Maps Tree-sitter node type strings to integer ids."""

    def __init__(self) -> None:
        self._type_to_id: Dict[str, int] = {}

    def id_for(self, node_type: str) -> int:
        """Return the id for ``node_type`` creating a new entry if needed."""

        if node_type not in self._type_to_id:
            self._type_to_id[node_type] = len(self._type_to_id)
        return self._type_to_id[node_type]

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._type_to_id)


@dataclass
class ASTEncoder:
    """Encode C++ source code as a sequence of node-type ids."""

    schema: NodeTypeSchema = field(default_factory=NodeTypeSchema)
    parser: Parser | None = field(init=False, default=None)
    _init_error: Exception | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        if get_parser is None:
            self._init_error = _PARSER_ERROR
        else:
            try:
                self.parser = get_parser("cpp")
            except Exception as exc:  # pragma: no cover
                self._init_error = exc

    def _traverse(self, node: Node, out: List[int]) -> None:
        out.append(self.schema.id_for(node.type))
        for child in node.children:
            self._traverse(child, out)

    def encode(self, code: str) -> List[int]:
        """Return the node-type ids for ``code`` in a pre-order traversal."""

        if self.parser is None:
            raise RuntimeError(
                "Tree-sitter C++ parser unavailable"
            ) from self._init_error
        tree: Tree = self.parser.parse(code.encode("utf8"))
        ids: List[int] = []
        self._traverse(tree.root_node, ids)
        return ids

    def encode_with_depth(self, code: str) -> List[Tuple[int, int]]:
        """Return ``(node_type_id, depth)`` pairs for ``code``."""

        if self.parser is None:
            raise RuntimeError(
                "Tree-sitter C++ parser unavailable"
            ) from self._init_error
        tree: Tree = self.parser.parse(code.encode("utf8"))
        result: List[Tuple[int, int]] = []

        def walk(n: Node, depth: int) -> None:
            result.append((self.schema.id_for(n.type), depth))
            for child in n.children:
                walk(child, depth + 1)

        walk(tree.root_node, 0)
        return result

    def encode_with_parents(self, code: str) -> List[Tuple[int, int, int]]:
        """Return ``(node_id, parent_id, depth)`` triples for ``code``.

        ``parent_id`` for the root node is ``-1``. This helper is useful for
        lightweight structural embeddings where the model consumes the node
        type along with its depth and parent type.
        """

        if self.parser is None:
            raise RuntimeError(
                "Tree-sitter C++ parser unavailable"
            ) from self._init_error

        tree: Tree = self.parser.parse(code.encode("utf8"))
        triples: List[Tuple[int, int, int]] = []

        def walk(n: Node, parent_id: int, depth: int) -> None:
            node_id = self.schema.id_for(n.type)
            triples.append((node_id, parent_id, depth))
            for child in n.children:
                walk(child, node_id, depth + 1)

        walk(tree.root_node, -1, 0)
        return triples
