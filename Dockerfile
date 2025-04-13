# Use NVIDIA CUDA base image with Python 3.9
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies and Python 3.9
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository universe \
    && apt-get update \
    && apt-get install -y \
    python3.9 python3-distutils python3-pip \
    ffmpeg libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Python 3.9 as the default Python version without update-alternatives
RUN ln -sf /usr/bin/python3.9 /usr/bin/python

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
