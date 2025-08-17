"""Minimal wrapper for executing commands inside gVisor using Docker."""

from __future__ import annotations

import shutil
import subprocess
from typing import Iterable, List, Mapping, Optional


class SandboxError(RuntimeError):
    """Raised when the sandbox cannot execute a command."""


class GVisorRunner:
    """Adapter that runs commands inside a Docker container using gVisor.

    This runner constructs ``docker run`` invocations that leverage the
    ``runsc`` runtime provided by gVisor.  Only a subset of Docker's resource
    limiting flags are exposed which mirrors the interface of the other
    sandbox adapters.  The implementation intentionally avoids executing any
    commands when the ``docker`` binary is unavailable so unit tests can run
    without a full container environment.
    """

    def __init__(
        self, *, docker_path: str = "docker", image: str = "ubuntu:latest"
    ) -> None:
        self.docker_path = docker_path
        self.image = image

    def build_command(
        self,
        command: List[str],
        *,
        time_limit: int = 5,
        memory: int = 256 * 1024,
        processes: int = 1,
        network: bool = False,
        workdir: Optional[str] = None,
        readonly_dirs: Optional[Iterable[str]] = None,
        env: Optional[Mapping[str, str]] = None,
        fsize: Optional[int] = None,
    ) -> List[str]:
        """Build a ``docker run`` command that executes ``command`` under
        gVisor.

        Parameters
        ----------
        command:
            The command to execute inside the container.
        time_limit:
            CPU time limit in seconds (translated into ``--cpus``).
        memory:
            Memory limit in kilobytes (translated into ``--memory``).
        processes:
            Maximum number of processes allowed inside the container.
        network:
            Allow network access if ``True``.
        workdir:
            Working directory inside the container.
        readonly_dirs:
            Iterable of host paths to mount read-only inside the container at
            the same paths.
        env:
            Optional mapping of environment variables to define inside the
            container.
        """
        docker_cmd = [
            self.docker_path,
            "run",
            "--rm",
            "--runtime=runsc",
            "--cpus=1",
            f"--pids-limit={processes}",
            f"--memory={memory}k",
        ]
        if not network:
            docker_cmd.append("--network=none")
        if workdir is not None:
            docker_cmd.extend(["-w", workdir])
        if readonly_dirs is not None:
            for path in readonly_dirs:
                docker_cmd.extend(["-v", f"{path}:{path}:ro"])
        if env is not None:
            for key, value in env.items():
                docker_cmd.extend(["-e", f"{key}={value}"])
        if fsize is not None:
            docker_cmd.extend(["--ulimit", f"fsize={fsize}"])
        docker_cmd.append(self.image)
        docker_cmd.extend(command)
        return docker_cmd

    def run(
        self,
        command: List[str],
        *,
        time_limit: int = 5,
        memory: int = 256 * 1024,
        processes: int = 1,
        network: bool = False,
        workdir: Optional[str] = None,
        readonly_dirs: Optional[Iterable[str]] = None,
        env: Optional[Mapping[str, str]] = None,
        stdin: Optional[bytes] = None,
        stdout_limit: Optional[int] = None,
        stderr_limit: Optional[int] = None,
    ) -> subprocess.CompletedProcess:
        """Execute ``command`` inside a gVisor-backed Docker container."""
        if shutil.which(self.docker_path) is None:
            raise SandboxError(
                f"docker executable not found: {self.docker_path}"
            )
        max_limit = max(stdout_limit or 0, stderr_limit or 0)
        cmd = self.build_command(
            command,
            time_limit=time_limit,
            memory=memory,
            processes=processes,
            network=network,
            workdir=workdir,
            readonly_dirs=readonly_dirs,
            env=env,
            fsize=max_limit if max_limit else None,
        )
        proc = subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout_data = proc.stdout
        stderr_data = proc.stderr
        if stdout_limit is not None:
            stdout_data = stdout_data[:stdout_limit]
        if stderr_limit is not None:
            stderr_data = stderr_data[:stderr_limit]
        return subprocess.CompletedProcess(
            cmd, proc.returncode, stdout_data, stderr_data
        )
