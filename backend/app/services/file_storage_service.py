import uuid
import os
from pathlib import Path
from typing import Dict

from fastapi import UploadFile

from app.config import settings
from app.utils.validators import stream_file_to_disk, ALLOWED_EXCEL_EXTENSIONS


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


async def save_excel_file(file: UploadFile) -> Dict:
    """Save uploaded Excel file to storage and return metadata."""
    file_uuid = uuid.uuid4()
    
    storage_root = settings.TECH_FILE_STORAGE_PATH or settings.FILE_STORAGE_PATH
    storage_path = Path(storage_root)
    storage_path.mkdir(parents=True, exist_ok=True)

    extension = ""
    if file.filename:
        extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_EXCEL_EXTENSIONS:
        extension = ".xlsx"

    output_path = storage_path / f"{file_uuid}{extension}"

    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    metadata = await stream_file_to_disk(file, str(output_path), max_size_bytes)

    return {
        "uuid": file_uuid,
        "sha256": metadata["sha256"],
        "size_bytes": metadata["size_bytes"],
        "extension": extension,
    }


def get_excel_file_path(storage_uuid: uuid.UUID, extension: str) -> Path:
    """Get Excel file path for a storage UUID and extension."""
    normalized_extension = extension if extension.startswith(".") else f".{extension}"
    storage_root = settings.TECH_FILE_STORAGE_PATH or settings.FILE_STORAGE_PATH
    return Path(storage_root) / f"{storage_uuid}{normalized_extension}"


def get_candidate_paths(storage_uuid: uuid.UUID, extension: str, kind: str = "tech") -> list[Path]:
    """Return candidate file paths across active and legacy storage roots."""
    normalized_extension = extension if extension.startswith(".") else f".{extension}"

    if kind == "tech":
        primary_root = settings.TECH_FILE_STORAGE_PATH or settings.FILE_STORAGE_PATH
        roots: list[str] = [primary_root]
        if settings.TECH_FILE_STORAGE_PATH and settings.FILE_STORAGE_PATH:
            if settings.TECH_FILE_STORAGE_PATH != settings.FILE_STORAGE_PATH:
                roots.append(settings.FILE_STORAGE_PATH)
    else:
        roots = [settings.FILE_STORAGE_PATH]

    seen = set()
    paths: list[Path] = []
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        paths.append(Path(root) / f"{storage_uuid}{normalized_extension}")

    return paths


def delete_excel_file(storage_uuid: uuid.UUID, extension: str) -> bool:
    """Delete Excel file from storage."""
    path = get_excel_file_path(storage_uuid, extension)
    if path.exists():
        os.remove(path)
        return True
    return False

