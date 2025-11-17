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
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Run database migrations
RUN python migrate_add_progress.py

# Pre-download RapidOCR models and fonts to avoid runtime downloads
# These are the exact models and resources that get downloaded at runtime
RUN mkdir -p /usr/local/lib/python3.11/site-packages/rapidocr/models && \
    cd /usr/local/lib/python3.11/site-packages/rapidocr/models && \
    echo "Downloading RapidOCR models and fonts..." && \
    curl -L -o ch_PP-OCRv4_det_infer.pth "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/torch/PP-OCRv4/det/ch_PP-OCRv4_det_infer.pth" && \
    curl -L -o ch_ptocr_mobile_v2.0_cls_infer.pth "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/torch/PP-OCRv4/cls/ch_ptocr_mobile_v2.0_cls_infer.pth" && \
    curl -L -o ch_PP-OCRv4_rec_infer.pth "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/torch/PP-OCRv4/rec/ch_PP-OCRv4_rec_infer.pth" && \
    curl -L -o FZYTK.TTF "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.4.0/resources/fonts/FZYTK.TTF" && \
    echo "✅ RapidOCR models and fonts downloaded successfully!"

# Create storage directories
RUN mkdir -p storage/parsed storage/temp

# Expose port
EXPOSE 8002

ENV PYTHONUNBUFFERED=1

# Run using run.py
CMD ["python", "run.py"]
