"""
Configuration settings for Document Ingestion Service
"""
import os
from pathlib import Path
from typing import List

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Storage settings
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
TEMP_DIR = STORAGE_DIR / "temp"

# Database settings
DATABASE_URL = f"sqlite:///{BASE_DIR}/database.db"

# File upload settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ZIP_SIZE = 100 * 1024 * 1024  # 100MB for zip files
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".zip"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "image/tiff",
    "application/zip",
    "application/x-zip-compressed"
}

# API settings
API_V1_PREFIX = "/api/v1"
HOST = "0.0.0.0"
PORT = 8000

# Security settings
API_KEY = os.getenv("API_KEY", "demo-api-key-123")  # Simple API key for demo

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Service URLs (for inter-service communication)
DOCUMENT_PARSING_URL = os.getenv("DOCUMENT_PARSING_URL", "http://localhost:8002")
INFORMATION_STRUCTURING_URL = os.getenv("INFORMATION_STRUCTURING_URL", "http://localhost:8003")

# Batch processing settings for large uploads
MAX_CONCURRENT_PARSING = int(os.getenv("MAX_CONCURRENT_PARSING", "5"))  # Max parallel parsing requests
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))  # Documents per batch
BATCH_DELAY = float(os.getenv("BATCH_DELAY", "2.0"))  # Seconds between batches

# Retry settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "5.0"))  # Initial retry delay in seconds
RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", "2.0"))  # Exponential backoff multiplier

# Create directories if they don't exist
def create_directories():
    """Create necessary directories"""
    STORAGE_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

# Initialize directories on import
create_directories()
