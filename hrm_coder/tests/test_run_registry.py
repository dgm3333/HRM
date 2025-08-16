from hrm_coder.run_registry import registry


def test_run_records_version_info():
    run = registry.create_run({"seed": "7"})
    assert run.version.git_sha
    assert run.version.seed == 7
