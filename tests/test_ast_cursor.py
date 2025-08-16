import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from utils.ast_edit import CppAst  # noqa: E402
from utils.ast_cursor import (  # noqa: E402
    CursorPolicy,
    ScoredCursorPolicy,
    find_node_by_type,
)

CPP_SNIPPET = """int add(int a, int b) { return a + b; }"""
REASON = "Tree-sitter parser unavailable"


def _parser_available() -> bool:
    try:
        ast = CppAst()
        ast.parse("int x;")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _parser_available(), reason=REASON)
def test_find_node_by_type():
    ast = CppAst()
    tree = ast.parse(CPP_SNIPPET)
    func = find_node_by_type(tree, "function_definition")
    assert func is not None
    assert func.type == "function_definition"


@pytest.mark.skipif(not _parser_available(), reason=REASON)
def test_cursor_policy_with_custom_predicate():
    ast = CppAst()
    tree = ast.parse(CPP_SNIPPET)
    # predicate that selects the return statement
    policy = CursorPolicy(lambda n: n.type == "return_statement")
    node = policy.select(tree)
    assert node is not None
    assert node.type == "return_statement"


@pytest.mark.skipif(not _parser_available(), reason=REASON)
def test_scored_cursor_policy_prefers_high_score():
    ast = CppAst()
    tree = ast.parse(CPP_SNIPPET)

    def scorer(node):
        return 1.0 if node.type == "return_statement" else 0.0

    policy = ScoredCursorPolicy(scorer)
    node = policy.select(tree)
    assert node is not None
    assert node.type == "return_statement"
