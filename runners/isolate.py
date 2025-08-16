"""Lightweight wrapper for the ``isolate`` sandbox tool."""

from __future__ import annotations

import shutil
import subprocess
from typing import Iterable, List, Optional


class SandboxError(RuntimeError):
    """Raised when the sandbox cannot execute a command."""


class IsolateRunner:
    """Adapter for the ``isolate`` sandbox tool.

    The runner exposes a small subset of the ``isolate`` command line in a
    Pythonic interface.  It performs the standard ``--init`` → ``--run`` →
    ``--cleanup`` sequence for each invocation and allows callers to mount
    additional read-only directories or specify an explicit working
    directory inside the sandbox.  The implementation intentionally
    constructs command lines without executing them, permitting unit tests
    to exercise the wrapper even when the ``isolate`` binary is not
    installed.
    """

    def __init__(self, isolate_path: str = "isolate", box_id: int = 0) -> None:
        self.isolate_path = isolate_path
        self.box_id = box_id

    def build_command(
        self,
        command: List[str],
        *,
        time_limit: int = 5,
        wall_time: int = 5,
        memory: int = 256 * 1024,
        processes: int = 1,
        network: bool = False,
        workdir: Optional[str] = None,
        readonly_dirs: Optional[Iterable[str]] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> List[str]:
        """Build an ``isolate --run`` invocation.

        Parameters
        ----------
        command:
            The command to execute inside the sandbox.
        time_limit:
            CPU time limit in seconds.
        wall_time:
            Wall clock limit in seconds.
        memory:
            Memory limit in kilobytes.
        processes:
            Maximum number of allowed processes.
        network:
            Allow network access if ``True``.
        workdir:
            Path inside the sandbox to use as the working directory.  When
            provided the same path on the host is mounted read-write.
        readonly_dirs:
            Optional collection of host directories to bind read-only
            inside the sandbox at the same absolute paths.
        stdout, stderr:
            Optional filenames (inside the sandbox) to capture the
            respective streams.
        """
        isolate_cmd = [
            self.isolate_path,
            "--cg",
            f"--box-id={self.box_id}",
            f"--time={time_limit}",
            f"--wall={wall_time}",
            f"--mem={memory}",
            f"--processes={processes}",
        ]
        if not network:
            isolate_cmd.append("--net=none")
        if workdir is not None:
            isolate_cmd.append(f"--dir={workdir}=rw")
            isolate_cmd.append(f"--chdir={workdir}")
        if readonly_dirs is not None:
            for path in readonly_dirs:
                isolate_cmd.append(f"--dir={path}=ro")
        if stdout is not None:
            isolate_cmd.append(f"--stdout={stdout}")
        if stderr is not None:
            isolate_cmd.append(f"--stderr={stderr}")
        isolate_cmd.extend(["--run", "--"])
        isolate_cmd.extend(command)
        return isolate_cmd

    def run(
        self,
        command: List[str],
        *,
        time_limit: int = 5,
        wall_time: int = 5,
        memory: int = 256 * 1024,
        processes: int = 1,
        network: bool = False,
        workdir: Optional[str] = None,
        readonly_dirs: Optional[Iterable[str]] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        stdin: Optional[bytes] = None,
    ) -> subprocess.CompletedProcess:
        """Execute ``command`` within ``isolate``.

        The method performs the standard ``init`` → ``run`` → ``cleanup``
        lifecycle for a single command invocation.  In case initialization
        fails a :class:`SandboxError` is raised.  Execution errors of the
        sandboxed command itself are reflected in the returned
        :class:`subprocess.CompletedProcess` object and are not raised as
        exceptions.
        """
        if shutil.which(self.isolate_path) is None:
            raise SandboxError(
                f"isolate executable not found: {self.isolate_path}"
            )

        init_cmd = [
            self.isolate_path,
            f"--box-id={self.box_id}",
            "--init",
        ]
        init_proc = subprocess.run(init_cmd, capture_output=True, text=True)
        if init_proc.returncode != 0:
            raise SandboxError("isolate initialization failed")
        try:
            cmd = self.build_command(
                command,
                time_limit=time_limit,
                wall_time=wall_time,
                memory=memory,
                processes=processes,
                network=network,
                workdir=workdir,
                readonly_dirs=readonly_dirs,
                stdout=stdout,
                stderr=stderr,
            )
            proc = subprocess.run(
                cmd,
                input=stdin,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            subprocess.run(
                [
                    self.isolate_path,
                    f"--box-id={self.box_id}",
                    "--cleanup",
                ],
                capture_output=True,
                text=True,
            )
        return proc
