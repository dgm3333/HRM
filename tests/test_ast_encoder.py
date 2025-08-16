from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from hrm.ast_encoder import ASTEncoder

CPP_SNIPPET = """int add(int a, int b) { return a + b; }"""


def _parser_available() -> bool:
    try:
        enc = ASTEncoder()
        enc.encode("int x;")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _parser_available(), reason="Tree-sitter parser unavailable")
def test_encode_produces_node_ids():
    enc = ASTEncoder()
    ids = enc.encode(CPP_SNIPPET)
    assert ids[0] == enc.schema.id_for("translation_unit")
    assert len(ids) > 3


@pytest.mark.skipif(not _parser_available(), reason="Tree-sitter parser unavailable")
def test_encode_with_depth():
    enc = ASTEncoder()
    pairs = enc.encode_with_depth(CPP_SNIPPET)
    # root node at depth 0
    assert pairs[0] == (enc.schema.id_for("translation_unit"), 0)
    # ensure there is a node deeper than root
    assert any(depth > 0 for _, depth in pairs)
