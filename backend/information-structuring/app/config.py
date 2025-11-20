"""
Configuration settings for Information Structuring Service
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Storage settings
STORAGE_DIR = BASE_DIR / "storage"
RESULTS_DIR = STORAGE_DIR / "results"

# Database settings
DATABASE_URL = f"sqlite:///{BASE_DIR}/structuring.db"

# API settings
API_V1_PREFIX = "/api/v1"
HOST = "0.0.0.0"
PORT = 8003

# Security settings
API_KEY = os.getenv("API_KEY", "demo-api-key-123")

# Gemini API settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Rate limiting for Gemini API (free tier: 15 requests per minute)
GEMINI_MAX_CONCURRENT = int(os.getenv("GEMINI_MAX_CONCURRENT", "3"))  # Max concurrent API calls
GEMINI_RATE_LIMIT_DELAY = float(os.getenv("GEMINI_RATE_LIMIT_DELAY", "4.0"))  # Delay between requests (seconds)
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
GEMINI_RETRY_DELAY = float(os.getenv("GEMINI_RETRY_DELAY", "10.0"))  # Delay before retry

# Service URLs
DOCUMENT_INGESTION_URL = os.getenv("DOCUMENT_INGESTION_URL", "http://localhost:8001")
DOCUMENT_PARSING_URL = os.getenv("DOCUMENT_PARSING_URL", "http://localhost:8002")
FEATURE_ENGINEERING_URL = os.getenv("FEATURE_ENGINEERING_URL", "http://localhost:8004")
RISK_PREDICTION_URL = os.getenv("RISK_PREDICTION_URL", "http://localhost:8004")

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Create directories if they don't exist
def create_directories():
    """Create necessary directories"""
    STORAGE_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

# Initialize directories on import
create_directories()
