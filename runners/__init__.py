"""Sandbox runner adapters for HRM Coder."""

from .gvisor import GVisorRunner
from .io_judge import run_io_tests
from .isolate import IsolateRunner
from .nsjail import NSJailRunner
from .error_taxonomy import classify_compile, classify_runtime
from .binary_adapter import BinarySandboxAdapter, SANITIZER_ENV
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
    "sandbox_detector",
    "toolchain_detector",
]
