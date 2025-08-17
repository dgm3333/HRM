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
    assert "--time_limit=2" in cmd
    assert "--rlimit_cpu=1" in cmd
    assert f"--cgroup_mem_max={1024 * 1024}" in cmd
    assert f"--rlimit_as={1024 * 1024}" in cmd
    assert "--cgroup_pids_max=1" in cmd
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


def test_build_command_with_workdir_and_readonly_dirs(tmp_path):
    runner = NSJailRunner(nsjail_path="nsjail")
    cmd = runner.build_command(
        ["/bin/echo", "hi"],
        workdir="/work",
        readonly_dirs=["/data"],
    )
    assert "--cwd" in cmd
    assert "--bindmount" in cmd
    assert "--bindmount_ro" in cmd


def test_run_enforces_output_limits(tmp_path):
    fake = tmp_path / "nsjail"
    fake.write_text(
        """#!/usr/bin/env python3
import sys, subprocess
args = sys.argv[1:]
idx = args.index('--')
cmd = args[idx + 1:]
res = subprocess.run(cmd)
sys.exit(res.returncode)
"""
    )
    fake.chmod(0o755)
    runner = NSJailRunner(nsjail_path=str(fake))
    proc = runner.run(
        ["/bin/sh", "-c", "printf 'abcdef' && printf 'ghij' >&2"],
        stdout_limit=3,
        stderr_limit=2,
    )
    assert proc.stdout == "abc"
    assert proc.stderr == "gh"
