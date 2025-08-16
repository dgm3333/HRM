import subprocess
import sys
from pathlib import Path


def test_smoke_train_script_runs():
    script = Path(__file__).resolve().parents[1] / "scripts" / "smoke_train.py"
    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, check=True
    )
    assert "avg_loss=" in result.stdout
    assert "reinforce:" in result.stdout
