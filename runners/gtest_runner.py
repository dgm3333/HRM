"""Run GoogleTest binaries and collect JUnit XML results.

This module executes a compiled GoogleTest binary and parses the
resulting JUnit-style XML report into a Python structure.  A sandbox
adapter such as :class:`~runners.isolate.IsolateRunner` may be supplied
to enforce resource limits and disable networking.  When no sandbox is
provided the binary is executed directly via :mod:`subprocess`.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from xml.etree import ElementTree as ET

from .isolate import IsolateRunner, SandboxError
from .sandbox_cache import SandboxCache


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


def _parse_gcov_file(path: Path) -> float:
    """Return line coverage ratio from a ``gcov`` report file."""
    executed = 0
    total = 0
    for line in path.read_text().splitlines():
        parts = line.split(":", 2)
        if len(parts) < 2:
            continue
        count = parts[0].strip()
        if count in ("-", "====="):
            continue
        if count == "#####":
            total += 1
            continue
        try:
            num = int(count)
        except ValueError:
            continue
        total += 1
        if num > 0:
            executed += 1
    return executed / total if total else 0.0


def _collect_coverage(sources: Sequence[Path], workdir: Path) -> float:
    """Run ``gcov`` on ``sources`` in ``workdir`` and average coverage."""
    if shutil.which("gcov") is None:
        return 0.0
    covs: List[float] = []
    for src in sources:
        subprocess.run(
            ["gcov", str(src), "-o", str(workdir)],
            capture_output=True,
            text=True,
            cwd=str(workdir),
            check=False,
        )
        gcov_file = workdir / f"{src.name}.gcov"
        if gcov_file.exists():
            covs.append(_parse_gcov_file(gcov_file))
    return sum(covs) / len(covs) if covs else 0.0


def run_gtests(
    binary: Path,
    *,
    sandbox: Optional[IsolateRunner] = None,
    time_limit: int = 5,
    wall_time: int = 5,
    memory: int = 256 * 1024,
    cache: Optional[SandboxCache] = None,
    collect_coverage: bool = False,
    sources: Optional[Sequence[Path]] = None,
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
    cache:
        Optional :class:`SandboxCache` instance used to memoize results for
        identical binaries and limits.
    collect_coverage:
        When ``True`` compute a line coverage ratio for ``sources`` using
        ``gcov``.  The binary must have been built with ``--coverage`` flags.
    sources:
        Sequence of source files corresponding to the compiled
        binary. Required when ``collect_coverage`` is ``True``.
    """

    key: Optional[str] = None
    if cache is not None:
        parts = [
            binary.read_bytes(),
            str(time_limit).encode(),
            str(wall_time).encode(),
            str(memory).encode(),
        ]
        if collect_coverage:
            if not sources:
                raise ValueError("sources must be provided for coverage")
            for src in sources:
                parts.append(Path(src).read_bytes())
            parts.append(b"coverage")
        key = cache.hash_parts(parts)
        cached = cache.load(key)
        if cached is not None:
            return cached

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
            proc = subprocess.run(
                cmd, capture_output=True, text=True, check=False
            )

        if proc.returncode != 0:
            raise GTestExecutionError(
                f"gtest binary exited with code {proc.returncode}"
            )
        if not xml_path.exists():  # pragma: no cover - defensive
            raise GTestExecutionError("gtest did not produce XML output")
        xml = xml_path.read_text()

    result = _parse_gtest_xml(xml)
    if collect_coverage:
        if not sources:
            raise ValueError("sources must be provided for coverage")
        result["coverage"] = _collect_coverage(sources, binary.parent)
    if cache is not None and key is not None:
        cache.store(key, result)
    return result
