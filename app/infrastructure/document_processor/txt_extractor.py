"""Text document extraction implementation."""
import time
import asyncio
from typing import Optional, List, Dict, Any

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.core.utils.file_detection import TEXT_MIME_TYPE
from app.infrastructure.document_processor.base import BaseDocumentExtractor


class TXTExtractor(BaseDocumentExtractor):
    """Plain text document extractor implementation."""
    
    def __init__(self, cache_enabled: bool = True, fallback_encoding: bool = True):
        """Initialize text extractor.
        
        Args:
            cache_enabled: Whether to enable caching
            fallback_encoding: Whether to try fallback encoding on failure
        """
        super().__init__(cache_enabled=cache_enabled)
        self.fallback_encoding = fallback_encoding
    
    @property
    def mime_types(self) -> list[str]:
        """Get list of MIME types supported by this extractor.
        
        Returns:
            list[str]: List of supported MIME types
        """
        return [TEXT_MIME_TYPE, "application/rtf", "text/csv", "text/html", "text/xml"]
    
    @property
    def supported_extensions(self) -> list[str]:
        """Get list of file extensions supported by this extractor.
        
        Returns:
            list[str]: List of supported file extensions
        """
        return [".txt", ".rtf", ".csv", ".html", ".htm", ".xml"]
    
    async def extract_text(self, content: bytes, filename: Optional[str] = None) -> str:
        """Extract text from plain text content.
        
        Args:
            content: Text content as bytes
            filename: Optional original filename
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        start_time = time.time()
        self.log_extraction_start(content, filename)
        
        try:
            # Run CPU-bound operation in thread pool
            result = await asyncio.to_thread(self._extract_text_sync, content)
            
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
                raise DocumentProcessingError(detail=f"Text extraction failed: {str(e)}")
    
    def _extract_text_sync(self, content: bytes) -> str:
        """Synchronous implementation of text extraction.
        
        Args:
            content: Text content
            
        Returns:
            str: Decoded text
            
        Raises:
            DocumentProcessingError: If extraction fails completely
        """
        # Try UTF-8 first
        try:
            text = content.decode('utf-8')
            logger.debug(f"Successfully decoded text with UTF-8 encoding")
            return self._clean_text(text)
        except UnicodeDecodeError as e:
            logger.warning(f"Failed to decode as UTF-8: {str(e)}")
            
            # Only try fallback if enabled
            if not self.fallback_encoding:
                raise DocumentProcessingError(
                    detail="Failed to decode text with UTF-8 encoding and fallback is disabled"
                )
            
            # Try with error replacement
            try:
                text = content.decode('utf-8', errors='replace')
                logger.warning("Decoded text with UTF-8 replacement; some characters may be incorrect")
                return self._clean_text(text)
            except Exception as fallback_error:
                logger.error(f"Failed to decode even with replacement: {str(fallback_error)}")
                raise DocumentProcessingError(
                    detail="Failed to decode text content with all available methods"
                )
        except Exception as e:
            logger.error(f"Unexpected error decoding text: {str(e)}")
            raise DocumentProcessingError(detail=f"Error extracting text: {str(e)}")
