"""Light‑weight C++ tokenization utilities.

The tokenizer is intentionally simple and keeps dependencies minimal.
It recognises comments, string/character literals, identifiers,
keywords and common operators.  Comments are stripped during
tokenisation so that reward calculations and training are not polluted
by non‑semantic text.
"""
from __future__ import annotations

import re
from typing import Iterable, List

# Borrowed from the C++ standard.  The list is not exhaustive but covers
# tokens used in introductory competitive‑programming style problems
# targeted by the project.
CPP_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
    "bool", "break", "case", "catch", "char", "char16_t", "char32_t",
    "class", "compl", "const", "constexpr", "const_cast", "continue",
    "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern", "false", "float",
    "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
    "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator",
    "or", "or_eq", "private", "protected", "public", "register",
    "reinterpret_cast", "return", "short", "signed", "sizeof", "static",
    "static_assert", "static_cast", "struct", "switch", "template",
    "this", "thread_local", "throw", "true", "try", "typedef",
    "typeid", "typename", "union", "unsigned", "using", "virtual",
    "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
}

# Regex adapted from CPython's Lib/tokenize.py but extended for C++
# operators.  It intentionally keeps the implementation compact and
# avoids pulling in heavy parser packages such as tree‑sitter.
TOKEN_REGEX = re.compile(
    r"//.*?$|/\*.*?\*/|"  # C++ comments
    r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|"  # string & char literals
    r"[A-Za-z_][A-Za-z0-9_]*|"  # identifiers/keywords
    r"\d+\.\d+|\d+|"  # numbers
    r"==|!=|<=|>=|->|&&|\|\||"  # multi-char operators
    r"[+\-*/%&|^~<>?:=,!;{}()\[\].]",  # single-char tokens
    re.DOTALL | re.MULTILINE,
)


def tokenize(code: str) -> List[str]:
    """Tokenise *code* and return a list of string tokens.

    Comments are removed.  The tokenizer is deterministic which enables
    reproducible training and evaluation.
    """
    tokens: List[str] = []
    for match in TOKEN_REGEX.finditer(code):
        tok = match.group(0)
        if tok.startswith("//") or tok.startswith("/*"):
            continue
        tokens.append(tok)
    return tokens


def build_vocab(samples: Iterable[str]) -> List[str]:
    """Create a vocabulary from *samples* of source code."""
    vocab = []
    seen = set()
    for code in samples:
        for tok in tokenize(code):
            if tok not in seen:
                vocab.append(tok)
                seen.add(tok)
    return vocab


class CppTokenizer:
    """Small helper class used by :class:`CodeEncoder`.

    It exposes :py:meth:`tokenize` and :py:meth:`build_vocab` for
    external consumers.
    """

    def tokenize(self, code: str) -> List[str]:
        return tokenize(code)

    def build_vocab(self, samples: Iterable[str]) -> List[str]:
        return build_vocab(samples)
