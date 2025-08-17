import subprocess

from runners.nsjail import NSJailRunner


def test_build_command_defaults():
    runner = NSJailRunner(nsjail_path="nsjail")
    cmd = runner.build_command([
        "/bin/echo",
        "hi",
    ], time_limit=1, wall_time=2, memory=1024, processes=1)
    assert cmd[0] == "nsjail"
    assert "-Mo" in cmd
    assert "--disable_clone_newnet" not in cmd
    assert "--time_limit=2" in cmd
    assert "--rlimit_cpu=1" in cmd
    assert f"--cgroup_mem_max={1024 * 1024}" in cmd
    assert f"--rlimit_as={1024 * 1024}" in cmd
    assert "--cgroup_pids_max=1" in cmd
    assert cmd[-2:] == ["/bin/echo", "hi"]


def test_build_command_with_options():
    runner = NSJailRunner(nsjail_path="nsjail")
    cmd = runner.build_command(
        ["/bin/true"],
        time_limit=1,
        wall_time=3,
        memory=2048,
        processes=2,
        network=True,
        workdir="/tmp/work",
        readonly_dirs=["/data"],
        env={"FOO": "BAR"},
        fsize=64,
    )
    assert "--disable_clone_newnet" in cmd
    assert "--time_limit=3" in cmd
    assert "--rlimit_cpu=1" in cmd
    assert f"--cgroup_mem_max={2048 * 1024}" in cmd
    assert f"--rlimit_as={2048 * 1024}" in cmd
    assert "--cwd" in cmd and "--bindmount" in cmd
    assert "/tmp/work:/tmp/work" in cmd
    assert "--bindmount_ro" in cmd
    assert "/data:/data" in cmd
    assert "--env" in cmd and "FOO=BAR" in cmd
    assert "--rlimit_fsize=64" in cmd


def test_run_truncates_output(monkeypatch):
    runner = NSJailRunner(nsjail_path="nsjail")
    monkeypatch.setattr("shutil.which", lambda p: "/usr/bin/nsjail")
    Completed = subprocess.CompletedProcess

    def fake_run(cmd, *args, **kwargs):
        return Completed(cmd, 0, "A" * 100, "B" * 100)

    monkeypatch.setattr(subprocess, "run", fake_run)
    proc = runner.run(["/bin/echo", "hi"], stdout_limit=10, stderr_limit=10)
    assert proc.stdout == "A" * 10
    assert proc.stderr == "B" * 10
