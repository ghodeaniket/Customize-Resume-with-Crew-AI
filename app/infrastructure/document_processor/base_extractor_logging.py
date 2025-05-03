"""Logging functionality for base document extractor."""
from typing import Dict, Any
from app.core.logging import logger


class BaseExtractorLogging:
    """Logging utilities for document extractors."""
    
    def log_extraction_start(self, extractor_name: str, content: bytes, 
                           metadata: Dict[str, Any]) -> None:
        """Log extraction start with metadata.
        
        Args:
            extractor_name: Name of the extractor class
            content: Document content
            metadata: Extraction metadata
        """
        logger.info(
            f"Starting extraction with {extractor_name}, "
            f"size: {len(content)} bytes",
            extra={
                **metadata,
                "task": "document_extraction",
                "action": "start"
            }
        )
    
    def log_extraction_success(self, extractor_name: str, result: str, 
                             elapsed_ms: float, metadata: Dict[str, Any]) -> None:
        """Log extraction success with metadata.
        
        Args:
            extractor_name: Name of the extractor class
            result: Extracted text
            elapsed_ms: Elapsed time in milliseconds
            metadata: Extraction metadata
        """
        logger.info(
            f"Extraction successful with {extractor_name}, "
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
    
    def log_extraction_error(self, extractor_name: str, error: Exception, 
                           elapsed_ms: float, metadata: Dict[str, Any]) -> None:
        """Log extraction error with metadata.
        
        Args:
            extractor_name: Name of the extractor class
            error: Exception that occurred
            elapsed_ms: Elapsed time in milliseconds
            metadata: Extraction metadata
        """
        logger.error(
            f"Extraction failed with {extractor_name}: {str(error)}",
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
