FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install build dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install
COPY requirements.txt .

# Install openai-whisper from git to avoid pkg_resources bug
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git@v20231117

# Install remaining requirements (excluding openai-whisper)
RUN grep -v "openai-whisper" requirements.txt > requirements_temp.txt && \
    pip install --no-cache-dir -r requirements_temp.txt && \
    rm requirements_temp.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8001

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
