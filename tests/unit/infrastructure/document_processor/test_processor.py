"""Tests for the DocumentProcessor class."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.core.exceptions import DocumentProcessingError
from app.infrastructure.document_processor.processor import DocumentProcessor


class TestDocumentProcessor:
    """Test cases for DocumentProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create document processor for testing."""
        return DocumentProcessor(cache_enabled=False)
    
    @pytest.fixture
    def pdf_content(self):
        """Sample PDF content."""
        return b"%PDF-1.5\nsome pdf content"
    
    @pytest.fixture
    def docx_content(self):
        """Sample DOCX content."""
        return b"PK\x03\x04some docx content"
    
    @pytest.fixture
    def txt_content(self):
        """Sample text content."""
        return b"This is a plain text document."
    
    @pytest.mark.asyncio
    async def test_extract_empty_content(self, processor):
        """Test extraction with empty content."""
        with pytest.raises(DocumentProcessingError, match="Empty file content"):
            await processor.extract_text_from_bytes(b"")
    
    @pytest.mark.asyncio
    @patch("app.infrastructure.document_processor.factory.PDFExtractor.extract_text")
    async def test_extract_pdf(self, mock_extract, processor, pdf_content):
        """Test PDF extraction."""
        mock_extract.return_value = "Extracted PDF content"
        
        result = await processor.extract_text_from_bytes(pdf_content, "application/pdf")
        
        assert result == "Extracted PDF content"
        mock_extract.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.infrastructure.document_processor.factory.DOCXExtractor.extract_text")
    async def test_extract_docx(self, mock_extract, processor, docx_content):
        """Test DOCX extraction."""
        mock_extract.return_value = "Extracted DOCX content"
        
        result = await processor.extract_text_from_bytes(
            docx_content, 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        assert result == "Extracted DOCX content"
        mock_extract.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.infrastructure.document_processor.factory.TXTExtractor.extract_text")
    async def test_extract_txt(self, mock_extract, processor, txt_content):
        """Test text extraction."""
        mock_extract.return_value = "Extracted text content"
        
        result = await processor.extract_text_from_bytes(txt_content, "text/plain")
        
        assert result == "Extracted text content"
        mock_extract.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_unsupported_type(self, processor):
        """Test extraction with unsupported type."""
        with pytest.raises(DocumentProcessingError):
            await processor.extract_text_from_bytes(b"some data", "image/jpeg")
    
    @pytest.mark.asyncio
    @patch("app.infrastructure.document_processor.factory.PDFExtractor.extract_text")
    async def test_extract_with_error(self, mock_extract, processor, pdf_content):
        """Test extraction with error."""
        mock_extract.side_effect = Exception("Test error")
        
        with pytest.raises(DocumentProcessingError, match="Test error"):
            await processor.extract_text_from_bytes(pdf_content, "application/pdf")
    
    def test_is_supported_file_type(self, processor):
        """Test checking if a file type is supported."""
        assert processor.is_supported_file_type("test.pdf")
        assert processor.is_supported_file_type("test.docx")
        assert processor.is_supported_file_type("test.txt")
        assert not processor.is_supported_file_type("test.jpg")
        assert not processor.is_supported_file_type("")
