import sys
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.ast_edit import CppAst


CPP_SNIPPET = """int add(int a, int b) { return a + b; }"""

_HAS_CHILD = hasattr(CppAst().parse("int x; ").root_node, "child")


@pytest.mark.skipif(not _HAS_CHILD, reason="tree-sitter Node.child not available")
def test_parse_and_basic_edits():
    try:
        ast = CppAst()
    except Exception as e:  # pragma: no cover - environment missing parser
        pytest.skip(f"Tree-sitter parser unavailable: {e}")
    tree = ast.parse(CPP_SNIPPET)
    assert tree.root_node.type == "translation_unit"

    # Replace the return expression
    func = tree.root_node.children[0]
    return_node = func.child_by_field_name("body").child(1)
    edited = ast.replace(CPP_SNIPPET, return_node, "return a - b;")
    assert ast.is_valid(edited.code)

    # Insert a simple comment at the beginning
    inserted = ast.insert(edited.code, 0, "// add two numbers\n")
    assert ast.is_valid(inserted.code)

    # Delete the comment
    comment_node = ast.parse(inserted.code).root_node.child(0)
    deleted = ast.delete(inserted.code, comment_node)
    assert ast.is_valid(deleted.code)

