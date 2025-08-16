"""HRM Coder backend stub for Phase 2."""

from .api import app  # noqa: F401
from .inventory import inventory_package, find_injection_points  # noqa: F401

__all__ = ["app", "inventory_package", "find_injection_points"]
