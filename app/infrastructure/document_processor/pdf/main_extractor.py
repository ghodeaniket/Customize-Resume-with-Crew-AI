"""Main PDF extractor with fallback mechanism."""
import time
from typing import Optional, List

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.infrastructure.document_processor.pdf.base_pdf_extractor import BasePDFExtractor
from app.infrastructure.document_processor.pdf.pypdf2_extractor import PyPDF2Extractor
from app.infrastructure.document_processor.pdf.pymupdf_extractor import PyMuPDFExtractor, lazy_import_pymupdf


class PDFExtractor(BasePDFExtractor):
    """Main PDF extractor with fallback mechanism."""
    
    def __init__(self, cache_enabled: bool = True, use_pymupdf_first: bool = True):
        """Initialize PDF extractor.
        
        Args:
            cache_enabled: Whether to enable caching
            use_pymupdf_first: Whether to try PyMuPDF before PyPDF2
        """
        super().__init__(cache_enabled=cache_enabled)
        self.use_pymupdf_first = use_pymupdf_first
        self.pypdf2_extractor = PyPDF2Extractor(cache_enabled=cache_enabled)
        self.pymupdf_extractor = PyMuPDFExtractor(cache_enabled=cache_enabled)
    
    async def extract_text(self, content: bytes, filename: Optional[str] = None) -> str:
        """Extract text from PDF content.
        
        Args:
            content: PDF content as bytes
            filename: Optional original filename
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        start_time = time.time()
        self.log_extraction_start(content, filename)
        
        try:
            result = await self._extract_with_fallback(content)
            
            # Log extraction success
            elapsed_ms = (time.time() - start_time) * 1000
            self.log_extraction_success(content, result, elapsed_ms, filename)
            
            return result
        except Exception as e:
            # Log extraction error
            elapsed_ms = (time.time() - start_time) * 1000
            self.log_extraction_error(content, e, elapsed_ms, filename)
            
            # Re-raise as DocumentProcessingError
            if isinstance(e, DocumentProcessingError):
                raise
            else:
                raise DocumentProcessingError(detail=f"PDF extraction failed: {str(e)}")
    
    async def _extract_with_fallback(self, content: bytes) -> str:
        """Extract text from PDF with fallback mechanism.
        
        Args:
            content: PDF content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If all extraction methods fail
        """
        errors = []
        
        # Order of extraction methods
        if self.use_pymupdf_first and lazy_import_pymupdf():
            extractors = [
                ("PyMuPDF", self.pymupdf_extractor),
                ("PyPDF2", self.pypdf2_extractor)
            ]
        else:
            extractors = [
                ("PyPDF2", self.pypdf2_extractor)
            ]
            # Only add PyMuPDF if available
            if lazy_import_pymupdf():
                extractors.append(("PyMuPDF", self.pymupdf_extractor))
        
        # Try each extractor in order
        for name, extractor in extractors:
            try:
                logger.info(f"Attempting PDF extraction with {name}")
                result = await extractor.extract_text(content)
                if result and result.strip():
                    return result
                else:
                    logger.warning(f"{name} extraction produced empty result, trying next method")
                    errors.append(f"{name} extraction produced empty result")
            except Exception as e:
                logger.warning(f"{name} extraction failed: {str(e)}")
                errors.append(f"{name} error: {str(e)}")
        
        # All extraction methods failed or produced empty results
        error_msg = "All PDF extraction methods failed: " + "; ".join(errors)
        logger.error(error_msg)
        
        # If we have any empty results, return placeholder rather than failing
        if "empty result" in " ".join(errors):
            return "[Document contains no extractable text]"
        
        # Otherwise, raise exception
        raise DocumentProcessingError(detail=error_msg)
