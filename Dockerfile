# Use NVIDIA CUDA base image
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Python 3.9
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        tzdata \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.9 \
        python3.9-distutils \
        ffmpeg \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
    && ln -sf /usr/share/zoneinfo/UTC /etc/localtime \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python3.9 -m ensurepip --upgrade

# Create explicit symlinks
RUN ln -s /usr/bin/python3.9 /usr/bin/python \
    && ln -s /usr/bin/pip3 /usr/bin/pip

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 5040

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5040", "--timeout", "300", "app:app"]
