from pathlib import Path
import subprocess

from runners.binary_adapter import BinarySandboxAdapter, SANITIZER_ENV
from runners.cpp_runner import compile_cpp


def test_binary_adapter_injects_sanitizers(tmp_path: Path) -> None:
    src = tmp_path / "main.cpp"
    src.write_text("int main(){return 0;}")
    res = compile_cpp(src)
    assert res.success and res.binary is not None

    class CaptureEnvRunner:
        def __init__(self) -> None:
            self.env = None

        def run(self, cmd, **kwargs):
            self.env = kwargs.get("env")
            return subprocess.run(
                cmd,
                input=kwargs.get("stdin"),
                capture_output=True,
                text=True,
                check=False,
                cwd=kwargs.get("workdir"),
            )

    runner = CaptureEnvRunner()
    adapter = BinarySandboxAdapter(runner)
    code, _, _ = adapter.run(res.binary)
    assert code == 0
    assert runner.env is not None
    assert runner.env["ASAN_OPTIONS"] == SANITIZER_ENV["ASAN_OPTIONS"]
    assert runner.env["UBSAN_OPTIONS"] == SANITIZER_ENV["UBSAN_OPTIONS"]
