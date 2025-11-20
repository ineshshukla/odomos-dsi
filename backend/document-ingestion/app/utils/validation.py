"""
File validation utilities
"""
try:
    import magic
    MAGIC_AVAILABLE = True
except (ImportError, OSError):
    MAGIC_AVAILABLE = False
    
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
from app.config import MAX_FILE_SIZE, MAX_ZIP_SIZE, ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES

def validate_file_size(file: UploadFile) -> None:
    """Validate file size"""
    # Auto-detect if it's a ZIP file for size validation
    is_zip = file.filename and file.filename.lower().endswith('.zip')
    max_size = MAX_ZIP_SIZE if is_zip else MAX_FILE_SIZE
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size allowed: {max_size / (1024*1024):.1f}MB"
        )

def validate_file_extension(filename: str) -> None:
    """Validate file extension"""
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

def validate_file_content(file: UploadFile) -> Tuple[str, str]:
    """Validate file content using magic numbers (if available)"""
    # Read first 1024 bytes for magic number detection
    content = file.file.read(1024)
    file.file.seek(0)  # Reset file pointer
    
    if MAGIC_AVAILABLE:
        # Detect MIME type using libmagic
        mime_type = magic.from_buffer(content, mime=True)
        
        # Special handling for ZIP files which might be detected as generic binary or other types
        is_zip = file.filename and file.filename.lower().strip().endswith('.zip')
        if is_zip and (mime_type == 'application/octet-stream' or mime_type not in ALLOWED_MIME_TYPES):
             # Check for ZIP file signature (PK\x03\x04 or PK\x05\x06)
             if content[:4] in (b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'):
                 mime_type = "application/zip"
        
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File content not allowed. Detected type: {mime_type}"
            )
    else:
        # Fall back to checking file extension
        mime_type = "application/octet-stream"  # Generic binary
        if file.filename:
            if file.filename.lower().endswith('.pdf'):
                mime_type = "application/pdf"
            elif file.filename.lower().endswith(('.jpg', '.jpeg')):
                mime_type = "image/jpeg"
            elif file.filename.lower().endswith('.png'):
                mime_type = "image/png"
            elif file.filename.lower().endswith('.zip'):
                mime_type = "application/zip"
    
    return mime_type, content

def validate_upload_file(file: UploadFile) -> Tuple[str, str]:
    """
    Comprehensive file validation
    Returns: (mime_type, content_preview)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate file size
    validate_file_size(file)
    
    # Validate file extension
    validate_file_extension(file.filename)
    
    # Validate file content
    mime_type, content_preview = validate_file_content(file)
    
    return mime_type, content_preview

def get_file_size(file: UploadFile) -> int:
    """Get file size in bytes"""
    if file.size:
        return file.size
    
    # If size is not available, read the file to get size
    current_pos = file.file.tell()
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(current_pos)  # Reset position
    return size
