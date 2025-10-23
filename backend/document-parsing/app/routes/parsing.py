"""
Parsing routes for document processing
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import ParseRequest, ParseResponse, ParsingResult, ErrorResponse
from app.services.parsing_service import DocumentParsingService
from app.utils.auth_middleware import get_any_user

router = APIRouter(prefix="/parsing", tags=["parsing"])

@router.post("/parse", response_model=ParseResponse)
async def parse_document(
    request: ParseRequest,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Parse a document using docling (authenticated users)"""
    
    try:
        parsing_service = DocumentParsingService(db)
        result = await parsing_service.parse_document(
            document_id=request.document_id,
            file_path=request.file_path
        )
        
        return ParseResponse(
            parsing_id=result.id,
            document_id=result.document_id,
            status=result.status,
            message="Document parsed successfully"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

@router.get("/result/{parsing_id}", response_model=ParsingResult)
async def get_parsing_result(
    parsing_id: str,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Get parsing result by parsing ID (authenticated users)"""
    
    parsing_service = DocumentParsingService(db)
    result = parsing_service.get_parsing_result_by_id(parsing_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Parsing result not found")
    
    return ParsingResult(
        parsing_id=result.id,
        document_id=result.document_id,
        extracted_text=result.extracted_text,
        status=result.status,
        created_at=result.created_at
    )

@router.get("/result/document/{document_id}", response_model=ParsingResult)
async def get_parsing_result_by_document(
    document_id: str,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Get parsing result by document ID (authenticated users)"""
    
    parsing_service = DocumentParsingService(db)
    result = parsing_service.get_parsing_result(document_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Parsing result not found")
    
    return ParsingResult(
        parsing_id=result.id,
        document_id=result.document_id,
        extracted_text=result.extracted_text,
        status=result.status,
        created_at=result.created_at
    )

@router.post("/parse-internal", response_model=ParseResponse, include_in_schema=False)
async def parse_document_internal(
    request: ParseRequest,
    db: Session = Depends(get_db)
):
    """Internal endpoint for service-to-service communication (no auth required)"""
    
    try:
        parsing_service = DocumentParsingService(db)
        result = await parsing_service.parse_document(
            document_id=request.document_id,
            file_path=request.file_path
        )
        
        return ParseResponse(
            parsing_id=result.id,
            document_id=result.document_id,
            status=result.status,
            message="Document parsed successfully"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

@router.delete("/{document_id}/delete-internal", include_in_schema=False)
async def delete_parsing_result_internal(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Internal endpoint to delete parsing result (no auth required)"""
    
    try:
        from pathlib import Path
        from app.config import PARSED_DIR
        
        # Delete from database
        from app.models.database import ParsingResult
        result = db.query(ParsingResult).filter(ParsingResult.document_id == document_id).first()
        if result:
            db.delete(result)
            db.commit()
        
        # Delete parsed file if exists
        parsed_file = PARSED_DIR / f"{document_id}.md"
        if parsed_file.exists():
            parsed_file.unlink()
        
        return {"message": "Parsing result deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
