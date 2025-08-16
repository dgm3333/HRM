#!/usr/bin/env python3
"""Utility to copy report artifacts into a GitHub Pages directory.

This script helps Phase 8 (CI/CD and Automation) by preparing the
latest evaluation reports for publication via GitHub Pages. It copies
all files from a source directory into a destination directory and
generates a simple ``index.html`` listing the contained artifacts.
"""
from __future__ import annotations

import argparse
import html
import shutil
from pathlib import Path


def build_index(dest: Path) -> None:
    """Generate a basic ``index.html`` with links to files in ``dest``."""
    lines = ["<html><body><h1>HRM Reports</h1><ul>"]
    for path in sorted(p for p in dest.rglob("*") if p.is_file()):
        rel = path.relative_to(dest).as_posix()
        lines.append(f'<li><a href="{html.escape(rel)}">{html.escape(rel)}</a></li>')
    lines.append("</ul></body></html>")
    (dest / "index.html").write_text("\n".join(lines))


def publish(source: Path, dest: Path) -> None:
    """Copy ``source`` directory tree into ``dest`` and create an index."""
    if not source.exists():
        raise FileNotFoundError(f"Source directory {source} does not exist")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    build_index(dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to report artifacts")
    parser.add_argument("dest", type=Path, help="Destination directory for Pages")
    args = parser.parse_args()
    publish(args.source, args.dest)
    print(f"Published reports from {args.source} to {args.dest}")


if __name__ == "__main__":
    main()
