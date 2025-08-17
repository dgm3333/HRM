import json
import subprocess
import sys
from pathlib import Path


def test_sandbox_smoke_outputs_json(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "sandbox_smoke.py"
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
    for name in ("isolate", "nsjail", "runsc"):
        assert name in data
        assert "available" in data[name]
        assert "ok" in data[name]
