"""Cursor policy helpers for Tree-sitter C++ ASTs.

This module provides a very small utility used in Phase 9 of the HRM
Coder roadmap.  A :class:`CursorPolicy` represents a strategy for selecting
an AST node to target for an edit.  Policies are expressed as predicates
over :class:`tree_sitter.Node` instances and the ``select`` method walks the
parse tree in breadth‑first order returning the first node that satisfies
the predicate.

The initial implementation is intentionally simple – it supports only
predicate based searches and returns the first match.  It can be expanded in
later phases with scores, multi-node selections or learned policies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from tree_sitter import Node, Tree


Predicate = Callable[[Node], bool]


@dataclass
class CursorPolicy:
    """Select nodes from a Tree-sitter :class:`Tree` using a predicate.

    Parameters
    ----------
    predicate:
        Function returning ``True`` for nodes that satisfy the policy.
    """

    predicate: Predicate

    def select(self, tree: Tree) -> Optional[Node]:
        """Return the first node in ``tree`` that matches ``predicate``.

        The traversal uses a breadth-first search which tends to prefer
        shallower nodes and keeps the walk deterministic.
        """

        queue = [tree.root_node]
        while queue:
            node = queue.pop(0)
            if self.predicate(node):
                return node
            queue.extend(node.children)
        return None


def find_node_by_type(tree: Tree, node_type: str) -> Optional[Node]:
    """Convenience helper to locate the first node of ``node_type``.

    Parameters
    ----------
    tree:
        Parsed Tree-sitter tree.
    node_type:
        Node type string to search for.
    """

    policy = CursorPolicy(lambda n: n.type == node_type)
    return policy.select(tree)
