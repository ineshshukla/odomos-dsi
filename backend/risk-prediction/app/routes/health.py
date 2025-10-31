"""
Health check routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.database import get_db
from app.models.schemas import HealthResponse
from app.config import SERVICE_VERSION, MODEL_PATH
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    
    # Check database
    try:
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception:
        database_status = "unhealthy"
    
    # Check if model is loaded
    try:
        service = PredictionService(db)
        model_loaded = service.is_model_loaded()
    except Exception:
        model_loaded = False
    
    return HealthResponse(
        status="healthy" if database_status == "healthy" and model_loaded else "unhealthy",
        timestamp=datetime.utcnow(),
        version=SERVICE_VERSION,
        database=database_status,
        model_loaded=model_loaded,
        model_path=MODEL_PATH
    )
