from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.ast_actions import DeleteAction, InsertAction, ReplaceAction
from utils.ast_constraints import ConstraintChecker
from utils.ast_edit import CppAst

CPP_SNIPPET = "int add(int a, int b) { return a + b; }"


def _parser_available() -> bool:
    try:
        ast = CppAst()
        ast.parse("int x;")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _parser_available(), reason="Tree-sitter parser unavailable")
def test_actions_and_constraints():
    ast = CppAst()
    checker = ConstraintChecker(ast)
    tree = ast.parse(CPP_SNIPPET)
    func = tree.root_node.children[0]
    body = func.child_by_field_name("body")
    return_node = body.child(1)

    replace_action = ReplaceAction(return_node, "return a - b;")
    assert checker.is_valid_edit(CPP_SNIPPET, replace_action)

    bad_action = ReplaceAction(return_node, "return ;")
    assert not checker.is_valid_edit(CPP_SNIPPET, bad_action)

    insert_action = InsertAction(0, "// comment\n")
    assert checker.is_valid_edit(CPP_SNIPPET, insert_action)

    delete_action = DeleteAction(return_node)
    assert checker.is_valid_edit(CPP_SNIPPET, delete_action)
