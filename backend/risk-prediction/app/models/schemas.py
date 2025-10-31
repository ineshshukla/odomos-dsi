"""
Pydantic schemas for Risk Prediction Service
"""
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    """Request model for prediction"""
    document_id: str = Field(..., description="Document ID")
    structuring_id: Optional[str] = Field(None, description="Structuring result ID")
    structured_data: Dict = Field(..., description="Structured mammography data from structuring service")

class PredictionResponse(BaseModel):
    """Response model for prediction request"""
    prediction_id: str
    document_id: str
    status: str
    message: str

class PredictionResult(BaseModel):
    """Complete prediction result model"""
    prediction_id: str
    document_id: str
    structuring_id: Optional[str]
    predicted_birads: str
    predicted_label_id: int
    confidence_score: float
    probabilities: Dict[str, float]
    risk_level: str
    review_status: Optional[str] = "New"
    coordinator_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    model_version: str
    processing_time: Optional[float]
    status: str
    created_at: datetime

class ReviewStatusUpdate(BaseModel):
    """Model for updating review status"""
    review_status: str = Field(..., description="Review status: New, Under Review, Follow-up Initiated, Review Complete")
    coordinator_notes: Optional[str] = Field(None, description="Coordinator's notes")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    database: str
    model_loaded: bool
    model_path: str

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int
