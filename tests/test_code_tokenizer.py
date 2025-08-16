import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from hrm import CppTokenizer, CodeEncoder


def test_tokenizer_removes_comments_and_splits_tokens():
    code = """
    // comment line
    int main() {
        /* block comment */
        std::string s = "hi";
        return 0; // trailing
    }
    """
    toks = CppTokenizer().tokenize(code)
    assert "comment" not in toks
    assert toks == [
        "int",
        "main",
        "(",
        ")",
        "{",
        "std",
        ":",
        ":",
        "string",
        "s",
        "=",
        '"hi"',
        ";",
        "return",
        "0",
        ";",
        "}",
    ]


def test_code_encoder_round_trip():
    samples = ["int x = 1;", "int y = x + 2;"]
    encoder = CodeEncoder()
    encoder.build_vocab(samples)
    ids = encoder.encode("int y = x + 2;")
    decoded = encoder.decode(ids)
    assert decoded.split() == CppTokenizer().tokenize("int y = x + 2;")
