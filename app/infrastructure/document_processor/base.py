"""Base abstract class for document extractors."""
import abc
import re
from typing import Optional, Dict, Any

from app.core.logging import logger


class BaseDocumentExtractor(abc.ABC):
    """Abstract base class defining the document extraction interface."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize document extractor.
        
        Args:
            cache_enabled: Whether to enable caching for this extractor
        """
        self.cache_enabled = cache_enabled
    
    @property
    def mime_types(self) -> list[str]:
        """Get list of MIME types supported by this extractor.
        
        Returns:
            list[str]: List of supported MIME types
        """
        return []
        
    @property
    def supported_extensions(self) -> list[str]:
        """Get list of file extensions supported by this extractor.
        
        Returns:
            list[str]: List of supported file extensions
        """
        return []
    
    @abc.abstractmethod
    async def extract_text(self, content: bytes, filename: Optional[str] = None) -> str:
        """Extract text from document content.
        
        Args:
            content: Document content as bytes
            filename: Optional original filename
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        pass
    
    def can_handle(self, mime_type: str, filename: Optional[str] = None) -> bool:
        """Check if this extractor can handle a given document type.
        
        Args:
            mime_type: Document MIME type
            filename: Optional original filename for extension checking
            
        Returns:
            bool: True if this extractor can handle the document type
        """
        # Check if mime_type is directly supported
        if mime_type in self.mime_types:
            return True
        
        # If a filename is provided, check the extension
        if filename:
            extension = self._get_extension(filename)
            return extension in self.supported_extensions
        
        return False
    
    def _get_extension(self, filename: str) -> str:
        """Get lowercase extension from filename including the dot.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Lowercase extension including the dot
        """
        if not filename:
            return ""
        
        parts = filename.split(".")
        if len(parts) > 1:
            return f".{parts[-1].lower()}"
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace but preserve paragraphs
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        
        # Remove empty lines but preserve paragraph structure
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def get_cache_key(self, content: bytes) -> str:
        """Get cache key for document content.
        
        Args:
            content: Document content
            
        Returns:
            str: Cache key
        """
        import hashlib
        
        # Create a hash of the content to use as cache key
        content_hash = hashlib.md5(content).hexdigest()
        
        # Include class name to differentiate extractors
        return f"{self.__class__.__name__}_{content_hash}"
    
    def get_extraction_metadata(self, content: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        """Get metadata about the extraction process.
        
        Args:
            content: Document content
            filename: Optional original filename
            
        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        return {
            "extractor": self.__class__.__name__,
            "content_size": len(content),
            "filename": filename,
            "extension": self._get_extension(filename) if filename else None,
            "cache_enabled": self.cache_enabled,
        }
    
    def log_extraction_start(self, content: bytes, filename: Optional[str] = None) -> None:
        """Log extraction start with metadata.
        
        Args:
            content: Document content
            filename: Optional original filename
        """
        metadata = self.get_extraction_metadata(content, filename)
        logger.info(
            f"Starting extraction with {self.__class__.__name__}, "
            f"size: {len(content)} bytes",
            extra={
                **metadata,
                "task": "document_extraction",
                "action": "start"
            }
        )
    
    def log_extraction_success(self, content: bytes, result: str, elapsed_ms: float, 
                              filename: Optional[str] = None) -> None:
        """Log extraction success with metadata.
        
        Args:
            content: Document content
            result: Extracted text
            elapsed_ms: Elapsed time in milliseconds
            filename: Optional original filename
        """
        metadata = self.get_extraction_metadata(content, filename)
        logger.info(
            f"Extraction successful with {self.__class__.__name__}, "
            f"extracted {len(result)} characters in {elapsed_ms:.2f}ms",
            extra={
                **metadata,
                "extracted_chars": len(result),
                "processing_time_ms": elapsed_ms,
                "status": "success",
                "task": "document_extraction",
                "action": "complete"
            }
        )
        
        # Log sample of extracted text for verification
        sample = result[:200] + "..." if len(result) > 200 else result
        logger.debug(f"Extracted text sample: {sample}")
    
    def log_extraction_error(self, content: bytes, error: Exception, elapsed_ms: float,
                            filename: Optional[str] = None) -> None:
        """Log extraction error with metadata.
        
        Args:
            content: Document content
            error: Exception that occurred
            elapsed_ms: Elapsed time in milliseconds
            filename: Optional original filename
        """
        metadata = self.get_extraction_metadata(content, filename)
        logger.error(
            f"Extraction failed with {self.__class__.__name__}: {str(error)}",
            exc_info=True,
            extra={
                **metadata,
                "error": str(error),
                "error_type": error.__class__.__name__,
                "processing_time_ms": elapsed_ms,
                "status": "failed",
                "task": "document_extraction",
                "action": "error"
            }
        )
