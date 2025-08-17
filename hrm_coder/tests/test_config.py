from pathlib import Path

from hrm_coder.config import load_config


def test_load_config_defaults():
    cfg = load_config()
    assert cfg.model.name == "small"
    assert cfg.dataset.name == "humaneval-cpp"
    assert cfg.runner.compiler == "g++"
    assert cfg.runner.timeout == 5
    assert cfg.runner.memory_limit == 256
    assert cfg.runner.cpus == 1
    assert cfg.runner.network is False
    assert cfg.acceptance.pass_at_1 == 0.5
    assert cfg.acceptance.max_timeout_rate == 0.05
    assert cfg.training.baseline_coef == 0.5
    assert cfg.training.curriculum_stage == "visible"
    assert cfg.environment.seed == 0
    assert cfg.environment.timezone == "UTC"
    project_root = Path(__file__).resolve().parents[2]
    assert cfg.paths.data_root == project_root / "data"
    assert cfg.paths.runs_root == project_root / "runs"
    assert cfg.paths.artifacts_root == project_root / "artifacts"


def test_load_config_override():
    overrides = [
        "model.learning_rate=0.01",
        "runner.timeout=10",
        "runner.memory_limit=512",
        "runner.cpus=2",
        "runner.network=true",
        "acceptance.pass_at_1=0.9",
        "training.baseline_coef=0.7",
        "training.curriculum_stage=hidden",
        "environment.seed=123",
    ]
    cfg = load_config([
        *overrides,
    ])
    assert cfg.model.learning_rate == 0.01
    assert cfg.runner.timeout == 10
    assert cfg.runner.memory_limit == 512
    assert cfg.runner.cpus == 2
    assert cfg.runner.network is True
    assert cfg.acceptance.pass_at_1 == 0.9
    assert cfg.training.baseline_coef == 0.7
    assert cfg.training.curriculum_stage == "hidden"
    assert cfg.environment.seed == 123


def test_load_config_path_override(tmp_path):
    cfg = load_config([
        f"paths.data_root={tmp_path / 'data'}",
        f"paths.runs_root={tmp_path / 'runs'}",
        f"paths.artifacts_root={tmp_path / 'artifacts'}",
    ])
    assert cfg.paths.data_root == tmp_path / "data"
    assert cfg.paths.runs_root == tmp_path / "runs"
    assert cfg.paths.artifacts_root == tmp_path / "artifacts"
