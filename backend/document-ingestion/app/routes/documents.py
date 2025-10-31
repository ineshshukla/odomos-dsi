"""
Document routes for file upload and management
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import (
    UploadResponse, 
    DocumentStatus, 
    DocumentListResponse, 
    FileInfo,
    ErrorResponse
)
from app.services.document_service import DocumentService
from app.utils.validation import validate_upload_file
from app.utils.auth_middleware import get_clinic_admin, get_any_user

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    patient_id: Optional[str] = Form(None, description="Patient ID (optional)"),
    description: Optional[str] = Form(None, description="Description of the document"),
    current_user: dict = Depends(get_clinic_admin),
    db: Session = Depends(get_db)
):
    """Upload a mammography report document (Clinic Admin only)"""
    
    try:
        # Validate file
        mime_type, _ = validate_upload_file(file)
        
        # Read file content
        file_content = await file.read()
        
        # Create metadata (use current user's ID as uploader)
        from app.models.schemas import UploadMetadata
        metadata = UploadMetadata(
            uploader_id=current_user["sub"],  # User ID from JWT token
            patient_id=patient_id,
            description=description
        )
        
        # Get clinic/organization name from JWT token
        clinic_name = current_user.get("organization", "Unknown Clinic")
        
        # Upload document
        document_service = DocumentService(db)
        document = await document_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            content_type=mime_type,
            metadata=metadata,
            clinic_name=clinic_name
        )
        
        # Create response
        file_info = FileInfo(
            filename=document.original_filename,
            size=document.file_size,
            content_type=document.content_type
        )
        
        return UploadResponse(
            upload_id=document.id,
            status=document.status,
            file_info=file_info,
            created_at=document.created_at,
            message="Document uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{document_id}", response_model=DocumentStatus)
async def get_document_status(
    document_id: str,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Get document status and information (authenticated users)"""
    
    document_service = DocumentService(db)
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get processing statuses
    processing_statuses = document_service.get_processing_statuses(document_id)
    
    file_info = FileInfo(
        filename=document.original_filename,
        size=document.file_size,
        content_type=document.content_type
    )
    
    return DocumentStatus(
        upload_id=document.id,
        status=document.status,
        file_info=file_info,
        created_at=document.created_at,
        updated_at=document.updated_at,
        clinic_name=document.clinic_name,
        upload_timestamp=document.created_at,
        processing_statuses=[
            {
                "service_name": ps.service_name,
                "status": ps.status,
                "error_message": ps.error_message,
                "created_at": ps.created_at
            }
            for ps in processing_statuses
        ]
    )

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """List all documents with pagination (authenticated users)"""
    
    document_service = DocumentService(db)
    # Filter by uploader_id for clinic admins to see only their uploads
    # GCF coordinators can see all documents
    uploader_id = current_user["sub"] if current_user.get("role") == "clinic_admin" else None
    documents, total = document_service.get_documents(page, limit, status, uploader_id)
    
    document_list = []
    for doc in documents:
        file_info = FileInfo(
            filename=doc.original_filename,
            size=doc.file_size,
            content_type=doc.content_type
        )
        
        document_list.append(DocumentStatus(
            upload_id=doc.id,
            status=doc.status,
            file_info=file_info,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            clinic_name=doc.clinic_name,
            upload_timestamp=doc.created_at,
            processing_statuses=[]
        ))
    
    return DocumentListResponse(
        documents=document_list,
        total=total,
        page=page,
        limit=limit
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_clinic_admin),
    db: Session = Depends(get_db)
):
    """Delete a document (Clinic Admin only)"""
    
    document_service = DocumentService(db)
    success = document_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}

# Internal endpoints (no authentication required - for service-to-service communication)

@router.post("/update-status-internal")
async def update_processing_status_internal(
    payload: dict,
    db: Session = Depends(get_db)
):
    """Update processing status (internal endpoint, no auth required)"""
    try:
        document_id = payload.get("document_id")
        service_name = payload.get("service_name")
        status = payload.get("status")
        error_message = payload.get("error_message")
        
        document_service = DocumentService(db)
        document_service.add_processing_status(
            document_id=document_id,
            service_name=service_name,
            status=status,
            error_message=error_message
        )
        
        return {"message": "Status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{document_id}/status-internal")
async def update_document_status_internal(
    document_id: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """Update document status (internal endpoint, no auth required)"""
    try:
        status = payload.get("status")
        
        document_service = DocumentService(db)
        success = document_service.update_document_status(document_id, status)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
