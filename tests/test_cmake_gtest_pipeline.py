from pathlib import Path
import sys
import shutil
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from runners.cpp_build import build_and_run_gtests  # noqa: E402

if (
    shutil.which("g++") is None
    or not Path("/usr/include/gtest/gtest.h").exists()
):
    pytest.skip("gtest headers not available", allow_module_level=True)


def test_build_and_run_gtests(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text(
        """
cmake_minimum_required(VERSION 3.20)
project(sample LANGUAGES CXX)
find_package(GTest REQUIRED)
add_executable(sample_test sample_test.cpp)
target_link_libraries(sample_test GTest::gtest_main)
enable_testing()
add_test(NAME sample_test COMMAND sample_test)
"""
    )
    (src_dir / "sample_test.cpp").write_text(
        """
#include <gtest/gtest.h>
int add(int a,int b){return a+b;}
TEST(Sample, Adds){EXPECT_EQ(add(2,2),4);}
int main(int argc,char** argv){
    ::testing::InitGoogleTest(&argc,argv);
    return RUN_ALL_TESTS();
}
"""
    )
    build_dir = tmp_path / "build"
    result = build_and_run_gtests(
        src_dir, build_dir, test_binary="sample_test"
    )
    assert result["configure_returncode"] == 0, result["configure_stderr"]
    assert result["build_returncode"] == 0, result["build_stderr"]
    assert result["tests"] == 1
    assert result["failures"] == 0
    assert result["cases"][0]["name"] == "Adds"
    assert result["cases"][0]["passed"]
