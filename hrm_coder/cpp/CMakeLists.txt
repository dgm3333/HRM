cmake_minimum_required(VERSION 3.20)
project(hrm_coder_cpp LANGUAGES CXX)

add_executable(dummy placeholder.cc)

enable_testing()
add_test(NAME dummy COMMAND dummy)
