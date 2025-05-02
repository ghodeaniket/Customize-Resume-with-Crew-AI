"""DOCX document extraction implementation."""
import io
import time
import asyncio
from typing import Optional, List, Dict, Any

import docx

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.core.utils.file_detection import DOCX_MIME_TYPE, DOC_MIME_TYPE
from app.infrastructure.document_processor.base import BaseDocumentExtractor


class DOCXExtractor(BaseDocumentExtractor):
    """DOCX document extractor implementation."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize DOCX extractor.
        
        Args:
            cache_enabled: Whether to enable caching
        """
        super().__init__(cache_enabled=cache_enabled)
    
    @property
    def mime_types(self) -> list[str]:
        """Get list of MIME types supported by this extractor.
        
        Returns:
            list[str]: List of supported MIME types
        """
        return [DOCX_MIME_TYPE, DOC_MIME_TYPE]
    
    @property
    def supported_extensions(self) -> list[str]:
        """Get list of file extensions supported by this extractor.
        
        Returns:
            list[str]: List of supported file extensions
        """
        return [".docx", ".doc"]
    
    async def extract_text(self, content: bytes, filename: Optional[str] = None) -> str:
        """Extract text from DOCX content.
        
        Args:
            content: DOCX content as bytes
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
            result = await asyncio.to_thread(self._extract_docx_sync, content)
            
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
                raise DocumentProcessingError(detail=f"DOCX extraction failed: {str(e)}")
    
    def _extract_docx_sync(self, content: bytes) -> str:
        """Synchronous implementation of DOCX extraction.
        
        Args:
            content: DOCX content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        docx_file = io.BytesIO(content)
        try:
            doc = docx.Document(docx_file)
            
            # Extract text from paragraphs with error recovery
            paragraphs = []
            paragraph_errors = 0
            
            for i, para in enumerate(doc.paragraphs):
                try:
                    text = para.text.strip()
                    if text:  # Only add non-empty paragraphs
                        paragraphs.append(text)
                except Exception as para_error:
                    logger.warning(f"Error extracting paragraph {i}: {str(para_error)}")
                    paragraph_errors += 1
                    # Continue with other paragraphs
            
            logger.debug(f"Extracted {len(paragraphs)} paragraphs from DOCX (errors: {paragraph_errors})")
            
            # Extract text from tables if any
            table_text = []
            table_errors = 0
            
            for i, table in enumerate(doc.tables):
                try:
                    for row in table.rows:
                        try:
                            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                            if row_text:  # Only add non-empty rows
                                table_text.append(" | ".join(row_text))
                        except Exception as row_error:
                            logger.warning(f"Error extracting row in table {i}: {str(row_error)}")
                            # Continue with other rows
                except Exception as table_error:
                    logger.warning(f"Error extracting table {i}: {str(table_error)}")
                    table_errors += 1
                    # Continue with other tables
            
            if table_text:
                logger.debug(
                    f"Extracted text from {len(doc.tables)} tables "
                    f"(errors: {table_errors})"
                )
                
            # Combine all text
            all_text = paragraphs + table_text
            
            # Check if we have any content
            if not all_text:
                logger.warning("No text extracted from DOCX")
                return "[Document contains no extractable text]"
                
            # Join with appropriate separators
            # Double newline between paragraphs, single newline between table rows
            text = "\n\n".join(paragraphs)
            if paragraphs and table_text:
                text += "\n\n"
            if table_text:
                text += "\n".join(table_text)
            
            # Clean and return text
            return self._clean_text(text)
            
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}", exc_info=True)
            
            # Provide more specific error messages based on common failures
            error_message = str(e).lower()
            if "file is not a zip file" in error_message:
                raise DocumentProcessingError(
                    detail="The file appears to be corrupted or not a valid DOCX document."
                )
            elif "requiring repair" in error_message:
                raise DocumentProcessingError(
                    detail="The DOCX file is damaged and requires repair. Please try repairing the document."
                )
            
            # Re-raise with generic message
            raise DocumentProcessingError(detail=f"Error processing DOCX: {str(e)}")
