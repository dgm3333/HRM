import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from utils.ast_cursor import CursorPolicy, find_node_by_type  # noqa: E402
from utils.ast_edit import CppAst  # noqa: E402

CPP_SNIPPET = "int add(int a, int b) { return a + b; }"


def _parser_available() -> bool:
    try:
        CppAst().parse("int x;")
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _parser_available(), reason="Tree-sitter parser unavailable"
)
def test_cursor_policy_selects_node():
    ast = CppAst()
    tree = ast.parse(CPP_SNIPPET)
    policy = CursorPolicy(lambda n: n.type == "return_statement")
    node = policy.select(tree)
    assert node is not None
    assert node.type == "return_statement"


@pytest.mark.skipif(
    not _parser_available(), reason="Tree-sitter parser unavailable"
)
def test_find_node_by_type():
    ast = CppAst()
    tree = ast.parse(CPP_SNIPPET)
    node = find_node_by_type(tree, "function_definition")
    assert node is not None
    assert node.type == "function_definition"
