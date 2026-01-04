import os
import pytest
import asyncio
from io import BytesIO
from fastapi import UploadFile, HTTPException

from app.utils.validators import validate_pdf_header, stream_file_to_disk


class FakeUploadFile:
    """Fake UploadFile for testing."""
    
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content
        self._position = 0
    
    async def read(self, size: int = -1) -> bytes:
        if size == -1:
            result = self._content[self._position:]
            self._position = len(self._content)
        else:
            result = self._content[self._position:self._position + size]
            self._position += size
        return result
    
    async def seek(self, position: int) -> None:
        self._position = position


@pytest.mark.asyncio
async def test_validate_pdf_valid():
    """Valid PDF passes validation."""
    pdf_content = b"%PDF-1.4 some pdf content"
    file = FakeUploadFile("test.pdf", pdf_content)
    
    # Should not raise
    await validate_pdf_header(file)


@pytest.mark.asyncio
async def test_validate_pdf_invalid_extension():
    """Invalid extension is rejected."""
    content = b"%PDF-1.4 some pdf content"
    file = FakeUploadFile("test.exe", content)
    
    with pytest.raises(HTTPException) as exc_info:
        await validate_pdf_header(file)
    
    assert exc_info.value.status_code == 400
    assert "Only PDF files allowed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_pdf_invalid_magic_bytes():
    """File without PDF magic bytes is rejected."""
    content = b"This is not a PDF file"
    file = FakeUploadFile("test.pdf", content)
    
    with pytest.raises(HTTPException) as exc_info:
        await validate_pdf_header(file)
    
    assert exc_info.value.status_code == 400
    assert "magic bytes" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_stream_file_to_disk_success(tmp_path):
    """File is streamed to disk successfully."""
    content = b"%PDF-1.4 test content"
    file = FakeUploadFile("test.pdf", content)
    output_path = str(tmp_path / "test.pdf")
    max_size = 1024 * 1024  # 1MB
    
    result = await stream_file_to_disk(file, output_path, max_size)
    
    assert result["size_bytes"] == len(content)
    assert len(result["sha256"]) == 64  # SHA256 hex length
    assert os.path.exists(output_path)
    
    with open(output_path, "rb") as f:
        assert f.read() == content


@pytest.mark.asyncio
async def test_stream_file_to_disk_too_large(tmp_path):
    """Large file is rejected."""
    content = b"x" * 1000
    file = FakeUploadFile("test.pdf", content)
    output_path = str(tmp_path / "test.pdf")
    max_size = 100  # Very small limit
    
    with pytest.raises(HTTPException) as exc_info:
        await stream_file_to_disk(file, output_path, max_size)
    
    assert exc_info.value.status_code == 413
    assert not os.path.exists(output_path)

