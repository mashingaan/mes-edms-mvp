import uuid
import os
from pathlib import Path
from typing import Dict

from fastapi import UploadFile

from app.config import settings
from app.utils.validators import stream_file_to_disk


async def save_file(file: UploadFile) -> Dict:
    """Save uploaded file to storage and return metadata."""
    # Generate UUID for storage filename
    file_uuid = uuid.uuid4()
    
    # Ensure storage directory exists
    storage_path = Path(settings.FILE_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Build output path
    output_path = storage_path / f"{file_uuid}.pdf"
    
    # Calculate max size in bytes
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Stream to disk and get metadata
    metadata = await stream_file_to_disk(file, str(output_path), max_size_bytes)
    
    return {
        "uuid": file_uuid,
        "sha256": metadata["sha256"],
        "size_bytes": metadata["size_bytes"],
    }


def get_file_path(storage_uuid: uuid.UUID) -> Path:
    """Get file path for a storage UUID."""
    return Path(settings.FILE_STORAGE_PATH) / f"{storage_uuid}.pdf"


def delete_file(storage_uuid: uuid.UUID) -> bool:
    """Delete file from storage."""
    path = get_file_path(storage_uuid)
    if path.exists():
        os.remove(path)
        return True
    return False

