"""
Structuring routes for document processing
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import (
    StructureRequest, 
    StructureResponse, 
    StructuringResult, 
    StructuredData,
    ErrorResponse
)
from app.services.structuring_service import InformationStructuringService
from app.utils.auth_middleware import get_any_user

router = APIRouter(prefix="/structuring", tags=["structuring"])

@router.post("/structure", response_model=StructureResponse)
async def structure_document(
    request: StructureRequest,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Structure a mammography report using Gemini API (authenticated users)"""
    
    try:
        structuring_service = InformationStructuringService(db)
        result = await structuring_service.structure_document(
            document_id=request.document_id,
            extracted_text=request.extracted_text
        )
        
        return StructureResponse(
            structuring_id=result.id,
            document_id=result.document_id,
            status=result.status,
            message="Document structured successfully" if result.status == "completed" else f"Structuring failed: {result.error_message}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structuring failed: {str(e)}")

@router.get("/result/{structuring_id}", response_model=StructuringResult)
async def get_structuring_result(
    structuring_id: str,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Get structuring result by structuring ID (authenticated users)"""
    
    structuring_service = InformationStructuringService(db)
    result = structuring_service.get_structuring_result_by_id(structuring_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Structuring result not found")
    
    return StructuringResult(
        structuring_id=result.id,
        document_id=result.document_id,
        structured_data=StructuredData(**result.structured_data),
        confidence_score=result.confidence_score,
        model_used=result.model_used,
        processing_time=result.processing_time,
        status=result.status,
        created_at=result.created_at
    )

@router.get("/result/document/{document_id}", response_model=StructuringResult)
async def get_structuring_result_by_document(
    document_id: str,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Get structuring result by document ID (authenticated users)"""
    
    structuring_service = InformationStructuringService(db)
    result = structuring_service.get_structuring_result(document_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Structuring result not found")
    
    return StructuringResult(
        structuring_id=result.id,
        document_id=result.document_id,
        structured_data=StructuredData(**result.structured_data),
        confidence_score=result.confidence_score,
        model_used=result.model_used,
        processing_time=result.processing_time,
        status=result.status,
        created_at=result.created_at
    )

@router.post("/structure-internal", response_model=StructureResponse, include_in_schema=False)
async def structure_document_internal(
    request: StructureRequest,
    db: Session = Depends(get_db)
):
    """Internal endpoint for service-to-service communication (no auth required)"""
    
    try:
        structuring_service = InformationStructuringService(db)
        result = await structuring_service.structure_document(
            document_id=request.document_id,
            extracted_text=request.extracted_text
        )
        
        return StructureResponse(
            structuring_id=result.id,
            document_id=result.document_id,
            status=result.status,
            message="Document structured successfully" if result.status == "completed" else f"Structuring failed: {result.error_message}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structuring failed: {str(e)}")

@router.delete("/{document_id}/delete-internal", include_in_schema=False)
async def delete_structuring_result_internal(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Internal endpoint to delete structuring result (no auth required)"""
    
    try:
        from pathlib import Path
        from app.config import RESULTS_DIR
        
        # Delete from database
        from app.models.database import StructuringResult
        result = db.query(StructuringResult).filter(StructuringResult.document_id == document_id).first()
        if result:
            db.delete(result)
            db.commit()
        
        # Delete structured result file if exists
        result_file = RESULTS_DIR / f"{document_id}.json"
        if result_file.exists():
            result_file.unlink()
        
        return {"message": "Structuring result deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
