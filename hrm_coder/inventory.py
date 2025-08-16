"""Utilities for auditing the existing HRM package.

This module helps Phase 0 of the hrm-coder project by providing helper
functions that introspect the ``hrm`` package and surface potential
injection points for C++ token or AST based decoders.  The goal is to
make it trivial to see which modules and classes already exist so that
future phases can extend them instead of rewriting from scratch.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModuleInventory:
    """Light‑weight description of a module's public surface."""

    name: str
    classes: List[str]
    functions: List[str]


def inventory_package(package: str) -> Dict[str, ModuleInventory]:
    """Return a mapping of module name to :class:`ModuleInventory`.

    Parameters
    ----------
    package:
        Package path to walk.  The package must be importable and expose
        ``__path__``.
    """
    pkg = importlib.import_module(package)
    if not hasattr(pkg, "__path__"):
        raise ValueError(f"{package!r} is not a package")

    inventory: Dict[str, ModuleInventory] = {}
    for mod_info in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        module = importlib.import_module(mod_info.name)
        classes = [
            name
            for name, obj in inspect.getmembers(module, inspect.isclass)
            if obj.__module__ == mod_info.name
        ]
        functions = [
            name
            for name, obj in inspect.getmembers(module, inspect.isfunction)
            if obj.__module__ == mod_info.name
        ]
        inventory[mod_info.name] = ModuleInventory(
            name=mod_info.name, classes=classes, functions=functions
        )
    return inventory


def find_injection_points(inv: Dict[str, ModuleInventory]) -> List[str]:
    """Return fully-qualified class names related to code encoding.

    The heuristic is intentionally simple: any class whose name contains
    ``Encoder`` or ``Tokenizer`` is considered a candidate injection point
    for plugging in C++ specific implementations.
    """
    points: List[str] = []
    for module, info in inv.items():
        for cls in info.classes:
            if "Encoder" in cls or "Tokenizer" in cls:
                points.append(f"{module}.{cls}")
    return points
