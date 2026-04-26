FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# System deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Python deps
RUN python3 -m pip install --upgrade pip
RUN pip install \
    runpod \
    boto3 \
    openai-whisper \
    torch

WORKDIR /app

# Copy worker code
COPY handler.py /app/handler.py

# Run the worker
CMD ["python3", "handler.py"]