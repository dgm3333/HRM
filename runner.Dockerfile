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
        pkg-config \
        libprotobuf-dev \
        protobuf-compiler \
        libnl-route-3-dev \
        libcap-dev \
        libseccomp-dev \
        zlib1g-dev \
        llvm \
        libclang-rt-14-dev \
    && rm -rf /var/lib/apt/lists/* && \
    git clone https://github.com/google/nsjail.git /tmp/nsjail && \
    make -C /tmp/nsjail && \
    mv /tmp/nsjail/nsjail /usr/local/bin/nsjail && \
    rm -rf /tmp/nsjail

# nsjail provides process isolation; llvm packages enable sanitizer builds

WORKDIR /workspace

CMD ["bash"]
