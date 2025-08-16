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
from typing import Dict, Optional, Tuple


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


def _select_tool(
    names: Tuple[str, ...], info: Optional[Dict[str, ToolInfo]] = None
) -> Tuple[Optional[str], Optional[ToolInfo]]:
    """Return first available tool from ``names``.

    This helper mirrors the sandbox selection logic used elsewhere in
    Phase 0.  ``names`` is a tuple of tool identifiers in priority order.
    ``info`` allows callers to pass precomputed detection results to
    avoid repeated ``PATH`` scans.
    """

    if info is None:
        info = detect_toolchains()
    for name in names:
        details = info.get(name)
        if details and details.get("available"):
            return name, details
    return None, None


def select_compiler(
    preference: Tuple[str, ...] = ("g++", "clang++"),
    info: Optional[Dict[str, ToolInfo]] = None,
) -> Tuple[Optional[str], Optional[ToolInfo]]:
    """Choose the first available C++ compiler from ``preference``."""

    return _select_tool(preference, info)


def select_coverage_tool(
    preference: Tuple[str, ...] = ("llvm-cov", "gcov", "lcov"),
    info: Optional[Dict[str, ToolInfo]] = None,
) -> Tuple[Optional[str], Optional[ToolInfo]]:
    """Choose the first available coverage tool from ``preference``."""

    return _select_tool(preference, info)


__all__ = [
    "detect_toolchains",
    "select_compiler",
    "select_coverage_tool",
    "ToolInfo",
]
