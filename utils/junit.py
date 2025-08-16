"""JUnit XML parsing helpers.

This module provides lightweight utilities to extract test
statistics from JUnit formatted XML strings.  The intent is to
support Phase 5 of the project where per-test rewards are derived
from unit-test results.
"""

from __future__ import annotations

from typing import Tuple
import xml.etree.ElementTree as ET


def parse_junit_summary(xml: str) -> Tuple[int, int]:
    """Return the number of passed tests and total tests.

    Parameters
    ----------
    xml:
        String containing a JUnit ``<testsuite>`` or ``<testsuites>``
        document.

    Returns
    -------
    Tuple[int, int]
        A pair ``(passed, total)`` with the count of tests that passed
        and the total number of tests executed.

    Raises
    ------
    ValueError
        If ``xml`` cannot be parsed as JUnit XML.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ValueError("invalid junit xml") from exc

    def _extract(node: ET.Element) -> Tuple[int, int]:
        tests = int(node.attrib.get("tests", 0))
        failures = int(node.attrib.get("failures", 0))
        errors = int(node.attrib.get("errors", 0))
        return tests - (failures + errors), tests

    if root.tag == "testsuites":
        passed = total = 0
        for suite in root.findall("testsuite"):
            p, t = _extract(suite)
            passed += p
            total += t
        return passed, total

    passed, total = _extract(root)
    return passed, total
