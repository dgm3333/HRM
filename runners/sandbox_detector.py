"""Utility functions to detect available sandbox backends.

Phase 0 focuses on evaluating existing sandboxing options.  This module
provides a small helper that inspects the current environment for the
presence of ``isolate``, ``nsjail`` and gVisor's ``runsc`` runtime.  It
returns structured information that can be used to decide which adapter
is usable on a given system.
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Dict, Optional


class SandboxInfo(Dict[str, Optional[str]]):
    """Dictionary describing a sandbox binary.

    Keys
    ----
    available:
        ``True`` if the binary is present on ``PATH``.
    version:
        Version string reported by ``--version`` (``None`` if unknown).
    path:
        Resolved path to the binary (``None`` if missing).
    """


def _probe_version(cmd: str) -> Optional[str]:
    """Return the first line of ``cmd --version`` if it executes successfully."""
    try:
        proc = subprocess.run([cmd, "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    line = proc.stdout.strip().splitlines()
    return line[0] if line else None


def detect_sandboxes() -> Dict[str, SandboxInfo]:
    """Detect availability of supported sandbox tools.

    Returns a mapping from sandbox name (``isolate``, ``nsjail``, ``runsc``)
    to :class:`SandboxInfo` entries describing presence and version
    information.  Missing binaries are reported with ``available=False``.
    """
    tools = {
        "isolate": "isolate",
        "nsjail": "nsjail",
        "runsc": "runsc",
    }
    results: Dict[str, SandboxInfo] = {}
    for name, binary in tools.items():
        path = shutil.which(binary)
        info: SandboxInfo = SandboxInfo(available=False, version=None, path=None)
        if path:
            info["available"] = True
            info["path"] = path
            info["version"] = _probe_version(binary)
        results[name] = info
    return results
