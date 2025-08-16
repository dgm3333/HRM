"""Simple token based code encoder.

The encoder builds a vocabulary from provided samples and can
convert C++ source into token ids and back again.  It purposely keeps
the implementation light‑weight so it can be used in early HRM
experiments before a more sophisticated AST‑based encoder is added.
"""
from __future__ import annotations

from typing import Iterable, List, Dict

from .code_tokenizer import CppTokenizer


class CodeEncoder:
    """Naïve C++ token encoder."""

    def __init__(self, vocab: Iterable[str] | None = None) -> None:
        self.tokenizer = CppTokenizer()
        self.vocab: Dict[str, int] = {}
        if vocab is not None:
            for tok in vocab:
                self.vocab.setdefault(tok, len(self.vocab))
        # Reserve an unknown token id for unseen tokens.
        self.unk_token = "<unk>"
        self.vocab.setdefault(self.unk_token, len(self.vocab))

    def build_vocab(self, samples: Iterable[str]) -> None:
        """Populate the vocabulary based on *samples* of source code."""
        for tok in self.tokenizer.build_vocab(samples):
            self.vocab.setdefault(tok, len(self.vocab))

    def encode(self, code: str) -> List[int]:
        """Encode C++ *code* into a list of token ids."""
        ids: List[int] = []
        for tok in self.tokenizer.tokenize(code):
            ids.append(self.vocab.get(tok, self.vocab[self.unk_token]))
        return ids

    def decode(self, ids: Iterable[int]) -> str:
        """Decode *ids* back into a whitespace separated string."""
        rev_vocab = {i: tok for tok, i in self.vocab.items()}
        return " ".join(rev_vocab.get(i, self.unk_token) for i in ids)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.vocab)
