#!/usr/bin/env python3
"""Run a simple command inside available sandbox backends.

Phase 0 evaluates different sandbox adapters.  This script detects which
sandboxes are present on the host and attempts to execute ``/bin/echo``
inside each of them.  The outcome for every backend is reported as JSON
so that developers can quickly gauge which runners are operational.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
import sys

# Ensure repository root on module search path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runners import sandbox_detector  # noqa: E402
from runners.isolate import IsolateRunner, SandboxError as IsolateError  # noqa: E402
from runners.nsjail import NSJailRunner, SandboxError as NSJailError  # noqa: E402
from runners.gvisor import GVisorRunner, SandboxError as GVisorError  # noqa: E402


def _run_isolate(path: str) -> Dict[str, Any]:
    runner = IsolateRunner(isolate_path=path)
    try:
        proc = runner.run(["/bin/echo", "hello"], stdout_limit=1024, stderr_limit=1024)
        return {
            "available": True,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": True, "ok": False, "error": str(exc)}


def _run_nsjail(path: str) -> Dict[str, Any]:
    runner = NSJailRunner(nsjail_path=path)
    try:
        proc = runner.run(["/bin/echo", "hello"], stdout_limit=1024, stderr_limit=1024)
        return {
            "available": True,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": True, "ok": False, "error": str(exc)}


def _run_gvisor() -> Dict[str, Any]:
    runner = GVisorRunner()
    try:
        proc = runner.run(["/bin/echo", "hello"])
        return {
            "available": True,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": True, "ok": False, "error": str(exc)}


def smoke_test() -> Dict[str, Any]:
    info = sandbox_detector.detect_sandboxes()
    results: Dict[str, Any] = {}

    iso = info.get("isolate", {})
    if iso.get("available") and iso.get("path"):
        results["isolate"] = _run_isolate(iso["path"])
    else:
        results["isolate"] = {"available": False, "ok": None}

    ns = info.get("nsjail", {})
    if ns.get("available") and ns.get("path"):
        results["nsjail"] = _run_nsjail(ns["path"])
    else:
        results["nsjail"] = {"available": False, "ok": None}

    gv = info.get("runsc", {})
    if gv.get("available"):
        results["runsc"] = _run_gvisor()
    else:
        results["runsc"] = {"available": False, "ok": None}

    return results


def main() -> None:
    print(json.dumps(smoke_test(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
