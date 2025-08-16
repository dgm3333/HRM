import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from runners.gvisor import GVisorRunner


def test_build_command_network_off_by_default():
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")
    cmd = runner.build_command(["/bin/echo", "hello"], processes=2)
    assert cmd[:4] == ["docker", "run", "--rm", "--runtime=runsc"]
    assert "--network=none" in cmd
    assert f"--pids-limit=2" in cmd
    assert cmd[-2:] == ["/bin/echo", "hello"]


def test_build_command_with_mounts_and_workdir():
    runner = GVisorRunner(docker_path="docker", image="ubuntu:latest")
    cmd = runner.build_command(
        ["/bin/true"],
        workdir="/workspace",
        readonly_dirs=["/data"],
    )
    assert "-w" in cmd and cmd[cmd.index("-w") + 1] == "/workspace"
    mount_flag = f"/data:/data:ro"
    assert any(part.endswith(mount_flag) for part in cmd)
    assert "--network=none" in cmd
