import re
from hrm_coder.run_registry import RunRegistry, _get_git_sha


def test_create_run_version_stamp():
    registry = RunRegistry()
    run = registry.create_run(seed=123, docker_digest="sha256:deadbeef")
    assert run.git_sha == _get_git_sha()
    assert run.seed == 123
    assert run.docker_digest == "sha256:deadbeef"
    assert re.fullmatch(r"[0-9a-f]{40}", run.git_sha) or run.git_sha == "unknown"
