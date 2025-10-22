"""
Storage utilities for file handling
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple
from app.config import UPLOADS_DIR, TEMP_DIR

def generate_file_path(filename: str) -> Tuple[Path, str]:
    """
    Generate a unique file path for storage
    Returns: (full_path, unique_filename)
    """
    # Create date-based directory structure
    now = datetime.now()
    date_dir = UPLOADS_DIR / now.strftime("%Y/%m/%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(filename).suffix
    unique_id = str(uuid.uuid4())
    unique_filename = f"{unique_id}{file_extension}"
    
    # Full path
    full_path = date_dir / unique_filename
    
    return full_path, unique_filename

def save_uploaded_file(file_content: bytes, file_path: Path) -> None:
    """Save uploaded file to storage"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(file_content)

def get_file_info(file_path: Path) -> dict:
    """Get file information"""
    stat = file_path.stat()
    return {
        "size": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_ctime),
        "modified_at": datetime.fromtimestamp(stat.st_mtime)
    }

def delete_file(file_path: Path) -> bool:
    """Delete file from storage"""
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False

def cleanup_temp_files() -> int:
    """Clean up temporary files older than 1 hour"""
    import time
    current_time = time.time()
    cleaned_count = 0
    
    for temp_file in TEMP_DIR.iterdir():
        if temp_file.is_file():
            file_age = current_time - temp_file.stat().st_mtime
            if file_age > 3600:  # 1 hour
                try:
                    temp_file.unlink()
                    cleaned_count += 1
                except Exception:
                    pass
    
    return cleaned_count
