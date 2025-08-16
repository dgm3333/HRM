import subprocess
import sys


def test_train_module_runs(tmp_path):
    """Ensure the training entry point executes end-to-end and checkpoints."""
    ckpt = tmp_path / "ckpt.pt"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hrm_coder.train",
            "--checkpoint",
            str(ckpt),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "avg_loss=" in result.stdout
    assert "Checkpoint written" in result.stdout
    assert ckpt.exists()

    # Resume to exercise load path
    result2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "hrm_coder.train",
            "--checkpoint",
            str(ckpt),
            "--resume",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Resumed from" in result2.stdout
