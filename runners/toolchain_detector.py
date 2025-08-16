"""Detect available compilers and coverage tools for C++ runs.

Phase 0 requires surveying the host environment for existing C++
compilers and coverage utilities.  This module inspects the current
``PATH`` for a small set of expected tools and returns structured
information describing their availability and version strings.  The
results help decide which parts of the toolchain are usable on a given
system.
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Dict, Optional


class ToolInfo(Dict[str, Optional[str]]):
    """Dictionary describing an installed tool.

    Keys
    ----
    available:
        ``True`` if the binary is present on ``PATH``.
    version:
        First line of ``--version`` output (``None`` if unavailable).
    path:
        Resolved path to the binary (``None`` if missing).
    """


def _probe_version(cmd: list[str]) -> Optional[str]:
    """Return the first line of ``cmd`` output if it executes successfully."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    line = proc.stdout.strip().splitlines()
    return line[0] if line else None


def detect_toolchains() -> Dict[str, ToolInfo]:
    """Detect availability of common compiler and coverage utilities."""
    tools = {
        "g++": ["g++", "--version"],
        "clang++": ["clang++", "--version"],
        "lcov": ["lcov", "--version"],
        "llvm-cov": ["llvm-cov", "--version"],
        "gcov": ["gcov", "--version"],
    }
    results: Dict[str, ToolInfo] = {}
    for name, cmd in tools.items():
        path = shutil.which(cmd[0])
        info: ToolInfo = ToolInfo(available=False, version=None, path=None)
        if path:
            info["available"] = True
            info["path"] = path
            info["version"] = _probe_version(cmd)
        results[name] = info
    return results


__all__ = ["detect_toolchains", "ToolInfo"]
