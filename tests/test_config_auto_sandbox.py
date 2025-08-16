import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from hrm_coder import config as cfg  # noqa: E402
from runners import sandbox_detector  # noqa: E402


def test_load_config_auto_selects_available(monkeypatch):
    monkeypatch.setattr(
        sandbox_detector,
        "select_sandbox",
        lambda info=None, preference=("isolate", "nsjail", "runsc"): ("isolate", {}),
    )
    conf = cfg.load_config(overrides=["runner.sandbox=auto"])
    assert conf.runner.sandbox == "isolate"


def test_load_config_auto_handles_missing(monkeypatch):
    monkeypatch.setattr(
        sandbox_detector,
        "select_sandbox",
        lambda info=None, preference=("isolate", "nsjail", "runsc"): (None, None),
    )
    conf = cfg.load_config(overrides=["runner.sandbox=auto"])
    assert conf.runner.sandbox == "none"

