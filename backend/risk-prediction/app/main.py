"""
Risk Prediction Service - Main FastAPI Application
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import LOG_LEVEL, LOG_FORMAT, CORS_ORIGINS, SERVICE_VERSION, PORT
from app.models.database import create_tables
from app.routes import health, predictions

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Risk Prediction Service...")
    create_tables()
    logger.info("Database tables created successfully")
    
    # Try to load model at startup (with error handling)
    try:
        from app.services.prediction_service import PredictionService
        from app.models.database import SessionLocal
        db = SessionLocal()
        try:
            service = PredictionService(db)
            if service.is_model_loaded():
                logger.info("Model loaded and ready for predictions")
            else:
                logger.warning("Model failed to load - check MODEL_PATH configuration")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to initialize prediction service: {e}")
        logger.warning("Service will start but predictions may fail")
    
    yield
    # Shutdown
    logger.info("Shutting down Risk Prediction Service...")

# Create FastAPI application
app = FastAPI(
    title="Risk Prediction Service",
    description="Microservice for BI-RADS prediction and cancer risk assessment using BioGPT",
    version=SERVICE_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(predictions.router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Risk Prediction Service",
        "version": SERVICE_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health/",
            "predict": "/predictions/predict",
            "get_by_document": "/predictions/document/{document_id}",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        log_level="info"
    )
