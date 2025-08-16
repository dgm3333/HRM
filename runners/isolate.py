import shutil
import subprocess
from typing import List, Optional


class SandboxError(RuntimeError):
    """Raised when the sandbox cannot execute a command."""


class IsolateRunner:
    """Adapter for the ``isolate`` sandbox tool.

    This minimal wrapper constructs and runs ``isolate`` commands with
    resource limits. It does not depend on the actual presence of the
    ``isolate`` binary until :meth:`run` is invoked, enabling unit tests
    to validate command construction without the binary installed.
    """

    def __init__(self, isolate_path: str = "isolate") -> None:
        self.isolate_path = isolate_path

    def build_command(
        self,
        command: List[str],
        *,
        time_limit: int = 5,
        wall_time: int = 5,
        memory: int = 256 * 1024,
        processes: int = 1,
        network: bool = False,
    ) -> List[str]:
        """Build an ``isolate`` invocation.

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
        """
        isolate_cmd = [
            self.isolate_path,
            "--cg",
            f"--time={time_limit}",
            f"--wall={wall_time}",
            f"--mem={memory}",
            f"--processes={processes}",
        ]
        if not network:
            isolate_cmd.append("--net=none")
        isolate_cmd.append("--")
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
        stdin: Optional[bytes] = None,
    ) -> subprocess.CompletedProcess:
        """Execute a command within ``isolate``.

        Returns the :class:`subprocess.CompletedProcess` object produced
        by :func:`subprocess.run`.
        """
        if shutil.which(self.isolate_path) is None:
            raise SandboxError(
                f"isolate executable not found: {self.isolate_path}"
            )
        cmd = self.build_command(
            command,
            time_limit=time_limit,
            wall_time=wall_time,
            memory=memory,
            processes=processes,
            network=network,
        )
        return subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )
