# Use NVIDIA CUDA base image with Python 3.9
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.9 python3.9-distutils python3-pip \
    ffmpeg libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Python alternatives
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1

# Upgrade pip and install dependencies
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose the app port
EXPOSE 5040

# Start with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5040", "--timeout", "300", "app:app"]
