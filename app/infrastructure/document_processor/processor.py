"""Main document processor implementation."""
import time
from typing import Optional
import asyncio

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.core.utils.file_detection import detect_file_type, get_detailed_file_info
from app.infrastructure.document_processor.factory import DocumentExtractorFactory
from app.infrastructure.document_processor.cache import InMemoryDocumentCache


class DocumentProcessor:
    """Main document processor implementing backward compatibility layer."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize document processor.
        
        Args:
            cache_enabled: Whether to cache extraction results
        """
        self.cache_enabled = cache_enabled
        self.cache = InMemoryDocumentCache()
        self.factory = DocumentExtractorFactory(cache_enabled=cache_enabled)
    
    async def extract_text_from_bytes(
        self, 
        file_content: bytes, 
        file_type: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """Extract text from various file formats.
        
        Args:
            file_content: Raw file content bytes
            file_type: MIME type of the file (optional)
            filename: Original filename (optional)
            
        Returns:
            str: Extracted text content
            
        Raises:
            DocumentProcessingError: If file type is unsupported or extraction fails
        """
        start_time = time.time()
        
        # Validate file content
        if not file_content or len(file_content) == 0:
            logger.error("Empty file content")
            raise DocumentProcessingError(detail="Empty file content")
        
        # Log initial file info
        file_size = len(file_content)
        logger.info(f"Starting document extraction, size: {file_size} bytes", extra={
            "file_size": file_size,
            "has_filename": bool(filename),
            "task": "document_extraction"
        })
        
        # Get detailed file information for better diagnostics
        file_info = get_detailed_file_info(file_content, filename)
        actual_file_type = file_type or file_info["detected_type"]
        
        logger.info(f"Detected file type: {actual_file_type}, size: {file_size} bytes", extra={
            "file_type": actual_file_type,
            "file_size": file_size,
            "task": "document_extraction"
        })
        
        try:
            # Get appropriate extractor for the file type
            extractor = self.factory.create_extractor(actual_file_type, filename)
            
            # Extract text
            result = await extractor.extract_text(file_content, filename)
            
            # Log extraction success
            total_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Total extraction time: {total_time_ms:.2f}ms", extra={
                "processing_time_ms": total_time_ms,
                "task": "document_extraction"
            })
            
            return result
                
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Error extracting text from document: {str(e)}", 
                exc_info=True,
                extra={
                    "error": str(e),
                    "file_type": actual_file_type,
                    "status": "failed",
                    "task": "document_extraction",
                    "processing_time_ms": total_time_ms
                }
            )
            
            # Re-raise as DocumentProcessingError if it's not already
            if isinstance(e, DocumentProcessingError):
                raise
            else:
                raise DocumentProcessingError(
                    detail=f"Error extracting text from document: {str(e)}"
                )
    
    def is_supported_file_type(self, filename: str) -> bool:
        """Check if a file type is supported based on extension.
        
        Args:
            filename: Filename to check
            
        Returns:
            bool: True if the file type is supported, False otherwise
        """
        return self.factory.is_supported_file_type(filename)
