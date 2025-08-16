#!/usr/bin/env python3
"""Inventory HRM repository APIs.

This utility walks selected directories and reports the classes and functions
found in each Python module. It avoids importing modules so that directories
without ``__init__`` files are handled gracefully. The report is printed as
JSON and is intended to help identify potential injection points for C++
token or AST encoders during Phase 0 discovery.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, List

# Top-level directories to inspect. Additional paths can be added as the
# project evolves.
DIRECTORIES = ["models", "dataset", "utils"]


def collect_api(py_file: Path) -> Dict[str, List[str]]:
    """Return the classes and functions defined in ``py_file``."""
    tree = ast.parse(py_file.read_text())
    classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    return {"classes": classes, "functions": functions}


def walk_directory(directory: Path, report: Dict[str, Dict[str, List[str]]]) -> None:
    for py_file in directory.glob("**/*.py"):
        module_name = (
            py_file.relative_to(Path("."))
            .with_suffix("")
            .as_posix()
            .replace("/", ".")
        )
        report[module_name] = collect_api(py_file)


def inventory(paths: List[str] = DIRECTORIES) -> Dict[str, Dict[str, List[str]]]:
    report: Dict[str, Dict[str, List[str]]] = {}
    for path in paths:
        directory = Path(path)
        if directory.exists():
            walk_directory(directory, report)
    return report


def main() -> None:
    print(json.dumps(inventory(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
