"""Phase 0 environment audit CLI.

This lightweight command line interface inspects the current
environment and prints information useful during Phase 0 of the
hrm-coder project.  It reports potential injection points in the
``hrm`` package as well as available sandbox backends and C++
toolchain components.
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .inventory import inventory_package, find_injection_points
from runners import sandbox_detector, toolchain_detector


def perform_audit(package: str = "hrm") -> Dict[str, Any]:
    """Collect audit information for ``package``.

    Returns a dictionary containing injection points, sandbox detection
    results and toolchain detection results.  The function is separated
    from the CLI to facilitate unit testing.
    """

    inventory = inventory_package(package)
    injection_points = find_injection_points(inventory)
    sandboxes = sandbox_detector.detect_sandboxes()
    toolchains = toolchain_detector.detect_toolchains()
    return {
        "injection_points": injection_points,
        "sandboxes": sandboxes,
        "toolchains": toolchains,
    }


def _format_available(info: Dict[str, Any]) -> str:
    return "available" if info.get("available") else "missing"


def _print_audit(data: Dict[str, Any]) -> None:
    print("Injection points:")
    for point in data["injection_points"]:
        print(f" - {point}")

    print("\nSandboxes:")
    for name, info in data["sandboxes"].items():
        status = _format_available(info)
        ver = f" ({info['version']})" if info.get("version") else ""
        print(f" - {name}: {status}{ver}")

    print("\nToolchains:")
    for name, info in data["toolchains"].items():
        status = _format_available(info)
        meets = " (meets requirement)" if info.get("meets_requirement") else ""
        ver = f" ({info['version']})" if info.get("version") else ""
        print(f" - {name}: {status}{meets}{ver}")


def main() -> None:  # pragma: no cover - exercised via tests
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package", default="hrm", help="Python package to inspect"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of text",
    )
    args = parser.parse_args()
    data = perform_audit(args.package)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        _print_audit(data)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
