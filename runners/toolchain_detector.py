"""Detect available compilers and coverage tools for C++ runs.

Phase 0 requires surveying the host environment for existing C++
compilers and coverage utilities.  This module inspects the current
``PATH`` for a small set of expected tools and returns structured
information describing their availability and version strings.  The
results help decide which parts of the toolchain are usable on a given
system.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from typing import Any, Dict, Optional, Tuple


class ToolInfo(Dict[str, Any]):
    """Dictionary describing an installed tool.

    Keys
    ----
    available:
        ``True`` if the binary is present on ``PATH``.
    version:
        First line of ``--version`` output (``None`` if unavailable).
    path:
        Resolved path to the binary (``None`` if missing).
    meets_requirement:
        ``True`` if the parsed version meets the Phase 0 minimum.
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


def _parse_version(line: str) -> Optional[Tuple[int, int]]:
    """Extract ``(major, minor)`` version tuple from ``line``.

    The function searches for the first ``X.Y`` pattern and returns the
    corresponding integers.  ``None`` is returned when no version pattern
    can be found.
    """

    match = re.search(r"(\d+)\.(\d+)", line)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


MIN_VERSIONS: Dict[str, Tuple[int, int]] = {
    "g++": (13, 0),
    "clang++": (17, 0),
    "llvm-cov": (17, 0),
    "gcov": (13, 0),
    "lcov": (1, 15),
}


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
        info: ToolInfo = ToolInfo(
            available=False,
            version=None,
            path=None,
            meets_requirement=False,
        )
        if path:
            info["available"] = True
            info["path"] = path
            ver = _probe_version(cmd)
            info["version"] = ver
            min_ver = MIN_VERSIONS.get(name)
            parsed = _parse_version(ver) if ver else None
            if parsed and min_ver:
                info["meets_requirement"] = parsed >= min_ver
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
        if (
            details
            and details.get("available")
            and details.get("meets_requirement", True)
        ):
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
