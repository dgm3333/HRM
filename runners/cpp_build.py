"""Minimal CMake build helpers for Phase 1 scaffolding.

These utilities wrap ``cmake`` and ``ctest`` to compile and execute the
placeholder C++ harnesses included with the project. They intentionally
expose only a tiny subset of options required for the early deterministic
environment work. Later phases will expand the interface with richer
configuration and diagnostics.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import Dict


def configure(
    source_dir: Path,
    build_dir: Path,
    *,
    preset: str = "sanitized",
    compiler: str = "g++",
) -> CompletedProcess:
    """Run a basic CMake configure step into ``build_dir``.

    Currently only a ``sanitized`` preset is supported which enables
    AddressSanitizer and UndefinedBehaviorSanitizer for deterministic
    debugging. The ``preset`` argument is reserved for future expansion.  A
    ``compiler`` can be provided to choose between toolchains such as ``g++``
    or ``clang++``.
    """
    build_dir.mkdir(parents=True, exist_ok=True)
    if preset != "sanitized":
        raise ValueError(f"unsupported preset: {preset}")
    cmd = [
        "cmake",
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        "-G",
        "Ninja",
        f"-DCMAKE_CXX_COMPILER={compiler}",
        "-DCMAKE_BUILD_TYPE=Debug",
        "-DCMAKE_CXX_FLAGS=-O1 -g -fsanitize=address,undefined "
        "-fno-omit-frame-pointer",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def build(build_dir: Path) -> CompletedProcess:
    """Invoke ``cmake --build`` for the given ``build_dir``."""
    cmd = ["cmake", "--build", str(build_dir)]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def run_tests(build_dir: Path) -> CompletedProcess:
    """Execute ``ctest`` in ``build_dir`` and return the completed process."""
    cmd = ["ctest", "--test-dir", str(build_dir)]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def build_and_run_gtests(
    source_dir: Path,
    build_dir: Path,
    *,
    test_binary: str,
    compiler: str = "g++",
    preset: str = "sanitized",
) -> Dict[str, object]:
    """Configure, build, and execute a GoogleTest binary with CMake.

    Parameters
    ----------
    source_dir:
        Directory containing a ``CMakeLists.txt`` and test sources.
    build_dir:
        Directory where the build files and resulting binary will be placed.
    test_binary:
        Name of the produced test executable inside ``build_dir``.
    compiler:
        Which C++ compiler to use (e.g. ``g++`` or ``clang++``).
    preset:
        Currently only ``"sanitized"`` is supported which enables ASan/UBSan
        for deterministic debugging.

    Returns
    -------
    Dict[str, object]
        Dictionary combining configure/build logs with parsed GoogleTest
        results.  On configure or build failure ``tests`` will be ``0`` and
        ``xml`` will be empty.
    """

    cfg = configure(source_dir, build_dir, preset=preset, compiler=compiler)
    data: Dict[str, object] = {
        "configure_stdout": cfg.stdout,
        "configure_stderr": cfg.stderr,
        "configure_returncode": cfg.returncode,
    }
    if cfg.returncode != 0:
        data.update(
            {
                "tests": 0,
                "failures": 0,
                "errors": 0,
                "cases": [],
                "xml": "",
            }
        )
        return data

    comp = build(build_dir)
    data.update(
        {
            "build_stdout": comp.stdout,
            "build_stderr": comp.stderr,
            "build_returncode": comp.returncode,
        }
    )
    if comp.returncode != 0:
        data.update(
            {
                "tests": 0,
                "failures": 0,
                "errors": 0,
                "cases": [],
                "xml": "",
            }
        )
        return data

    from .gtest_runner import run_gtests  # local import to avoid cycle

    binary = build_dir / test_binary
    run_res = run_gtests(binary)
    data.update(run_res)
    return data


__all__ = ["configure", "build", "run_tests", "build_and_run_gtests"]
