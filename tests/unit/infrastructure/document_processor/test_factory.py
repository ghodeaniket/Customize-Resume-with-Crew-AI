"""Tests for the DocumentExtractorFactory class."""
import pytest
from unittest.mock import patch, MagicMock

from app.core.exceptions import UnsupportedFileTypeError
from app.core.utils.file_detection import PDF_MIME_TYPE, DOCX_MIME_TYPE, TEXT_MIME_TYPE
from app.infrastructure.document_processor.factory import DocumentExtractorFactory
from app.infrastructure.document_processor.pdf_extractor import PDFExtractor
from app.infrastructure.document_processor.docx_extractor import DOCXExtractor
from app.infrastructure.document_processor.txt_extractor import TXTExtractor


class TestDocumentExtractorFactory:
    """Test cases for DocumentExtractorFactory."""
    
    def test_create_pdf_extractor(self):
        """Test creating PDF extractor."""
        factory = DocumentExtractorFactory()
        extractor = factory.create_extractor(PDF_MIME_TYPE)
        
        assert isinstance(extractor, PDFExtractor)
    
    def test_create_docx_extractor(self):
        """Test creating DOCX extractor."""
        factory = DocumentExtractorFactory()
        extractor = factory.create_extractor(DOCX_MIME_TYPE)
        
        assert isinstance(extractor, DOCXExtractor)
    
    def test_create_txt_extractor(self):
        """Test creating TXT extractor."""
        factory = DocumentExtractorFactory()
        extractor = factory.create_extractor(TEXT_MIME_TYPE)
        
        assert isinstance(extractor, TXTExtractor)
    
    def test_create_extractor_by_filename(self):
        """Test creating extractor by filename."""
        factory = DocumentExtractorFactory()
        
        # PDF by filename
        extractor = factory.create_extractor("application/octet-stream", "test.pdf")
        assert isinstance(extractor, PDFExtractor)
        
        # DOCX by filename
        extractor = factory.create_extractor("application/octet-stream", "test.docx")
        assert isinstance(extractor, DOCXExtractor)
        
        # TXT by filename
        extractor = factory.create_extractor("application/octet-stream", "test.txt")
        assert isinstance(extractor, TXTExtractor)
    
    def test_unsupported_file_type(self):
        """Test unsupported file type."""
        factory = DocumentExtractorFactory()
        
        with pytest.raises(UnsupportedFileTypeError):
            factory.create_extractor("image/jpeg")
    
    def test_get_supported_mime_types(self):
        """Test getting supported MIME types."""
        factory = DocumentExtractorFactory()
        mime_types = factory.get_supported_mime_types()
        
        assert PDF_MIME_TYPE in mime_types
        assert DOCX_MIME_TYPE in mime_types
        assert TEXT_MIME_TYPE in mime_types
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        factory = DocumentExtractorFactory()
        extensions = factory.get_supported_extensions()
        
        assert ".pdf" in extensions
        assert ".docx" in extensions
        assert ".txt" in extensions
    
    def test_is_supported_file_type(self):
        """Test checking if a file type is supported."""
        factory = DocumentExtractorFactory()
        
        assert factory.is_supported_file_type("test.pdf")
        assert factory.is_supported_file_type("test.docx")
        assert factory.is_supported_file_type("test.txt")
        assert not factory.is_supported_file_type("test.jpg")
        assert not factory.is_supported_file_type("")
