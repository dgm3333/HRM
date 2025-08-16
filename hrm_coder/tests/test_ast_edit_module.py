import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from hrm_coder.ast_edit import ASTEditor, Delete, Insert, node_embedding, parse_cpp


def test_parse_and_embedding():
    root = parse_cpp("int main(){ return 0; }")
    assert root.type == "translation_unit"
    emb = node_embedding(root)
    assert emb["type"] == "translation_unit"


def test_insert_and_delete_roundtrip():
    editor = ASTEditor("int main(){ return 0; }")
    insert = Insert(parent_path=[0, 2], index=1, code="int x = 0;")
    editor.apply(insert)
    body = editor.root.children[0].children[2]
    assert body.children[1].type == "declaration"

    delete = Delete(target_path=[0, 2, 1])
    editor.apply(delete)
    body = editor.root.children[0].children[2]
    assert len(body.children) == 3


def test_invalid_delete_path():
    editor = ASTEditor("int main(){ return 0; }")
    with pytest.raises(ValueError):
        editor.apply(Delete(target_path=[1]))
