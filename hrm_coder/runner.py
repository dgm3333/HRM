"""Utilities to construct sandbox runners from configuration."""
from __future__ import annotations

from typing import List, Optional
import subprocess

from runners import GVisorRunner, IsolateRunner, NSJailRunner, sandbox_detector
from .config import RunnerConfig


def create_sandbox_runner(config: RunnerConfig) -> object:
    """Instantiate the sandbox runner specified by ``config``.

    When ``config.sandbox`` is set to ``"auto"`` the function probes the
    environment and picks the first available backend in the order
    ``isolate`` → ``nsjail`` → ``runsc``.
    """

    sandbox = config.sandbox
    if sandbox in ("auto", ""):  # auto-select
        selected, _ = sandbox_detector.select_sandbox()
        if selected is None:
            raise RuntimeError("no supported sandbox available")
        sandbox = selected
    if sandbox == "isolate":
        return IsolateRunner()
    if sandbox == "nsjail":
        return NSJailRunner()
    if sandbox in {"runsc", "gvisor"}:
        return GVisorRunner()
    raise ValueError(f"unsupported sandbox: {sandbox}")


def run_in_sandbox(
    command: List[str],
    config: RunnerConfig,
    *,
    network: bool = False,
    stdin: Optional[bytes] = None,
) -> subprocess.CompletedProcess:
    """Execute ``command`` inside the sandbox described by ``config``."""

    runner = create_sandbox_runner(config)
    memory_kb = config.memory_limit * 1024
    common_kwargs = dict(
        time_limit=config.timeout,
        wall_time=config.timeout,
        memory=memory_kb,
        processes=config.cpus,
        network=network,
        stdin=stdin,
    )
    if isinstance(runner, IsolateRunner):
        return runner.run(command, **common_kwargs)
    if isinstance(runner, NSJailRunner):
        return runner.run(command, **common_kwargs)
    if isinstance(runner, GVisorRunner):
        # gVisor's runner does not support wall_time; ignore it
        common_kwargs.pop("wall_time", None)
        return runner.run(command, **common_kwargs)
    raise TypeError(f"Unsupported runner type: {type(runner).__name__}")


__all__ = ["create_sandbox_runner", "run_in_sandbox"]
