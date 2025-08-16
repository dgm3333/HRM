import json
import subprocess
import sys
from pathlib import Path


def test_env_probe_outputs_json(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "env_probe.py"
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "sandboxes" in data
    assert "toolchains" in data
    assert "python" in data
    assert "default_sandbox" in data
    assert "default_compiler" in data
