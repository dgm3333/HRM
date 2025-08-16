"""Cursor policy helpers for Tree-sitter C++ ASTs.

This module provides a very small utility used in Phase 9 of the HRM
Coder roadmap.  A :class:`CursorPolicy` represents a strategy for selecting
an AST node to target for an edit.  Policies are expressed as predicates
over :class:`tree_sitter.Node` instances and the ``select`` method walks the
parse tree in breadth‑first order returning the first node that satisfies
the predicate.

The initial implementation is intentionally simple – it supports only
predicate based searches and returns the first match.  For Phase 9 we also
include a tiny scored policy that walks the tree once and returns the node
with the highest score.  This serves as a lightweight placeholder for a
future learned cursor module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from tree_sitter import Node, Tree


Predicate = Callable[[Node], bool]
ScoreFn = Callable[[Node], float]


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


@dataclass
class ScoredCursorPolicy:
    """Select the node with the highest ``scorer`` value.

    The traversal is breadth‑first and considers all nodes.  If ``predicate``
    is provided, only nodes satisfying it are scored.
    """

    scorer: ScoreFn
    predicate: Optional[Predicate] = None

    def select(self, tree: Tree) -> Optional[Node]:
        best_score = float("-inf")
        best_node: Optional[Node] = None
        queue = [tree.root_node]
        while queue:
            node = queue.pop(0)
            if self.predicate is None or self.predicate(node):
                score = self.scorer(node)
                if score > best_score:
                    best_score = score
                    best_node = node
            queue.extend(node.children)
        return best_node


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
