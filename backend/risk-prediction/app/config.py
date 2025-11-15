"""
Risk Prediction Service Configuration
"""
import os
from pathlib import Path

# Service Configuration
SERVICE_NAME = "risk-prediction"
SERVICE_VERSION = "1.0.0"
PORT = 8004

# Model Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
# Point to the model in model-training directory - use relative path from backend directory
BACKEND_DIR = BASE_DIR.parent
MODEL_PATH = os.getenv("MODEL_PATH", str(BACKEND_DIR / "model-training" / "biogpt_birads_classifier" / "best_model"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/predictions.db")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Service URLs (for inter-service communication)
DOCUMENT_INGESTION_URL = os.getenv("DOCUMENT_INGESTION_URL", "http://localhost:8001")
INFORMATION_STRUCTURING_URL = os.getenv("INFORMATION_STRUCTURING_URL", "http://localhost:8003")

# Risk Level Thresholds
RISK_THRESHOLDS = {
    "high": ["4", "5", "6"],  # BI-RADS 4, 5, 6
    "medium": ["3"],           # BI-RADS 3
    "low": ["1", "2"],         # BI-RADS 1, 2
    "needs_assessment": ["0"]  # BI-RADS 0
}

# Confidence Thresholds
MIN_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to accept prediction
