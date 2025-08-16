from hrm_coder.config import load_config


def test_load_config_defaults():
    cfg = load_config()
    assert cfg.model.name == "small"
    assert cfg.dataset.name == "humaneval-cpp"


def test_load_config_override():
    cfg = load_config(["model.learning_rate=0.01"])
    assert cfg.model.learning_rate == 0.01
