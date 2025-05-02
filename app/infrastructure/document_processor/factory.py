"""Factory for creating document extractors."""
from typing import Dict, Type, Optional, List

from app.core.logging import logger
from app.core.utils.file_detection import (
    detect_file_type, get_detailed_file_info,
    PDF_MIME_TYPE, DOCX_MIME_TYPE, TEXT_MIME_TYPE, OCTET_STREAM
)
from app.core.exceptions import UnsupportedFileTypeError
from app.infrastructure.document_processor.base import BaseDocumentExtractor
from app.infrastructure.document_processor.pdf_extractor import PDFExtractor
from app.infrastructure.document_processor.docx_extractor import DOCXExtractor
from app.infrastructure.document_processor.txt_extractor import TXTExtractor


class DocumentExtractorFactory:
    """Factory for creating appropriate document extractors."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize document extractor factory.
        
        Args:
            cache_enabled: Whether to enable caching for extractors
        """
        self.cache_enabled = cache_enabled
        self._extractors: Dict[Type[BaseDocumentExtractor], BaseDocumentExtractor] = {}
        self._register_extractors()
    
    def _register_extractors(self) -> None:
        """Register default extractors."""
        # Instantiate extractors only once for reuse
        self._extractors[PDFExtractor] = PDFExtractor(cache_enabled=self.cache_enabled)
        self._extractors[DOCXExtractor] = DOCXExtractor(cache_enabled=self.cache_enabled)
        self._extractors[TXTExtractor] = TXTExtractor(cache_enabled=self.cache_enabled)
    
    def create_extractor(self, 
                        mime_type: str, 
                        filename: Optional[str] = None) -> BaseDocumentExtractor:
        """Create appropriate document extractor for the file type.
        
        Args:
            mime_type: MIME type of the document
            filename: Optional original filename
            
        Returns:
            BaseDocumentExtractor: Appropriate document extractor
            
        Raises:
            UnsupportedFileTypeError: If no suitable extractor is found
        """
        logger.info(f"Creating extractor for MIME type: {mime_type}, filename: {filename}")
        
        # Try PDF extractor
        if self._extractors[PDFExtractor].can_handle(mime_type, filename):
            logger.debug("Using PDF extractor")
            return self._extractors[PDFExtractor]
        
        # Try DOCX extractor
        if self._extractors[DOCXExtractor].can_handle(mime_type, filename):
            logger.debug("Using DOCX extractor")
            return self._extractors[DOCXExtractor]
        
        # Try TXT extractor
        if self._extractors[TXTExtractor].can_handle(mime_type, filename):
            logger.debug("Using TXT extractor")
            return self._extractors[TXTExtractor]
        
        # For application/octet-stream, try to determine from filename if available
        if mime_type == OCTET_STREAM and filename:
            for extractor_type in [PDFExtractor, DOCXExtractor, TXTExtractor]:
                extractor = self._extractors[extractor_type]
                if any(filename.lower().endswith(ext) for ext in extractor.supported_extensions):
                    logger.debug(f"Using {extractor_type.__name__} based on filename extension")
                    return extractor
        
        # No suitable extractor found
        logger.error(f"Unsupported file type: {mime_type}")
        raise UnsupportedFileTypeError(
            detail=f"Unsupported file type: {mime_type}"
        )
    
    def get_supported_mime_types(self) -> List[str]:
        """Get list of all supported MIME types.
        
        Returns:
            List[str]: List of supported MIME types
        """
        mime_types = []
        for extractor in self._extractors.values():
            mime_types.extend(extractor.mime_types)
        return list(set(mime_types))  # Remove duplicates
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions.
        
        Returns:
            List[str]: List of supported file extensions
        """
        extensions = []
        for extractor in self._extractors.values():
            extensions.extend(extractor.supported_extensions)
        return list(set(extensions))  # Remove duplicates
    
    def is_supported_file_type(self, filename: str) -> bool:
        """Check if a file type is supported based on extension.
        
        Args:
            filename: Filename to check
            
        Returns:
            bool: True if the file type is supported, False otherwise
        """
        if not filename:
            return False
            
        supported_extensions = self.get_supported_extensions()
        for ext in supported_extensions:
            if filename.lower().endswith(ext):
                return True
        
        return False
