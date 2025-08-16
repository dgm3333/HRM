"""Utility classes for HRM code tasks.

This package currently exposes a C++ tokenizer and a simple
`CodeEncoder` wrapper used by the training loop.  These utilities
progress Phase 6 of the project plan by providing the minimal
infrastructure required to tokenize C++ snippets and convert them to
integer token ids for HRM models.
"""

from .code_tokenizer import CppTokenizer
from .code_encoder import CodeEncoder

__all__ = ["CppTokenizer", "CodeEncoder"]
