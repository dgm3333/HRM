"""Run GoogleTest binaries and collect JUnit XML results.

This module executes a compiled GoogleTest binary and parses the
resulting JUnit-style XML report into a Python structure.  A sandbox
adapter such as :class:`~runners.isolate.IsolateRunner` may be supplied
to enforce resource limits and disable networking.  When no sandbox is
provided the binary is executed directly via :mod:`subprocess`.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from .isolate import IsolateRunner, SandboxError


class GTestExecutionError(RuntimeError):
    """Raised when a gtest binary fails to produce valid XML."""


def _parse_gtest_xml(xml: str) -> Dict[str, object]:
    """Parse GoogleTest XML output into a simple dictionary."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:  # pragma: no cover - defensive
        raise GTestExecutionError("invalid gtest XML") from exc

    cases: List[Dict[str, object]] = []
    for suite in root.findall("testsuite"):
        for case in suite.findall("testcase"):
            cases.append(
                {
                    "suite": suite.get("name", ""),
                    "name": case.get("name", ""),
                    "classname": case.get("classname", ""),
                    "time": float(case.get("time", "0") or 0),
                    "passed": case.find("failure") is None,
                }
            )
    return {
        "tests": int(root.get("tests", 0)),
        "failures": int(root.get("failures", 0)),
        "errors": int(root.get("errors", 0)),
        "cases": cases,
        "xml": xml,
    }


def run_gtests(
    binary: Path,
    *,
    sandbox: Optional[IsolateRunner] = None,
    time_limit: int = 5,
    wall_time: int = 5,
    memory: int = 256 * 1024,
) -> Dict[str, object]:
    """Execute ``binary`` and return parsed GoogleTest results.

    Parameters
    ----------
    binary:
        Path to the compiled GoogleTest executable.
    sandbox:
        Optional :class:`IsolateRunner` to enforce resource limits.
    time_limit, wall_time, memory:
        Resource limits forwarded to the sandbox runner.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        xml_path = Path(tmpdir) / "report.xml"
        cmd = [str(binary), f"--gtest_output=xml:{xml_path}"]
        if sandbox is not None:
            try:
                proc = sandbox.run(
                    cmd,
                    time_limit=time_limit,
                    wall_time=wall_time,
                    memory=memory,
                )
            except SandboxError as exc:  # pragma: no cover - defensive
                raise GTestExecutionError("sandbox execution failed") from exc
        else:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if proc.returncode != 0:
            raise GTestExecutionError(
                f"gtest binary exited with code {proc.returncode}"
            )
        if not xml_path.exists():  # pragma: no cover - defensive
            raise GTestExecutionError("gtest did not produce XML output")
        xml = xml_path.read_text()
    return _parse_gtest_xml(xml)
