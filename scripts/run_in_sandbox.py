"""Execute a command inside the configured sandbox.

This small utility wraps :func:`hrm_coder.runner.run_in_sandbox` so that
developers can quickly invoke commands inside the first available
sandbox backend (``isolate``, ``nsjail`` or gVisor's ``runsc`` runtime).

Example::

    python scripts/run_in_sandbox.py -- echo "hello"

The command after ``--`` is executed in the sandbox.  By default the
script auto-selects the sandbox backend, but a specific one can be chosen
via ``--sandbox``.
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from hrm_coder.config import RunnerConfig
from hrm_coder.runner import run_in_sandbox


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a command in a sandbox")
    parser.add_argument(
        "--sandbox",
        default="auto",
        help="Sandbox backend (isolate, nsjail, runsc, auto)",
    )
    parser.add_argument(
        "--timeout", type=int, default=5, help="CPU time limit in seconds"
    )
    parser.add_argument(
        "--memory",
        type=int,
        default=256,
        help="Memory limit in megabytes",
    )
    parser.add_argument(
        "--cpus", type=int, default=1, help="Number of allowed processes"
    )
    parser.add_argument(
        "--network",
        action="store_true",
        help="Allow network access inside the sandbox",
    )
    parser.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Command to run (use -- to separate)",
    )
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.error("no command provided")
    if args.cmd[0] == "--":
        args.cmd = args.cmd[1:]
    return args


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = RunnerConfig(
        sandbox=args.sandbox,
        timeout=args.timeout,
        memory_limit=args.memory,
        cpus=args.cpus,
        network=args.network,
    )
    proc = run_in_sandbox(args.cmd, config)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
