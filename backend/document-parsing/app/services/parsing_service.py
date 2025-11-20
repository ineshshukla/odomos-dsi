"""
Document parsing service using pypdf (lightweight fallback)
"""
import os
import httpx
import asyncio
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
# from docling.document_converter import DocumentConverter, PdfFormatOption
# from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline_options import PdfPipelineOptions
from pypdf import PdfReader

from app.models.database import ParsingResult
from app.config import PARSED_DIR, INFORMATION_STRUCTURING_URL, DOCUMENT_INGESTION_URL

# Singleton instance of DocumentConverter to avoid reloading models
_converter_instance = None

def get_converter():
    """
    Dummy converter getter since we are using pypdf now.
    Kept for compatibility if we switch back to docling later.
    """
    return None

class DocumentParsingService:
    """Service for parsing documents using pypdf"""
    
    def __init__(self, db: Session):
        self.db = db
        self.converter = get_converter()
    
    async def parse_document(self, document_id: str, file_path: str) -> ParsingResult:
        """Parse document using pypdf with granular progress tracking"""
        import time
        start_time = time.time()
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            print(f"📄 Starting parse for document: {document_id}")
            
            # Update status to "processing"
            await self.update_parsing_progress(document_id, "processing", 5, "Initializing...")
            
            # Handle different file types
            file_extension = os.path.splitext(file_path)[1].lower()
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"   File type: {file_extension}, Size: {file_size_mb:.2f} MB")
            
            extracted_text = ""
            
            if file_extension == '.txt':
                # For text files, just read the content directly (fast)
                await self.update_parsing_progress(document_id, "processing", 50, "Reading text file...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
                await self.update_parsing_progress(document_id, "processing", 90, "Text extracted")
            
            elif file_extension == '.pdf':
                # For PDF files, use pypdf
                await self.update_parsing_progress(document_id, "processing", 15, "Loading PDF...")
                
                # Run conversion in executor to avoid blocking
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    loop = asyncio.get_event_loop()
                    
                    # Update progress during conversion
                    await self.update_parsing_progress(document_id, "processing", 30, "Extracting text from PDF...")
                    
                    extracted_text = await loop.run_in_executor(
                        executor,
                        self._convert_document,
                        file_path,
                        document_id
                    )
                
                await self.update_parsing_progress(document_id, "processing", 85, "Cleaning extracted text...")
            
            else:
                # Fallback for other types (not supported by pypdf)
                raise ValueError(f"Unsupported file type for lightweight parsing: {file_extension}")
            
            # Log extraction stats
            elapsed = time.time() - start_time
            print(f"   ✅ Extraction completed in {elapsed:.2f}s - {len(extracted_text)} characters")
            
            await self.update_parsing_progress(document_id, "processing", 92, "Saving results...")
            
            # Check if result already exists for this document_id
            existing_result = self.db.query(ParsingResult).filter(
                ParsingResult.document_id == document_id
            ).first()
            
            await self.update_parsing_progress(document_id, "processing", 95, "Finalizing...")
            
            if existing_result:
                # Update existing result
                existing_result.extracted_text = extracted_text
                existing_result.status = "completed"
                existing_result.progress = 100
                existing_result.error_message = None
                self.db.commit()
                self.db.refresh(existing_result)
                parsing_result = existing_result
            else:
                # Create new result
                parsing_result = ParsingResult(
                    document_id=document_id,
                    extracted_text=extracted_text,
                    status="completed",
                    progress=100
                )
                self.db.add(parsing_result)
                self.db.commit()
                self.db.refresh(parsing_result)
            
            # Save parsed text to file
            await self.save_parsed_text(document_id, extracted_text)
            
            # Update document-ingestion service about completion
            await self.update_document_status(document_id, "parsed", "completed")
            
            print(f"✅ Parsing completed successfully in {time.time() - start_time:.2f}s")
            
            # Trigger information structuring service
            await self.trigger_structuring_service(document_id, extracted_text)
            
            return parsing_result
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            print(f"❌ Parsing failed after {elapsed:.2f}s: {error_msg}")
            
            # Check if result already exists for this document_id
            existing_result = self.db.query(ParsingResult).filter(
                ParsingResult.document_id == document_id
            ).first()
            
            if existing_result:
                # Update existing result with error
                existing_result.extracted_text = ""
                existing_result.status = "failed"
                existing_result.progress = 0
                existing_result.error_message = error_msg
                self.db.commit()
                self.db.refresh(existing_result)
            else:
                # Create new error result
                error_result = ParsingResult(
                    document_id=document_id,
                    extracted_text="",
                    status="failed",
                    progress=0,
                    error_message=error_msg
                )
                self.db.add(error_result)
                self.db.commit()
                self.db.refresh(error_result)
            
            # Update document-ingestion service about failure
            await self.update_document_status(document_id, "uploaded", "failed", error_msg)
            
            # Log detailed error for debugging
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            
            raise e
    
    def _convert_document(self, file_path: str, document_id: str = None) -> str:
        """Synchronous conversion method using pypdf"""
        import time
        start = time.time()
        print(f"   🔄 Converting document with pypdf...")
        
        text_content = []
        try:
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_content.append(text)
                print(f"      Extracted page {i+1}/{len(reader.pages)}")
        except Exception as e:
            print(f"      Error reading PDF: {e}")
            raise e
            
        full_text = "\n\n".join(text_content)
        
        elapsed = time.time() - start
        print(f"   ⏱️  pypdf conversion took {elapsed:.2f}s")
        return full_text
    
    async def update_parsing_progress(self, document_id: str, status: str, progress: int, message: str = None):
        """Update parsing progress in database with optional message"""
        try:
            existing_result = self.db.query(ParsingResult).filter(
                ParsingResult.document_id == document_id
            ).first()
            
            if existing_result:
                existing_result.status = status
                existing_result.progress = progress
                if message and hasattr(existing_result, 'progress_message'):
                    existing_result.progress_message = message
            else:
                # Create initial record
                parsing_result = ParsingResult(
                    document_id=document_id,
                    extracted_text="",
                    status=status,
                    progress=progress
                )
                self.db.add(parsing_result)
            
            self.db.commit()
            
            # Log progress for debugging
            if progress % 20 == 0 or progress > 90:  # Log at key milestones
                print(f"   📊 Progress: {progress}% - {message if message else status}")
                
        except Exception as e:
            print(f"⚠️  Warning: Failed to update progress: {str(e)}")
    
    async def save_parsed_text(self, document_id: str, text: str) -> None:
        """Save parsed text to file"""
        file_path = PARSED_DIR / f"{document_id}.md"
        file_path.write_text(text, encoding='utf-8')
    
    async def update_document_status(
        self, 
        document_id: str, 
        doc_status: str,
        processing_status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update document status in document-ingestion service"""
        try:
            payload = {
                "document_id": document_id,
                "service_name": "document_parsing",
                "status": processing_status,
                "error_message": error_message
            }
            
            async with httpx.AsyncClient() as client:
                # Update processing status
                await client.post(
                    f"{DOCUMENT_INGESTION_URL}/documents/update-status-internal",
                    json=payload,
                    timeout=10.0
                )
                
                # Update main document status
                if doc_status:
                    status_payload = {"status": doc_status}
                    await client.patch(
                        f"{DOCUMENT_INGESTION_URL}/documents/{document_id}/status-internal",
                        json=status_payload,
                        timeout=10.0
                    )
                    
        except Exception as e:
            print(f"Warning: Failed to update document status: {str(e)}")
    
    async def trigger_structuring_service(self, document_id: str, extracted_text: str) -> None:
        """Trigger information structuring service (internal service call, no auth needed)"""
        print(f"🔄 Triggering structuring service for document: {document_id}")
        print(f"   URL: {INFORMATION_STRUCTURING_URL}/structuring/structure-internal")
        print(f"   Text length: {len(extracted_text)} chars")
        
        try:
            payload = {
                "document_id": document_id,
                "extracted_text": extracted_text
            }
            
            async with httpx.AsyncClient() as client:
                # Internal service call - no authentication required
                response = await client.post(
                    f"{INFORMATION_STRUCTURING_URL}/structuring/structure-internal",
                    json=payload,
                    timeout=30.0
                )
                
                print(f"   Response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"   ⚠️ Warning: Structuring service returned {response.status_code}")
                    print(f"   Response: {response.text}")
                else:
                    print(f"   ✅ Structuring triggered successfully")
                    
        except Exception as e:
            print(f"   ❌ Failed to trigger structuring service: {str(e)}")
    
    def get_parsing_result(self, document_id: str) -> Optional[ParsingResult]:
        """Get parsing result by document ID"""
        return self.db.query(ParsingResult).filter(
            ParsingResult.document_id == document_id
        ).first()
    
    def get_parsing_result_by_id(self, parsing_id: str) -> Optional[ParsingResult]:
        """Get parsing result by parsing ID"""
        return self.db.query(ParsingResult).filter(
            ParsingResult.id == parsing_id
        ).first()
