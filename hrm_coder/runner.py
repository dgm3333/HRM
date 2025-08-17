"""Utilities to construct sandbox runners from configuration."""
from __future__ import annotations

from typing import List, Optional
import subprocess

from runners import (
    GVisorRunner,
    IsolateRunner,
    NSJailRunner,
    sandbox_detector,
)
from runners.sandbox_cache import SandboxCache
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
    network: Optional[bool] = None,
    stdin: Optional[bytes] = None,
    cache: Optional[SandboxCache] = None,
) -> subprocess.CompletedProcess:
    """Execute ``command`` inside the sandbox described by ``config``.

    When ``cache`` is provided the output of identical invocations is
    memoized. The cache key is derived from the command, runner limits, and
    ``stdin`` payload.
    """

    runner = create_sandbox_runner(config)
    memory_kb = config.memory_limit * 1024
    network = config.network if network is None else network

    key: Optional[str] = None
    if cache is not None:
        parts = [p.encode() for p in command]
        parts.append(str(config.timeout).encode())
        parts.append(str(config.memory_limit).encode())
        parts.append(str(config.cpus).encode())
        parts.append(b"net_on" if network else b"net_off")
        if stdin is not None:
            parts.append(stdin)
        key = cache.hash_parts(parts)
        cached = cache.load(key)
        if cached is not None:
            return subprocess.CompletedProcess(
                command,
                cached["returncode"],
                cached.get("stdout", ""),
                cached.get("stderr", ""),
            )

    common_kwargs = dict(
        time_limit=config.timeout,
        wall_time=config.timeout,
        memory=memory_kb,
        processes=config.cpus,
        network=network,
        stdin=stdin,
    )
    if isinstance(runner, IsolateRunner):
        proc = runner.run(command, **common_kwargs)
    elif isinstance(runner, NSJailRunner):
        proc = runner.run(command, **common_kwargs)
    elif isinstance(runner, GVisorRunner):
        # gVisor's runner does not support wall_time; ignore it
        common_kwargs.pop("wall_time", None)
        proc = runner.run(command, **common_kwargs)
    else:
        raise TypeError(f"Unsupported runner type: {type(runner).__name__}")

    if cache is not None and key is not None:
        cache.store(
            key,
            {
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
        )
    return proc


__all__ = ["create_sandbox_runner", "run_in_sandbox"]
