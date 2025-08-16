from hrm_coder.inventory import inventory_package, find_injection_points


def test_inventory_finds_code_encoder_and_tokenizer() -> None:
    inv = inventory_package("hrm")
    points = find_injection_points(inv)
    assert "hrm.code_encoder.CodeEncoder" in points
    assert "hrm.code_tokenizer.CppTokenizer" in points
