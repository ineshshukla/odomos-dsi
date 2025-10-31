"""
Pydantic schemas for Information Structuring Service
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class StructureRequest(BaseModel):
    """Request model for document structuring"""
    document_id: str = Field(..., description="Document ID from parsing service")
    extracted_text: str = Field(..., description="Extracted text from parsing service")

class StructureResponse(BaseModel):
    """Response model for structuring request"""
    structuring_id: str
    document_id: str
    status: str
    message: str

class StructuredData(BaseModel):
    """Structured mammography data model - matches training data format"""
    medical_unit: str = Field(default="unknown", description="Medical unit or hospital name")
    full_report: str = Field(default="unknown", description="Complete report text")
    lmp: str = Field(default="unknown", description="Last menstrual period")
    hormonal_therapy: str = Field(default="unknown", description="Hormonal therapy status")
    family_history: str = Field(default="unknown", description="Family history of breast pathology")
    reason: str = Field(default="unknown", description="Reason for mammography examination")
    observations: str = Field(default="unknown", description="Clinical observations and findings")
    conclusion: str = Field(default="unknown", description="Radiologist's conclusion/impression")
    recommendations: str = Field(default="unknown", description="Recommended follow-up actions")
    birads: str = Field(default="unknown", description="BI-RADS score (0-6)")
    age: str = Field(default="unknown", description="Patient age")
    children: str = Field(default="unknown", description="Number of children")

class StructuringResult(BaseModel):
    """Complete structuring result model"""
    structuring_id: str
    document_id: str
    structured_data: StructuredData
    confidence_score: Optional[float]
    model_used: str
    processing_time: Optional[int]
    status: str
    created_at: datetime

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    database: str
    gemini_api: str
