# runner.Dockerfile - base image for C++ execution environment
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        clang \
        clang-format \
        clang-tidy \
        cmake \
        g++ \
        gcc \
        git \
        libgtest-dev \
        ninja-build \
        python3 \
        python3-pip \
        isolate \
    && rm -rf /var/lib/apt/lists/*

# TODO: Install nsjail and sanitizer tools

WORKDIR /workspace

CMD ["bash"]
