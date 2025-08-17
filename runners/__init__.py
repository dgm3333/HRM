"""Sandbox runner adapters for HRM Coder."""

from .gvisor import GVisorRunner
from .io_judge import run_io_tests
from .isolate import IsolateRunner
from .nsjail import NSJailRunner
from .error_taxonomy import classify_compile, classify_runtime
from .binary_adapter import BinarySandboxAdapter, SANITIZER_ENV
from .codeforces_harness import (
    IOPair,
    build_io_harness,
    run_io_harness,
    summarize_result,
)
from . import sandbox_detector, toolchain_detector

__all__ = [
    "GVisorRunner",
    "IsolateRunner",
    "NSJailRunner",
    "BinarySandboxAdapter",
    "SANITIZER_ENV",
    "classify_compile",
    "classify_runtime",
    "run_io_tests",
    "IOPair",
    "build_io_harness",
    "run_io_harness",
    "summarize_result",
    "sandbox_detector",
    "toolchain_detector",
]
