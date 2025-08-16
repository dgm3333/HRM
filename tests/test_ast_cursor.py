import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.ast_edit import CppAst
from utils.ast_cursor import CursorPolicy, find_node_by_type

CPP_SNIPPET = """int add(int a, int b) { return a + b; }"""


def _parser_available() -> bool:
    try:
        ast = CppAst()
        ast.parse("int x;")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _parser_available(), reason="Tree-sitter parser unavailable")
def test_find_node_by_type():
    ast = CppAst()
    tree = ast.parse(CPP_SNIPPET)
    func = find_node_by_type(tree, "function_definition")
    assert func is not None
    assert func.type == "function_definition"


@pytest.mark.skipif(not _parser_available(), reason="Tree-sitter parser unavailable")
def test_cursor_policy_with_custom_predicate():
    ast = CppAst()
    tree = ast.parse(CPP_SNIPPET)
    # predicate that selects the return statement
    policy = CursorPolicy(lambda n: n.type == "return_statement")
    node = policy.select(tree)
    assert node is not None
    assert node.type == "return_statement"
