"""Base PDF extractor with common functionality."""
import time
from typing import Optional, List

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.core.utils.file_detection import PDF_MIME_TYPE
from app.infrastructure.document_processor.base import BaseDocumentExtractor


class BasePDFExtractor(BaseDocumentExtractor):
    """Base PDF extractor with common PDF functionality."""
    
    @property
    def mime_types(self) -> list[str]:
        """Get list of MIME types supported by this extractor.
        
        Returns:
            list[str]: List of supported MIME types
        """
        return [PDF_MIME_TYPE]
    
    @property
    def supported_extensions(self) -> list[str]:
        """Get list of file extensions supported by this extractor.
        
        Returns:
            list[str]: List of supported file extensions
        """
        return [".pdf"]
    
    def _clean_text_result(self, text: str) -> str:
        """Clean and validate extracted text result.
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return "[Document contains no extractable text]"
        
        cleaned = self._clean_text(text)
        if not cleaned.strip():
            return "[Document contains no extractable text]"
        
        return cleaned
    
    def _log_extraction_metrics(
        self, 
        content_length: int,
        total_pages: int,
        successful_pages: int,
        failed_pages: List[int],
        elapsed_ms: float
    ) -> None:
        """Log extraction metrics for debugging.
        
        Args:
            content_length: Length of the PDF content
            total_pages: Total number of pages
            successful_pages: Number of successfully extracted pages
            failed_pages: List of page numbers that failed
            elapsed_ms: Total extraction time in milliseconds
        """
        success_rate = successful_pages / total_pages if total_pages > 0 else 0
        
        if success_rate == 1.0:
            logger.info(
                f"PDF extraction complete: {total_pages} pages extracted successfully, "
                f"{elapsed_ms:.2f}ms"
            )
        else:
            failed_pages_str = ", ".join(map(str, failed_pages))
            logger.warning(
                f"Partial PDF extraction: {successful_pages}/{total_pages} pages extracted. "
                f"Failed pages: {failed_pages_str}. Total time: {elapsed_ms:.2f}ms"
            )
    
    def _create_extraction_error(self, method_name: str, error: Exception) -> DocumentProcessingError:
        """Create a standardized extraction error.
        
        Args:
            method_name: Name of the extraction method that failed
            error: The original exception
            
        Returns:
            DocumentProcessingError: Standardized error
        """
        error_msg = str(error).lower()
        
        # Check for common error patterns
        if "password" in error_msg or "encrypted" in error_msg:
            return DocumentProcessingError(
                detail=f"PDF is encrypted and cannot be processed with {method_name}. "
                       "Please remove the password and try again."
            )
        elif "corrupted" in error_msg or "eof marker not found" in error_msg:
            return DocumentProcessingError(
                detail=f"PDF file is incomplete or corrupted. {method_name} extraction failed."
            )
        else:
            return DocumentProcessingError(
                detail=f"{method_name} PDF extraction failed: {str(error)}"
            )
