from pathlib import Path
import subprocess
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from runners.isolate import IsolateRunner


def test_build_command_has_no_network_by_default():
    runner = IsolateRunner(isolate_path="isolate", box_id=0)
    cmd = runner.build_command(
        ["/bin/echo", "hello"],
        time_limit=1,
        wall_time=2,
        memory=1024,
        processes=1,
    )
    assert cmd[0] == "isolate"
    assert f"--box-id={runner.box_id}" in cmd
    assert "--net=none" in cmd
    assert "--run" in cmd
    run_idx = cmd.index("--run")
    assert cmd[run_idx + 1] == "--"
    assert cmd[-2:] == ["/bin/echo", "hello"]


def test_build_command_with_filesystem_options():
    runner = IsolateRunner(isolate_path="isolate", box_id=1)
    cmd = runner.build_command(
        ["/bin/true"],
        workdir="/tmp/work",
        readonly_dirs=["/data"],
        stdout="out.txt",
        stderr="err.txt",
    )
    assert "--dir=/tmp/work=rw" in cmd
    assert "--chdir=/tmp/work" in cmd
    assert "--dir=/data=ro" in cmd
    assert "--stdout=out.txt" in cmd
    assert "--stderr=err.txt" in cmd


def test_build_command_with_env():
    runner = IsolateRunner(isolate_path="isolate", box_id=2)
    cmd = runner.build_command(["/bin/true"], env={"LD_LIBRARY_PATH": "/libs", "FOO": "BAR"})
    assert "--env=LD_LIBRARY_PATH=/libs" in cmd
    assert "--env=FOO=BAR" in cmd


def test_build_command_with_output_limits():
    runner = IsolateRunner(isolate_path="isolate", box_id=3)
    cmd = runner.build_command(
        ["/bin/true"], stdout="out.txt", stderr="err.txt", fsize=64
    )
    assert "--stdout=out.txt" in cmd
    assert "--stderr=err.txt" in cmd
    assert "--fsize=64" in cmd


def test_run_truncates_output(monkeypatch, tmp_path):
    runner = IsolateRunner(isolate_path="isolate", box_id=4)

    monkeypatch.setattr("shutil.which", lambda p: "/usr/bin/isolate")

    captured = {}

    original_build = IsolateRunner.build_command

    def fake_build(self, command, **kwargs):
        captured["workdir"] = kwargs.get("workdir")
        return original_build(self, command, **kwargs)

    monkeypatch.setattr(IsolateRunner, "build_command", fake_build)

    def fake_run(cmd, *args, **kwargs):
        if "--run" in cmd:
            Path(captured["workdir"]).mkdir(parents=True, exist_ok=True)
            (Path(captured["workdir"]) / "stdout.txt").write_text("A" * 100)
            (Path(captured["workdir"]) / "stderr.txt").write_text("B" * 100)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    proc = runner.run(["/bin/echo", "hi"], stdout_limit=10, stderr_limit=10)
    assert proc.stdout == "A" * 10
    assert proc.stderr == "B" * 10
    assert captured["workdir"] is not None

