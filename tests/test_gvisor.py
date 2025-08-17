import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from runners.gvisor import GVisorRunner  # noqa: E402


def test_build_command_network_off_by_default():
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")
    cmd = runner.build_command(["/bin/echo", "hello"], processes=2)
    assert cmd[:4] == ["docker", "run", "--rm", "--runtime=runsc"]
    assert "--network=none" in cmd
    assert "--pids-limit=2" in cmd
    assert cmd[-2:] == ["/bin/echo", "hello"]


def test_build_command_with_mounts_and_workdir():
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")
    cmd = runner.build_command(
        ["/bin/true"],
        workdir="/workspace",
        readonly_dirs=["/data"],
    )
    assert "-w" in cmd and cmd[cmd.index("-w") + 1] == "/workspace"
    mount_flag = "/data:/data:ro"
    assert any(part.endswith(mount_flag) for part in cmd)
    assert "--network=none" in cmd


def test_build_command_with_env():
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")
    cmd = runner.build_command(["/bin/true"], env={"FOO": "BAR", "BAZ": "QUX"})
    assert "-e" in cmd
    assert "FOO=BAR" in cmd
    assert "BAZ=QUX" in cmd


def test_build_command_with_fsize():
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")
    cmd = runner.build_command(["/bin/true"], fsize=1234)
    assert "--ulimit" in cmd
    assert "fsize=1234" in cmd


def test_run_truncates_output(monkeypatch):
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")

    monkeypatch.setattr(shutil, "which", lambda p: "/usr/bin/docker")

    import subprocess

    Completed = subprocess.CompletedProcess

    def fake_run(cmd, *args, **kwargs):
        return Completed(cmd, 0, "A" * 100, "B" * 100)

    monkeypatch.setattr(subprocess, "run", fake_run)

    proc = runner.run(["/bin/echo", "hi"], stdout_limit=10, stderr_limit=5)
    assert proc.stdout == "A" * 10
    assert proc.stderr == "B" * 5


def test_run_includes_fsize(monkeypatch):
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")
    monkeypatch.setattr(shutil, "which", lambda p: "/usr/bin/docker")

    import subprocess

    captured = {}

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner.run(["/bin/echo", "hi"], stdout_limit=10)
    cmd = captured["cmd"]
    assert "--ulimit" in cmd
    assert "fsize=10" in cmd
