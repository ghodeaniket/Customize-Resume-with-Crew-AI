"""Unit tests for the document processor."""
import pytest
from pathlib import Path

from app.infrastructure.document_processor import DocumentProcessor
from app.core.exceptions import UnsupportedFileTypeError


def test_is_supported_file_type():
    """Test the file type validation."""
    processor = DocumentProcessor()
    
    # Supported file types
    assert processor.is_supported_file_type("resume.pdf") is True
    assert processor.is_supported_file_type("resume.docx") is True
    assert processor.is_supported_file_type("resume.doc") is True
    assert processor.is_supported_file_type("resume.txt") is True
    
    # Unsupported file types
    assert processor.is_supported_file_type("resume.jpg") is False
    assert processor.is_supported_file_type("resume.png") is False
    assert processor.is_supported_file_type("resume.csv") is False


# Additional tests will be implemented in Phase 1
