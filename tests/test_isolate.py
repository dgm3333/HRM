from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from runners.isolate import IsolateRunner


def test_build_command_has_no_network_by_default():
    runner = IsolateRunner(isolate_path="isolate")
    cmd = runner.build_command(
        ["/bin/echo", "hello"],
        time_limit=1,
        wall_time=2,
        memory=1024,
        processes=1,
    )
    assert cmd[0] == "isolate"
    assert "--net=none" in cmd
    assert "--" in cmd
    assert cmd[-2:] == ["/bin/echo", "hello"]

