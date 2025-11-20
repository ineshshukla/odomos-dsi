"""
Document routes for file upload and management
"""
import zipfile
import io
from typing import Optional, List
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

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (PDF, DICOM, or ZIP)"),
    patient_id: Optional[str] = Form(None, description="Patient ID (optional)"),
    description: Optional[str] = Form(None, description="Description of the document"),
    current_user: dict = Depends(get_clinic_admin),
    db: Session = Depends(get_db)
):
    """Upload a mammography report document or ZIP file containing multiple reports (Clinic Admin only)"""
    
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
        
        document_service = DocumentService(db)
        
        # Check if it's a ZIP file
        if mime_type == "application/zip" or mime_type in ["application/x-zip-compressed", "application/x-zip"]:
            # Handle ZIP file - extract and process all PDFs
            pdf_files = []
            try:
                with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_ref:
                    # Get list of PDF files in the zip
                    pdf_names = [name for name in zip_ref.namelist() 
                                if name.lower().endswith('.pdf') and not name.startswith('__MACOSX')]
                    
                    if not pdf_names:
                        raise HTTPException(
                            status_code=400, 
                            detail="No PDF files found in the ZIP archive"
                        )
                    
                    # Extract each PDF
                    for pdf_name in pdf_names:
                        try:
                            # Read PDF content from zip
                            pdf_content = zip_ref.read(pdf_name)
                            
                            # Get just the filename (remove directory path if present)
                            filename = pdf_name.split('/')[-1]
                            
                            # Skip hidden files and system files
                            if filename.startswith('.') or filename.startswith('_'):
                                continue
                            
                            pdf_files.append((pdf_content, filename, "application/pdf"))
                            
                        except Exception as e:
                            print(f"⚠️  Warning: Could not extract {pdf_name}: {str(e)}")
                            continue
                    
            except zipfile.BadZipFile:
                raise HTTPException(status_code=400, detail="Invalid or corrupted ZIP file")
            
            if not pdf_files:
                raise HTTPException(
                    status_code=400, 
                    detail="No valid documents found in ZIP file"
                )
            
            # Upload all documents
            documents = await document_service.upload_documents_bulk(
                files_data=pdf_files,
                metadata=metadata,
                clinic_name=clinic_name
            )
            
            # Return list of uploaded documents
            uploaded_documents = []
            for document in documents:
                file_info = FileInfo(
                    filename=document.original_filename,
                    size=document.file_size,
                    content_type=document.content_type
                )
                
                uploaded_documents.append(UploadResponse(
                    upload_id=document.id,
                    status=document.status,
                    file_info=file_info,
                    created_at=document.created_at,
                    message="Document uploaded successfully"
                ))
            
            return uploaded_documents
        
        else:
            # Handle single file upload (PDF, DICOM, etc.)
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

@router.post("/upload-zip")
async def upload_zip_batch(
    file: UploadFile = File(..., description="ZIP file containing multiple PDFs"),
    patient_id: Optional[str] = Form(None, description="Patient ID (optional)"),
    description: Optional[str] = Form(None, description="Description of the documents"),
    current_user: dict = Depends(get_clinic_admin),
    db: Session = Depends(get_db)
):
    """
    Upload a ZIP file containing multiple mammography reports (Clinic Admin only)
    Extracts and processes all PDFs in parallel for efficiency
    """
    
    try:
        # Validate zip file
        if not file.filename or not file.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Validate file size (larger limit for zip)
        mime_type, _ = validate_upload_file(file, is_zip=True)
        
        # Read zip file content
        zip_content = await file.read()
        
        # Extract PDF files from zip
        pdf_files = []
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
                # Get list of PDF files in the zip
                pdf_names = [name for name in zip_ref.namelist() 
                            if name.lower().endswith('.pdf') and not name.startswith('__MACOSX')]
                
                if not pdf_names:
                    raise HTTPException(
                        status_code=400, 
                        detail="No PDF files found in the ZIP archive"
                    )
                
                print(f"📦 Extracting {len(pdf_names)} PDF files from ZIP")
                
                # Extract each PDF
                for pdf_name in pdf_names:
                    try:
                        # Read PDF content from zip
                        pdf_content = zip_ref.read(pdf_name)
                        
                        # Get just the filename (remove directory path if present)
                        filename = pdf_name.split('/')[-1]
                        
                        # Skip hidden files and system files
                        if filename.startswith('.') or filename.startswith('_'):
                            continue
                        
                        pdf_files.append((pdf_content, filename, "application/pdf"))
                        
                    except Exception as e:
                        print(f"⚠️  Warning: Could not extract {pdf_name}: {str(e)}")
                        continue
                
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid or corrupted ZIP file")
        
        if not pdf_files:
            raise HTTPException(
                status_code=400, 
                detail="No valid PDF files could be extracted from the ZIP archive"
            )
        
        print(f"✅ Successfully extracted {len(pdf_files)} PDF files")
        
        # Create metadata
        from app.models.schemas import UploadMetadata
        metadata = UploadMetadata(
            uploader_id=current_user["sub"],
            patient_id=patient_id,
            description=description
        )
        
        # Get clinic/organization name from JWT token
        clinic_name = current_user.get("organization", "Unknown Clinic")
        
        # Upload all documents in bulk (processes in parallel)
        document_service = DocumentService(db)
        documents = await document_service.upload_documents_bulk(
            files_data=pdf_files,
            metadata=metadata,
            clinic_name=clinic_name
        )
        
        # Create response with all uploaded documents
        uploaded_documents = []
        for document in documents:
            file_info = FileInfo(
                filename=document.original_filename,
                size=document.file_size,
                content_type=document.content_type
            )
            
            uploaded_documents.append({
                "upload_id": document.id,
                "status": document.status,
                "file_info": file_info,
                "created_at": document.created_at
            })
        
        return {
            "message": f"Successfully uploaded {len(documents)} documents from ZIP file",
            "total_documents": len(documents),
            "documents": uploaded_documents
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Zip upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Zip upload failed: {str(e)}")

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
