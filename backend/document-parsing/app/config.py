"""
Configuration settings for Document Parsing Service
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Storage settings
STORAGE_DIR = BASE_DIR / "storage"
PARSED_DIR = STORAGE_DIR / "parsed"
TEMP_DIR = STORAGE_DIR / "temp"

# Database settings
DATABASE_URL = f"sqlite:///{BASE_DIR}/parsing.db"

# API settings
API_V1_PREFIX = "/api/v1"
HOST = "0.0.0.0"
PORT = 8002

# Security settings
API_KEY = os.getenv("API_KEY", "demo-api-key-123")

# Service URLs
DOCUMENT_INGESTION_URL = os.getenv("DOCUMENT_INGESTION_URL", "http://localhost:8001")
INFORMATION_STRUCTURING_URL = os.getenv("INFORMATION_STRUCTURING_URL", "http://localhost:8003")

# Processing limits
MAX_CONCURRENT_PARSING = int(os.getenv("MAX_CONCURRENT_PARSING", "3"))  # Limit concurrent docling operations
PARSING_TIMEOUT = int(os.getenv("PARSING_TIMEOUT", "120"))  # Seconds per document

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Create directories if they don't exist
def create_directories():
    """Create necessary directories"""
    STORAGE_DIR.mkdir(exist_ok=True)
    PARSED_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

# Initialize directories on import
create_directories()
