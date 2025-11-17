# Document Parsing Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglvnd0 \
    mesa-utils \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p storage/parsed storage/temp

# Expose port
EXPOSE 8002

ENV PYTHONUNBUFFERED=1

# Run using run.py
CMD ["python", "run.py"]
