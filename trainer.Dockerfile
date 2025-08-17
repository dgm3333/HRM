# trainer.Dockerfile - image for HRM training environment
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

# Pin locale, timezone, and deterministic CUDA/cuDNN/NCCL settings
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0 \
    CUDA_DEVICE_ORDER=PCI_BUS_ID \
    CUBLAS_WORKSPACE_CONFIG=:4096:8 \
    CUDA_LAUNCH_BLOCKING=1 \
    CUDNN_DETERMINISTIC=1 \
    CUDNN_BENCHMARK=0 \
    TORCH_CUDNN_V8_API_ENABLE=1 \
    NCCL_P2P_DISABLE=1 \
    NCCL_IB_DISABLE=1 \
    NCCL_ASYNC_ERROR_HANDLING=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1

# Minimal build tools for Python package compilation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        cmake \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir pre-commit

WORKDIR /workspace

CMD ["bash"]
