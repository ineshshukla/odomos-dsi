"""
Pydantic schemas for request/response models
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class UploadMetadata(BaseModel):
    """Metadata for file upload"""
    uploader_id: str = Field(..., description="ID of the person uploading the file")
    patient_id: Optional[str] = Field(None, description="Patient ID (optional)")
    description: Optional[str] = Field(None, description="Description of the document")

class FileInfo(BaseModel):
    """File information"""
    filename: str
    size: int
    content_type: str

class UploadResponse(BaseModel):
    """Response model for file upload"""
    upload_id: str
    status: str
    file_info: FileInfo
    created_at: datetime
    message: str

class DocumentStatus(BaseModel):
    """Document status response"""
    upload_id: str
    status: str
    file_info: FileInfo
    created_at: datetime
    updated_at: datetime
    clinic_name: Optional[str] = None
    upload_timestamp: Optional[datetime] = None
    processing_statuses: List[dict] = []

class DocumentListResponse(BaseModel):
    """Response for document listing"""
    documents: List[DocumentStatus]
    total: int
    page: int
    limit: int

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
    storage: str
