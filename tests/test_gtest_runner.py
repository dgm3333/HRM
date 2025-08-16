from pathlib import Path
import sys
import subprocess

sys.path.append(str(Path(__file__).resolve().parents[1]))

from runners.gtest_runner import run_gtests


def build_sample_test(tmpdir: Path) -> Path:
    code = (
        "#include <gtest/gtest.h>\n"
        "TEST(Sample, Adds){EXPECT_EQ(2+2,4);}\n"
        "int main(int argc,char**argv){::testing::InitGoogleTest(&argc, argv);return RUN_ALL_TESTS();}\n"
    )
    src = tmpdir / "sample_test.cpp"
    src.write_text(code)
    binary = tmpdir / "sample_test"
    subprocess.check_call([
        "g++",
        str(src),
        "-lgtest",
        "-lgtest_main",
        "-pthread",
        "-o",
        str(binary),
    ])
    return binary


def test_run_gtests(tmp_path):
    binary = build_sample_test(tmp_path)
    result = run_gtests(binary)
    assert result["tests"] == 1
    assert result["failures"] == 0
    assert result["cases"][0]["name"] == "Adds"
    assert result["cases"][0]["passed"]
