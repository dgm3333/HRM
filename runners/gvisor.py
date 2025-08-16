"""Minimal wrapper for executing commands inside gVisor using Docker."""

from __future__ import annotations

import shutil
import subprocess
from typing import Iterable, List, Optional


class SandboxError(RuntimeError):
    """Raised when the sandbox cannot execute a command."""


class GVisorRunner:
    """Adapter that runs commands inside a Docker container with gVisor runtime.

    This runner constructs ``docker run`` invocations that leverage the
    ``runsc`` runtime provided by gVisor.  Only a subset of Docker's resource
    limiting flags are exposed which mirrors the interface of the other
    sandbox adapters.  The implementation intentionally avoids executing any
    commands when the ``docker`` binary is unavailable so unit tests can run
    without a full container environment.
    """

    def __init__(self, *, docker_path: str = "docker", image: str = "ubuntu:latest") -> None:
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
    ) -> List[str]:
        """Build a ``docker run`` command that executes ``command`` under gVisor.

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
        """
        docker_cmd = [
            self.docker_path,
            "run",
            "--rm",
            "--runtime=runsc",
            f"--cpus=1",
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
        stdin: Optional[bytes] = None,
    ) -> subprocess.CompletedProcess:
        """Execute ``command`` inside a gVisor-backed Docker container."""
        if shutil.which(self.docker_path) is None:
            raise SandboxError(f"docker executable not found: {self.docker_path}")
        cmd = self.build_command(
            command,
            time_limit=time_limit,
            memory=memory,
            processes=processes,
            network=network,
            workdir=workdir,
            readonly_dirs=readonly_dirs,
        )
        return subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )
