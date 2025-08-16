import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from hrm.ast_encoder import ASTEncoder  # noqa: E402

CPP_SNIPPET = """int add(int a, int b) { return a + b; }"""


def _parser_available() -> bool:
    try:
        enc = ASTEncoder()
        enc.encode("int x;")
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _parser_available(), reason="Tree-sitter parser unavailable"
)
def test_encode_produces_node_ids():
    enc = ASTEncoder()
    ids = enc.encode(CPP_SNIPPET)
    assert ids[0] == enc.schema.id_for("translation_unit")
    assert len(ids) > 3


@pytest.mark.skipif(
    not _parser_available(), reason="Tree-sitter parser unavailable"
)
def test_encode_with_depth():
    enc = ASTEncoder()
    pairs = enc.encode_with_depth(CPP_SNIPPET)
    # root node at depth 0
    assert pairs[0] == (enc.schema.id_for("translation_unit"), 0)
    # ensure there is a node deeper than root
    assert any(depth > 0 for _, depth in pairs)


@pytest.mark.skipif(
    not _parser_available(), reason="Tree-sitter parser unavailable"
)
def test_encode_with_parents():
    enc = ASTEncoder()
    triples = enc.encode_with_parents(CPP_SNIPPET)
    root_id = enc.schema.id_for("translation_unit")
    # first triple corresponds to root
    assert triples[0] == (root_id, -1, 0)
    # ensure at least one child reports root as parent
    assert any(
        parent == root_id and depth == 1 for _, parent, depth in triples
    )
