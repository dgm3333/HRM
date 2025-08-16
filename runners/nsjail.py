import shutil
import subprocess
import tempfile
from typing import Iterable, List, Mapping, Optional


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
        workdir: Optional[str] = None,
        readonly_dirs: Optional[Iterable[str]] = None,
        env: Optional[Mapping[str, str]] = None,
        fsize: Optional[int] = None,
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
        workdir:
            Path inside the sandbox to use as the working directory. The
            same host path is bind-mounted read-write.
        readonly_dirs:
            Optional collection of host directories to bind read-only inside
            the sandbox.
        env:
            Optional mapping of environment variables to set inside the
            sandbox.
        fsize:
            Optional limit for files created by the process in bytes.
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
        if workdir is not None:
            nsjail_cmd.extend(["--cwd", workdir, "--bindmount", f"{workdir}:{workdir}"])
        if readonly_dirs is not None:
            for path in readonly_dirs:
                nsjail_cmd.extend(["--bindmount_ro", f"{path}:{path}"])
        if env is not None:
            for key, value in env.items():
                nsjail_cmd.extend(["--env", f"{key}={value}"])
        if fsize is not None:
            nsjail_cmd.append(f"--rlimit_fsize={fsize}")
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
        workdir: Optional[str] = None,
        readonly_dirs: Optional[Iterable[str]] = None,
        stdin: Optional[bytes] = None,
        env: Optional[Mapping[str, str]] = None,
        stdout_limit: Optional[int] = None,
        stderr_limit: Optional[int] = None,
    ) -> subprocess.CompletedProcess:
        """Execute a command within ``nsjail``.

        Returns the :class:`subprocess.CompletedProcess` instance produced
        by :func:`subprocess.run`.
        """
        if shutil.which(self.nsjail_path) is None:
            raise SandboxError(
                f"nsjail executable not found: {self.nsjail_path}"
            )

        tmpdir_ctx: Optional[tempfile.TemporaryDirectory[str]] = None
        if workdir is None:
            tmpdir_ctx = tempfile.TemporaryDirectory()
            workdir = tmpdir_ctx.name

        max_limit = max(stdout_limit or 0, stderr_limit or 0)
        fsize = max_limit if max_limit else None

        cmd = self.build_command(
            command,
            time_limit=time_limit,
            wall_time=wall_time,
            memory=memory,
            processes=processes,
            network=network,
            workdir=workdir,
            readonly_dirs=readonly_dirs,
            env=env,
            fsize=fsize,
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

        if tmpdir_ctx is not None:
            tmpdir_ctx.cleanup()

        return subprocess.CompletedProcess(cmd, proc.returncode, stdout_data, stderr_data)
