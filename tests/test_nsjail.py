
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from runners.nsjail import NSJailRunner


def test_build_command_network_off_by_default():
    runner = NSJailRunner(nsjail_path="nsjail")
    cmd = runner.build_command(
        ["/bin/echo", "hello"],
        time_limit=1,
        wall_time=2,
        memory=1024,
        processes=1,
    )
    assert cmd[0] == "nsjail"
    assert "--disable_clone_newnet" not in cmd
    assert "--" in cmd
    assert cmd[-2:] == ["/bin/echo", "hello"]


def test_build_command_allows_network_when_requested():
    runner = NSJailRunner(nsjail_path="nsjail")
    cmd = runner.build_command(["/bin/echo", "hi"], network=True)
    assert "--disable_clone_newnet" in cmd


def test_build_command_with_env():
    runner = NSJailRunner(nsjail_path="nsjail")
    cmd = runner.build_command(["/bin/true"], env={"LD_LIBRARY_PATH": "/libs"})
    assert "--env" in cmd
    env_idx = cmd.index("--env")
    assert cmd[env_idx + 1] == "LD_LIBRARY_PATH=/libs"
