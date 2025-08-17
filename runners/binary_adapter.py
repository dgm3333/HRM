from __future__ import annotations

"""Adapter to execute compiled binaries inside sandbox runners.

This module provides :class:`BinarySandboxAdapter` which wraps a sandbox
runner such as :class:`~runners.isolate.IsolateRunner` or
:class:`~runners.nsjail.NSJailRunner`. It normalizes environment variables
for AddressSanitizer and UndefinedBehaviorSanitizer to ensure deterministic
behaviour across backends.
"""

import tempfile
from pathlib import Path
from typing import Mapping, Optional, Tuple

from .isolate import SandboxError

SANITIZER_ENV: Mapping[str, str] = {
    "ASAN_OPTIONS": "detect_leaks=0:halt_on_error=1:color=never",
    "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1:color=never",
}


class BinarySandboxAdapter:
    """Run compiled binaries within a sandbox runner with sanitizer
    injection."""

    def __init__(
        self,
        sandbox,
        *,
        sanitizer_env: Mapping[str, str] | None = None,
    ) -> None:
        self.sandbox = sandbox
        self.sanitizer_env = dict(sanitizer_env or SANITIZER_ENV)

    def run(
        self,
        binary: Path,
        *,
        input_data: str = "",
        timeout: float = 2.0,
        memory_limit: Optional[int] = None,
        env: Optional[Mapping[str, str]] = None,
        sanitize_env: bool = True,
        cwd: Optional[Path] = None,
        stdout_limit: Optional[int] = None,
        stderr_limit: Optional[int] = None,
    ) -> Tuple[int, str, str]:
        """Execute ``binary`` inside the sandbox and return
        ``(code, stdout, stderr)``."""

        if cwd is None:
            cwd = binary.parent

        env_combined = dict(env or {})
        if sanitize_env:
            env_combined = {**self.sanitizer_env, **env_combined}

        memory_kb = (memory_limit or 256 * 1024 * 1024) // 1024

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                proc = self.sandbox.run(
                    [str(binary)],
                    time_limit=int(timeout),
                    wall_time=int(timeout),
                    memory=memory_kb,
                    processes=1,
                    network=False,
                    stdin=input_data,
                    workdir=tmpdir,
                    readonly_dirs=[str(cwd)],
                    env=env_combined,
                    stdout_limit=stdout_limit,
                    stderr_limit=stderr_limit,
                )
            except TypeError:
                try:
                    proc = self.sandbox.run(
                        [str(binary)],
                        time_limit=int(timeout),
                        wall_time=int(timeout),
                        memory=memory_kb,
                        processes=1,
                        network=False,
                        stdin=input_data,
                        env=env_combined,
                        stdout_limit=stdout_limit,
                        stderr_limit=stderr_limit,
                    )
                except TypeError:
                    proc = self.sandbox.run(
                        [str(binary)],
                        time_limit=int(timeout),
                        wall_time=int(timeout),
                        memory=memory_kb,
                        stdin=input_data,
                        env=env_combined,
                        stdout_limit=stdout_limit,
                        stderr_limit=stderr_limit,
                    )
            except SandboxError as exc:
                return -1, "", str(exc)

        return proc.returncode, proc.stdout, proc.stderr
