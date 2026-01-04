import os
import hashlib

from fastapi import UploadFile, HTTPException, status

ALLOWED_EXTENSIONS = {".pdf"}
PDF_MAGIC_BYTES = b"%PDF-"


async def validate_pdf_header(file: UploadFile) -> None:
    """Validate PDF without loading entire file into RAM."""
    # 1. Extension check
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files allowed"
            )
    
    # 2. Read first 5 bytes only (magic bytes check)
    chunk = await file.read(5)
    await file.seek(0)  # Reset for later streaming
    
    if not chunk.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file (magic bytes check failed)"
        )


async def stream_file_to_disk(
    file: UploadFile,
    output_path: str,
    max_size_bytes: int
) -> dict:
    """Stream file to disk, calculate SHA256, return metadata."""
    sha256_hash = hashlib.sha256()
    bytes_written = 0
    chunk_size = 8192  # 8KB chunks
    
    try:
        with open(output_path, 'wb') as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                
                bytes_written += len(chunk)
                if bytes_written > max_size_bytes:
                    os.remove(output_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum size of {max_size_bytes // (1024 * 1024)}MB"
                    )
                
                sha256_hash.update(chunk)
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    return {
        "sha256": sha256_hash.hexdigest(),
        "size_bytes": bytes_written
    }

