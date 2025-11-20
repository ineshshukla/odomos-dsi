"""
Document service for handling document operations
"""
import httpx
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.database import Document, ProcessingStatus
from app.models.schemas import UploadMetadata, FileInfo
from app.utils.storage import generate_file_path, save_uploaded_file, get_file_info
from app.utils.validation import validate_upload_file, get_file_size
from app.config import DOCUMENT_PARSING_URL

class DocumentService:
    """Service for document operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        metadata: UploadMetadata,
        clinic_name: Optional[str] = None
    ) -> Document:
        """Upload and store a document"""
        
        # Generate file path
        file_path, unique_filename = generate_file_path(filename)
        
        # Save file to storage
        save_uploaded_file(file_content, file_path)
        
        # Get file size
        file_size = len(file_content)
        
        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=filename,
            file_path=str(file_path),
            file_size=file_size,
            content_type=content_type,
            uploader_id=metadata.uploader_id,
            clinic_name=clinic_name,
            patient_id=metadata.patient_id,
            status="uploaded"
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Create initial processing status
        processing_status = ProcessingStatus(
            document_id=document.id,
            service_name="document_ingestion",
            status="completed"
        )
        self.db.add(processing_status)
        self.db.commit()
        
        # Trigger document parsing service
        await self.trigger_parsing_service(document.id, str(file_path))
        
        return document
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents(
        self, 
        page: int = 1, 
        limit: int = 10, 
        status: Optional[str] = None,
        uploader_id: Optional[str] = None
    ) -> tuple[List[Document], int]:
        """Get paginated list of documents"""
        query = self.db.query(Document)
        
        if status:
            query = query.filter(Document.status == status)
        
        if uploader_id:
            query = query.filter(Document.uploader_id == uploader_id)
        
        # Order by created_at descending (newest first)
        query = query.order_by(Document.created_at.desc())
        
        total = query.count()
        documents = query.offset((page - 1) * limit).limit(limit).all()
        
        return documents, total
    
    def update_document_status(self, document_id: str, status: str) -> bool:
        """Update document status"""
        document = self.get_document(document_id)
        if not document:
            return False
        
        document.status = status
        document.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document and its file"""
        document = self.get_document(document_id)
        if not document:
            return False
        
        try:
            # Delete processing statuses first (foreign key constraint)
            self.db.query(ProcessingStatus).filter(
                ProcessingStatus.document_id == document_id
            ).delete()
            
            # Delete file from storage
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Delete parsed text file if exists
            parsed_file = Path(f"/code/DSI/odomos-dsi/backend/document-parsing/parsed/{document_id}.md")
            if parsed_file.exists():
                parsed_file.unlink()
            
            # Delete structured result file if exists
            structured_file = Path(f"/code/DSI/odomos-dsi/backend/information-structuring/results/{document_id}.json")
            if structured_file.exists():
                structured_file.unlink()
            
            # Delete document from database
            self.db.delete(document)
            self.db.commit()
            
            # Notify other services to delete their records (fire and forget)
            try:
                import httpx
                # Delete from parsing service
                try:
                    httpx.delete(f"{DOCUMENT_PARSING_URL}/parsing/{document_id}/delete-internal", timeout=5.0)
                except:
                    pass
                
                # Delete from structuring service
                try:
                    httpx.delete(f"http://localhost:8003/structuring/{document_id}/delete-internal", timeout=5.0)
                except:
                    pass
            except:
                pass
            
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting document: {str(e)}")
            raise e
    
    def get_processing_statuses(self, document_id: str) -> List[ProcessingStatus]:
        """Get processing statuses for a document"""
        return self.db.query(ProcessingStatus).filter(
            ProcessingStatus.document_id == document_id
        ).all()
    
    def add_processing_status(
        self, 
        document_id: str, 
        service_name: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> ProcessingStatus:
        """Add processing status for a document"""
        processing_status = ProcessingStatus(
            document_id=document_id,
            service_name=service_name,
            status=status,
            error_message=error_message
        )
        self.db.add(processing_status)
        self.db.commit()
        self.db.refresh(processing_status)
        return processing_status
    
    async def trigger_parsing_service(self, document_id: str, file_path: str) -> None:
        """Trigger document parsing service with retry logic (internal service call, no auth needed)"""
        from app.config import MAX_RETRIES, RETRY_DELAY, RETRY_BACKOFF
        
        payload = {
            "document_id": document_id,
            "file_path": file_path
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient() as client:
                    # Internal service call - no authentication required
                    response = await client.post(
                        f"{DOCUMENT_PARSING_URL}/parsing/parse-internal",
                        json=payload,
                        timeout=60.0  # Increased timeout for large files
                    )
                    
                    if response.status_code == 200:
                        # Update status to indicate parsing started
                        self.add_processing_status(
                            document_id, 
                            "document_parsing", 
                            "processing"
                        )
                        return  # Success, exit retry loop
                    elif response.status_code == 429:  # Rate limited
                        retry_delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                        print(f"   ⚠️  Rate limited, retrying in {retry_delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(retry_delay)
                        continue
                    elif response.status_code >= 500:  # Server error, retry
                        retry_delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                        print(f"   ⚠️  Server error {response.status_code}, retrying in {retry_delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:  # Client error, don't retry
                        print(f"   ❌ Parsing service returned {response.status_code}: {response.text}")
                        self.add_processing_status(
                            document_id, 
                            "document_parsing", 
                            "failed", 
                            f"HTTP {response.status_code}"
                        )
                        return
                        
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                retry_delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                if attempt < MAX_RETRIES - 1:
                    print(f"   ⚠️  Connection error, retrying in {retry_delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    print(f"   ❌ Failed after {MAX_RETRIES} attempts: {str(e)}")
                    self.add_processing_status(
                        document_id, 
                        "document_parsing", 
                        "failed", 
                        str(e)
                    )
                    return
            except Exception as e:
                print(f"   ❌ Exception triggering parsing: {str(e)}")
                self.add_processing_status(
                    document_id, 
                    "document_parsing", 
                    "failed", 
                    str(e)
                )
                return
        
        # All retries exhausted
        print(f"   ❌ All {MAX_RETRIES} retry attempts exhausted")
        self.add_processing_status(
            document_id, 
            "document_parsing", 
            "failed", 
            "Max retries exceeded"
        )
    
    async def upload_documents_bulk(
        self,
        files_data: List[Tuple[bytes, str, str]],  # [(file_content, filename, content_type), ...]
        metadata: UploadMetadata,
        clinic_name: Optional[str] = None
    ) -> List[Document]:
        """
        Upload multiple documents in bulk (from zip extraction)
        Processes documents in parallel for efficiency
        
        Args:
            files_data: List of tuples (file_content, filename, content_type)
            metadata: Upload metadata
            clinic_name: Clinic name
            
        Returns:
            List of created Document objects
        """
        documents = []
        
        # Create all documents in database first (fast operation)
        for file_content, filename, content_type in files_data:
            # Generate file path
            file_path, unique_filename = generate_file_path(filename)
            
            # Save file to storage
            save_uploaded_file(file_content, file_path)
            
            # Get file size
            file_size = len(file_content)
            
            # Create document record
            document = Document(
                filename=unique_filename,
                original_filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                content_type=content_type,
                uploader_id=metadata.uploader_id,
                clinic_name=clinic_name,
                patient_id=metadata.patient_id,
                status="uploaded"
            )
            
            self.db.add(document)
            documents.append(document)
        
        # Commit all at once
        self.db.commit()
        
        # Refresh all documents to get IDs
        for doc in documents:
            self.db.refresh(doc)
            
            # Create initial processing status
            processing_status = ProcessingStatus(
                document_id=doc.id,
                service_name="document_ingestion",
                status="completed"
            )
            self.db.add(processing_status)
        
        self.db.commit()
        
        # Trigger parsing service in controlled batches to avoid overload
        from app.config import BATCH_SIZE, BATCH_DELAY, MAX_CONCURRENT_PARSING
        print(f"🚀 Triggering batched parsing for {len(documents)} documents")
        print(f"   Batch size: {BATCH_SIZE}, Concurrent limit: {MAX_CONCURRENT_PARSING}, Delay: {BATCH_DELAY}s")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_PARSING)
        
        async def trigger_with_limit(doc_id: str, file_path: str):
            async with semaphore:
                return await self.trigger_parsing_service(doc_id, file_path)
        
        # Process in batches
        total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(documents))
            batch = documents[start_idx:end_idx]
            
            print(f"   📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} documents)")
            
            # Trigger parsing for this batch
            batch_tasks = [
                trigger_with_limit(doc.id, doc.file_path)
                for doc in batch
            ]
            
            # Run batch with concurrency limit
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Delay between batches (except for last batch)
            if batch_num < total_batches - 1:
                print(f"   ⏳ Waiting {BATCH_DELAY}s before next batch...")
                await asyncio.sleep(BATCH_DELAY)
        
        print(f"✅ Bulk upload completed: {len(documents)} documents")
        return documents
