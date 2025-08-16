from hrm_coder.config import load_config


def test_load_config_defaults():
    cfg = load_config()
    assert cfg.model.name == "small"
    assert cfg.dataset.name == "humaneval-cpp"
    assert cfg.runner.compiler == "g++"
    assert cfg.runner.timeout == 5
    assert cfg.acceptance.pass_at_1 == 0.5
    assert cfg.acceptance.max_timeout_rate == 0.05
    assert cfg.training.baseline_coef == 0.5
    assert cfg.training.curriculum_stage == "visible"
    assert cfg.environment.seed == 0
    assert cfg.environment.timezone == "UTC"


def test_load_config_override():
    cfg = load_config([
        "model.learning_rate=0.01",
        "runner.timeout=10",
        "acceptance.pass_at_1=0.9",
        "training.baseline_coef=0.7",
        "training.curriculum_stage=hidden",
        "environment.seed=123",
    ])
    assert cfg.model.learning_rate == 0.01
    assert cfg.runner.timeout == 10
    assert cfg.acceptance.pass_at_1 == 0.9
    assert cfg.training.baseline_coef == 0.7
    assert cfg.training.curriculum_stage == "hidden"
    assert cfg.environment.seed == 123
