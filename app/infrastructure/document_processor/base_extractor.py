"""Base abstract class for document extractors."""
import abc
import re
from typing import Optional, Dict, Any

from app.core.logging import logger
from app.infrastructure.document_processor.base_extractor_logging import BaseExtractorLogging


class BaseDocumentExtractor(abc.ABC):
    """Abstract base class defining the document extraction interface."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize document extractor.
        
        Args:
            cache_enabled: Whether to enable caching for this extractor
        """
        self.cache_enabled = cache_enabled
        self._logger = BaseExtractorLogging()
    
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
        """Log extraction start with metadata."""
        metadata = self.get_extraction_metadata(content, filename)
        self._logger.log_extraction_start(self.__class__.__name__, content, metadata)
    
    def log_extraction_success(self, content: bytes, result: str, elapsed_ms: float, 
                              filename: Optional[str] = None) -> None:
        """Log extraction success with metadata."""
        metadata = self.get_extraction_metadata(content, filename)
        self._logger.log_extraction_success(self.__class__.__name__, result, elapsed_ms, metadata)
    
    def log_extraction_error(self, content: bytes, error: Exception, elapsed_ms: float,
                            filename: Optional[str] = None) -> None:
        """Log extraction error with metadata."""
        metadata = self.get_extraction_metadata(content, filename)
        self._logger.log_extraction_error(self.__class__.__name__, error, elapsed_ms, metadata)
