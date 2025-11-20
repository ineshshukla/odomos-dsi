"""Document parsing service using docling with fallback parsers
"""
import os
import httpx
import asyncio
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
import PyPDF2
import pdfplumber

from app.models.database import ParsingResult
from app.config import PARSED_DIR, INFORMATION_STRUCTURING_URL, DOCUMENT_INGESTION_URL

# Singleton instance of DocumentConverter to avoid reloading models
_converter_instance = None

def get_converter():
    """Get or create singleton DocumentConverter instance with optimized settings"""
    global _converter_instance
    if _converter_instance is None:
        print("🔧 Initializing DocumentConverter with highly optimized settings...")
        
        # Configure pipeline options for MAXIMUM speed
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Keep OCR for scanned documents
        pipeline_options.do_table_structure = False  # Disable - significant speedup
        pipeline_options.generate_page_images = False  # Disable - saves memory & time
        pipeline_options.generate_picture_images = False  # Disable - saves memory & time
        pipeline_options.images_scale = 1.0  # Don't upscale images
        
        # Create converter with optimized options
        _converter_instance = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )
        print("✅ DocumentConverter ready with maximum optimizations for speed")
    return _converter_instance

class DocumentParsingService:
    """Service for parsing documents using docling"""
    
    def __init__(self, db: Session):
        self.db = db
        self.converter = get_converter()
    
    async def parse_document(self, document_id: str, file_path: str) -> ParsingResult:
        """Parse document using docling with granular progress tracking"""
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
            
            if file_extension == '.txt':
                # For text files, just read the content directly (fast)
                await self.update_parsing_progress(document_id, "processing", 50, "Reading text file...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
                await self.update_parsing_progress(document_id, "processing", 90, "Text extracted")
            else:
                # For other files (PDF, DOCX, images), use multi-tier parsing strategy
                extracted_text = await self._parse_with_fallback(document_id, file_path)
            
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
    
    async def _parse_with_fallback(self, document_id: str, file_path: str) -> str:
        """Multi-tier parsing strategy with fallback parsers for robust handling"""
        import concurrent.futures
        import time
        
        # Strategy 1: Try Docling (most feature-rich, best quality)
        try:
            await self.update_parsing_progress(document_id, "processing", 15, "Trying Docling parser...")
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                await self.update_parsing_progress(document_id, "processing", 30, "Analyzing document structure...")
                result = await loop.run_in_executor(
                    executor,
                    self._convert_document,
                    file_path,
                    document_id
                )
            
            await self.update_parsing_progress(document_id, "processing", 75, "Extracting text content...")
            extracted_text = result.document.export_to_markdown()
            await self.update_parsing_progress(document_id, "processing", 85, "Text extracted successfully")
            
            print(f"   ✅ Docling parsing successful")
            return extracted_text
            
        except Exception as e:
            print(f"   ⚠️  Docling failed: {str(e)[:200]}")
            print(f"   🔄 Falling back to alternative parsers...")
        
        # Strategy 2: Try pdfplumber (good for malformed PDFs, maintains layout)
        try:
            await self.update_parsing_progress(document_id, "processing", 40, "Trying pdfplumber parser...")
            extracted_text = await self._parse_with_pdfplumber(file_path)
            await self.update_parsing_progress(document_id, "processing", 85, "Text extracted with pdfplumber")
            
            if extracted_text and len(extracted_text.strip()) > 100:
                print(f"   ✅ pdfplumber parsing successful ({len(extracted_text)} chars)")
                return extracted_text
            else:
                raise Exception("pdfplumber extracted insufficient text")
                
        except Exception as e:
            print(f"   ⚠️  pdfplumber failed: {str(e)[:100]}")
        
        # Strategy 3: Try PyPDF2 (most permissive, handles broken PDFs)
        try:
            await self.update_parsing_progress(document_id, "processing", 55, "Trying PyPDF2 parser...")
            extracted_text = await self._parse_with_pypdf2(file_path)
            await self.update_parsing_progress(document_id, "processing", 85, "Text extracted with PyPDF2")
            
            if extracted_text and len(extracted_text.strip()) > 50:
                print(f"   ✅ PyPDF2 parsing successful ({len(extracted_text)} chars)")
                return extracted_text
            else:
                raise Exception("PyPDF2 extracted insufficient text")
                
        except Exception as e:
            print(f"   ⚠️  PyPDF2 failed: {str(e)[:100]}")
        
        # All parsers failed
        raise Exception(
            "All parsing strategies failed. The PDF may be severely corrupted, encrypted, or contain only images. "
            "Please ensure the PDF is a valid text-based document."
        )
    
    async def _parse_with_pdfplumber(self, file_path: str) -> str:
        """Parse PDF using pdfplumber (handles layout-heavy PDFs)"""
        import concurrent.futures
        
        def _extract():
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"\n--- Page {page_num} ---\n")
                        text_parts.append(page_text)
            return '\n'.join(text_parts)
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(executor, _extract)
    
    async def _parse_with_pypdf2(self, file_path: str) -> str:
        """Parse PDF using PyPDF2 (most permissive, good for malformed PDFs)"""
        import concurrent.futures
        
        def _extract():
            text_parts = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file, strict=False)  # strict=False for malformed PDFs
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"\n--- Page {page_num} ---\n")
                            text_parts.append(page_text)
                    except Exception as e:
                        print(f"      ⚠️  Page {page_num} extraction failed: {str(e)[:50]}")
                        continue
            return '\n'.join(text_parts)
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(executor, _extract)
    
    def _convert_document(self, file_path: str, document_id: str = None):
        """Synchronous conversion method for executor with progress logging"""
        import time
        start = time.time()
        print(f"   🔄 Converting document...")
        result = self.converter.convert(file_path)
        elapsed = time.time() - start
        print(f"   ⏱️  Docling conversion took {elapsed:.2f}s")
        return result
    
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
