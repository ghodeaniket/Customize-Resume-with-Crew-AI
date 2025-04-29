"""Unit tests for the document processor."""
import pytest
import asyncio
from pathlib import Path
import io

from app.infrastructure.document_processor import DocumentProcessor
from app.core.exceptions import DocumentProcessingError
from app.core.utils.file_detection import (
    is_supported_file_type, detect_file_type, 
    PDF_MIME_TYPE, DOCX_MIME_TYPE, TEXT_MIME_TYPE
)


def test_supported_file_type():
    """Test the file type validation using utility function."""
    # Supported file types
    assert is_supported_file_type("resume.pdf") is True
    assert is_supported_file_type("resume.docx") is True
    assert is_supported_file_type("resume.doc") is True
    assert is_supported_file_type("resume.txt") is True
    
    # Unsupported file types
    assert is_supported_file_type("resume.jpg") is False
    assert is_supported_file_type("resume.png") is False
    assert is_supported_file_type("resume.csv") is False
    assert is_supported_file_type("") is False
    assert is_supported_file_type(None) is False


def test_detect_file_type(sample_pdf_content, sample_docx_content, sample_txt_content):
    """Test the file type detection."""
    # Test PDF detection
    assert detect_file_type(sample_pdf_content, "test.pdf") == PDF_MIME_TYPE
    assert detect_file_type(sample_pdf_content) == PDF_MIME_TYPE  # Without filename
    
    # Test DOCX detection
    assert detect_file_type(sample_docx_content, "test.docx") == DOCX_MIME_TYPE
    
    # Test TXT detection
    assert detect_file_type(sample_txt_content, "test.txt") == TEXT_MIME_TYPE


@pytest.mark.asyncio
async def test_extract_text_from_bytes_pdf(document_processor, sample_pdf_content):
    """Test extracting text from PDF bytes."""
    text = await document_processor.extract_text_from_bytes(
        sample_pdf_content, filename="test.pdf"
    )
    
    # Basic validation
    assert text is not None
    assert isinstance(text, str)
    assert len(text) > 0
    
    # Content validation
    assert "Test Resume" in text or "Software Engineer" in text


@pytest.mark.asyncio
async def test_extract_text_from_bytes_docx(document_processor, sample_docx_content):
    """Test extracting text from DOCX bytes."""
    text = await document_processor.extract_text_from_bytes(
        sample_docx_content, filename="test.docx"
    )
    
    # Basic validation
    assert text is not None
    assert isinstance(text, str)
    assert len(text) > 0
    
    # Content validation
    assert "Test Resume" in text or "Software Engineer" in text


@pytest.mark.asyncio
async def test_extract_text_from_bytes_txt(document_processor, sample_txt_content):
    """Test extracting text from TXT bytes."""
    text = await document_processor.extract_text_from_bytes(
        sample_txt_content, filename="test.txt"
    )
    
    # Basic validation
    assert text is not None
    assert isinstance(text, str)
    assert len(text) > 0
    
    # Content validation
    assert "Test Resume" in text
    assert "Software Engineer" in text
    assert "Skills" in text
    assert "Python" in text


@pytest.mark.asyncio
async def test_extract_text_from_empty_content(document_processor):
    """Test extracting text from empty content."""
    with pytest.raises(DocumentProcessingError):
        await document_processor.extract_text_from_bytes(b"", filename="empty.txt")


@pytest.mark.asyncio
async def test_extract_text_from_unsupported_type(document_processor):
    """Test extracting text from unsupported file type."""
    with pytest.raises(DocumentProcessingError):
        await document_processor.extract_text_from_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", filename="image.png"
        )


@pytest.mark.asyncio
async def test_caching_behavior(document_processor, sample_txt_content):
    """Test that caching works correctly."""
    # Enable caching
    document_processor.cache_enabled = True
    
    # First call should not use cache
    text1 = await document_processor.extract_text_from_bytes(
        sample_txt_content, filename="test.txt"
    )
    
    # Second call should use cache
    text2 = await document_processor.extract_text_from_bytes(
        sample_txt_content, filename="test.txt"
    )
    
    # Results should be identical
    assert text1 == text2
    
    # Disable caching
    document_processor.cache_enabled = False
    
    # Call should not use cache
    text3 = await document_processor.extract_text_from_bytes(
        sample_txt_content, filename="test.txt"
    )
    
    # Results should still be identical
    assert text1 == text3


@pytest.mark.asyncio
async def test_text_cleaning(document_processor):
    """Test the text cleaning functionality."""
    dirty_text = "This  has  extra  spaces\n\n\n\nAnd extra newlines\r\nAnd Windows line endings"
    
    cleaned_text = document_processor._clean_text(dirty_text)
    
    # Check that extra spaces are removed
    assert "This has extra spaces" in cleaned_text
    
    # Check that excessive newlines are normalized
    assert "\n\n" in cleaned_text  # Preserve paragraph breaks
    assert "\n\n\n" not in cleaned_text  # But not excessive breaks
    
    # Check that Windows line endings are normalized
    assert "\r\n" not in cleaned_text
