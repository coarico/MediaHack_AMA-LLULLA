FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Trigger Railway snapshot refresh

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep this layer tied to the backend image so Railway watch paths trigger rebuilds.
# Upgrade pip and install build dependencies
RUN pip install --upgrade pip setuptools==80.9.0 wheel

# Copy requirements and install
COPY requirements.txt .

RUN pip install --no-build-isolation openai-whisper==20231117 \
    && grep -v '^openai-whisper==' requirements.txt > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt

# Copy application
COPY . .

# Start command
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
