import shutil
import subprocess
from typing import List, Optional


class SandboxError(RuntimeError):
    """Raised when the sandbox cannot execute a command."""


class NSJailRunner:
    """Adapter for the ``nsjail`` sandbox tool.

    Similar to :class:`IsolateRunner`, this wrapper prepares ``nsjail``
    commands with resource limits. The actual ``nsjail`` binary is only
    required when :meth:`run` is executed so unit tests can exercise the
    command builder on systems without ``nsjail`` installed.
    """

    def __init__(self, nsjail_path: str = "nsjail") -> None:
        self.nsjail_path = nsjail_path

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
        """Construct an ``nsjail`` invocation.

        Parameters
        ----------
        command:
            The command to execute inside the sandbox.
        time_limit:
            CPU time limit in seconds.
        wall_time:
            Wall clock limit in seconds (``nsjail`` uses the same flag for
            both CPU and wall limits).
        memory:
            Memory limit in kilobytes.
        processes:
            Maximum number of processes.
        network:
            Allow network access if ``True``.
        """
        nsjail_cmd = [
            self.nsjail_path,
            "-Mo",
            f"--time_limit={time_limit}",
            f"--rlimit_as={memory * 1024}",
            f"--cgroup_pids_max={processes}",
        ]
        if network:
            nsjail_cmd.append("--disable_clone_newnet")
        nsjail_cmd.append("--")
        nsjail_cmd.extend(command)
        return nsjail_cmd

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
        """Execute a command within ``nsjail``.

        Returns the :class:`subprocess.CompletedProcess` instance produced
        by :func:`subprocess.run`.
        """
        if shutil.which(self.nsjail_path) is None:
            raise SandboxError(
                f"nsjail executable not found: {self.nsjail_path}"
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
