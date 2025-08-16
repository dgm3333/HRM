"""Sandbox runner adapters for HRM Coder."""

from .gvisor import GVisorRunner
from .io_judge import run_io_tests
from .isolate import IsolateRunner
from .nsjail import NSJailRunner
from .error_taxonomy import classify_compile, classify_runtime

__all__ = [
    "GVisorRunner",
    "IsolateRunner",
    "NSJailRunner",
    "classify_compile",
    "classify_runtime",
    "run_io_tests",
]
