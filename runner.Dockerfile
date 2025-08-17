# runner.Dockerfile - base image for C++ execution environment
FROM ubuntu:22.04

# Pin locale and timezone for deterministic behavior
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC

# Install toolchains, sandboxes, and coverage utilities
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
        isolate \
        lcov \
        libcap-dev \
        libclang-rt-14-dev \
        libgtest-dev \
        libnl-route-3-dev \
        libprotobuf-dev \
        libseccomp-dev \
        llvm-14 \
        llvm-14-tools \
        ninja-build \
        pkg-config \
        protobuf-compiler \
        python3 \
        python3-pip \
        tzdata \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* && \
    git clone https://github.com/google/nsjail.git /tmp/nsjail && \
    make -C /tmp/nsjail && \
    mv /tmp/nsjail/nsjail /usr/local/bin/nsjail && \
    rm -rf /tmp/nsjail && \
    cmake -S /usr/src/googletest -B /tmp/googletest && \
    cmake --build /tmp/googletest && \
    cp /tmp/googletest/lib/*.a /usr/local/lib/ && \
    rm -rf /tmp/googletest

# nsjail provides process isolation; llvm packages enable sanitizer builds

WORKDIR /workspace

CMD ["bash"]
