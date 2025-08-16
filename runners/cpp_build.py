"""Minimal CMake build helpers for Phase 1 scaffolding.

These utilities wrap ``cmake`` and ``ctest`` to compile and execute the
placeholder C++ harnesses included with the project. They intentionally
expose only a tiny subset of options required for the early deterministic
environment work. Later phases will expand the interface with richer
configuration and diagnostics.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from subprocess import CompletedProcess


def configure(
    source_dir: Path,
    build_dir: Path,
    preset: str = "sanitized",
) -> CompletedProcess:
    """Run a basic CMake configure step into ``build_dir``.

    Currently only a ``sanitized`` preset is supported which enables
    AddressSanitizer and UndefinedBehaviorSanitizer for deterministic
    debugging. The ``preset`` argument is reserved for future expansion.
    """
    build_dir.mkdir(parents=True, exist_ok=True)
    if preset != "sanitized":
        raise ValueError(f"unsupported preset: {preset}")
    cmd = [
        "cmake",
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        "-G",
        "Ninja",
        "-DCMAKE_BUILD_TYPE=Debug",
        "-DCMAKE_CXX_FLAGS=-O1 -g -fsanitize=address,undefined "
        "-fno-omit-frame-pointer",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def build(build_dir: Path) -> CompletedProcess:
    """Invoke ``cmake --build`` for the given ``build_dir``."""
    cmd = ["cmake", "--build", str(build_dir)]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def run_tests(build_dir: Path) -> CompletedProcess:
    """Execute ``ctest`` in ``build_dir`` and return the completed process."""
    cmd = ["ctest", "--test-dir", str(build_dir)]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


__all__ = ["configure", "build", "run_tests"]
