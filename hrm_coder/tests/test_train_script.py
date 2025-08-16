import subprocess
import sys


def test_train_module_runs():
    """Ensure the training entry point executes end-to-end."""
    result = subprocess.run(
        [sys.executable, "-m", "hrm_coder.train"], capture_output=True, text=True, check=True
    )
    assert "avg_loss=" in result.stdout
    assert "reinforce:" in result.stdout
