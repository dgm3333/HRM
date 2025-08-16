from __future__ import annotations

"""Utilities for editing C++ code via Tree-sitter ASTs.

This module provides a minimal AST representation and an edit action
space supporting insert, replace, and delete operations. A simple
constraint checker ensures edits maintain a valid tree structure.
"""

from dataclasses import dataclass
from typing import List, Optional, Union

from tree_sitter import Parser
from tree_sitter_languages import get_language


_PARSER: Optional[Parser] = None


def _get_parser() -> Parser:
    """Lazily initialize and return a Tree-sitter parser for C++."""
    global _PARSER
    if _PARSER is None:
        parser = Parser()
        parser.set_language(get_language("cpp"))
        _PARSER = parser
    return _PARSER


@dataclass
class ASTNode:
    """Simplified AST node used for editing."""

    type: str
    start_byte: int
    end_byte: int
    children: List["ASTNode"]

    @classmethod
    def from_ts(cls, node) -> "ASTNode":
        return cls(
            type=node.type,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            children=[cls.from_ts(child) for child in node.children],
        )


def parse_cpp(code: str) -> ASTNode:
    """Parse C++ source code into an ``ASTNode`` tree."""
    parser = _get_parser()
    tree = parser.parse(code.encode("utf8"))
    return ASTNode.from_ts(tree.root_node)


def node_embedding(node: ASTNode, depth: int = 0, parent: Optional[str] = None) -> dict:
    """Return a minimal embedding for ``node`` with type/depth/parent info."""
    return {"type": node.type, "depth": depth, "parent": parent}


# --- Edit action space ----------------------------------------------------


@dataclass
class Insert:
    parent_path: List[int]
    index: int
    code: str


@dataclass
class Replace:
    target_path: List[int]
    code: str


@dataclass
class Delete:
    target_path: List[int]


Action = Union[Insert, Replace, Delete]


def _get_node(root: ASTNode, path: List[int]) -> ASTNode:
    node = root
    for idx in path:
        if idx < 0 or idx >= len(node.children):
            raise ValueError(f"invalid path {path}")
        node = node.children[idx]
    return node


def _parse_snippet(code: str) -> ASTNode:
    """Parse a C++ snippet and return its first child node."""
    snippet_root = parse_cpp(code)
    if not snippet_root.children:
        raise ValueError("snippet produced empty AST")
    return snippet_root.children[0]


def check_action(root: ASTNode, action: Action) -> None:
    """Validate that ``action`` is applicable to ``root``."""
    if isinstance(action, Insert):
        parent = _get_node(root, action.parent_path)
        if action.index < 0 or action.index > len(parent.children):
            raise ValueError("invalid insert position")
        _parse_snippet(action.code)
    elif isinstance(action, Replace):
        _get_node(root, action.target_path)
        _parse_snippet(action.code)
    elif isinstance(action, Delete):
        _get_node(root, action.target_path)
    else:  # pragma: no cover - defensive
        raise TypeError("unknown action")


class ASTEditor:
    """In-memory AST editor for C++ source."""

    def __init__(self, code: str) -> None:
        self.code = code
        self.root = parse_cpp(code)

    def apply(self, action: Action) -> None:
        """Apply ``action`` to the parsed AST."""
        check_action(self.root, action)
        if isinstance(action, Insert):
            parent = _get_node(self.root, action.parent_path)
            node = _parse_snippet(action.code)
            parent.children.insert(action.index, node)
        elif isinstance(action, Replace):
            parent_path = action.target_path[:-1]
            idx = action.target_path[-1]
            node = _parse_snippet(action.code)
            if parent_path:
                parent = _get_node(self.root, parent_path)
                parent.children[idx] = node
            else:
                self.root = node
        elif isinstance(action, Delete):
            parent_path = action.target_path[:-1]
            idx = action.target_path[-1]
            parent = _get_node(self.root, parent_path)
            del parent.children[idx]
        else:  # pragma: no cover - defensive
            raise TypeError("unknown action")
