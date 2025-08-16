#!/usr/bin/env python3
"""Report available sandbox and C++ toolchain components.

This Phase 0 helper combines the sandbox and toolchain detectors to
summarize the host environment.  The output is JSON and can be used to
quickly assess whether required dependencies are installed before
running more involved HRM Coder tasks.
"""
from __future__ import annotations

import json
import platform
from typing import Any, Dict

from pathlib import Path
import sys

# Ensure repository root is on the module search path so local packages can
# be imported when this script is executed as a standalone file.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runners import sandbox_detector, toolchain_detector  # noqa: E402


def build_report() -> Dict[str, Any]:
    """Collect sandbox and toolchain availability information."""
    sandboxes = sandbox_detector.detect_sandboxes()
    selected, _ = sandbox_detector.select_sandbox(info=sandboxes)
    return {
        "python": platform.python_version(),
        "sandboxes": sandboxes,
        "default_sandbox": selected,
        "toolchains": toolchain_detector.detect_toolchains(),
    }


def main() -> None:
    print(json.dumps(build_report(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
