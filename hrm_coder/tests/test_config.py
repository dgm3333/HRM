from hrm_coder.config import load_config


def test_load_config_defaults():
    cfg = load_config()
    assert cfg.model.name == "small"
    assert cfg.dataset.name == "humaneval-cpp"
    assert cfg.runner.compiler == "g++"
    assert cfg.runner.timeout == 5


def test_load_config_override():
    cfg = load_config([
        "model.learning_rate=0.01",
        "runner.timeout=10",
    ])
    assert cfg.model.learning_rate == 0.01
    assert cfg.runner.timeout == 10
