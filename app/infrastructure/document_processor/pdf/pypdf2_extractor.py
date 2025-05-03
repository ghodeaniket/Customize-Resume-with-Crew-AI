"""PyPDF2 extraction implementation."""
import io
import time
import asyncio
from typing import Optional, List

from PyPDF2 import PdfReader

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.infrastructure.document_processor.pdf.base_pdf_extractor import BasePDFExtractor


class PyPDF2Extractor(BasePDFExtractor):
    """PDF extractor using PyPDF2 library."""
    
    async def extract_text(self, content: bytes, filename: Optional[str] = None) -> str:
        """Extract text from PDF content using PyPDF2.
        
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
            # Run CPU-bound operation in thread pool
            result = await asyncio.to_thread(self._extract_sync, content)
            
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
                raise self._create_extraction_error("PyPDF2", e)
    
    def _extract_sync(self, content: bytes) -> str:
        """Synchronous extraction using PyPDF2.
        
        Args:
            content: PDF content
            
        Returns:
            str: Extracted text
        """
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        
        # Get PDF metadata if available
        info = reader.metadata
        if info:
            logger.debug(f"PDF metadata: {info}")
        
        text_parts = []
        num_pages = len(reader.pages)
        successful_pages = 0
        failed_pages: List[int] = []
        
        logger.info(f"PDF structure: {num_pages} pages")
        
        # Process each page with detailed logging and recovery
        for i, page in enumerate(reader.pages):
            page_start_time = time.time()
            try:
                page_text = page.extract_text()
                page_time_ms = (time.time() - page_start_time) * 1000
                
                logger.debug(f"Page {i+1} extraction: {len(page_text)} chars, {page_time_ms:.2f}ms")
                
                if page_text and page_text.strip():  # Only add non-empty pages
                    text_parts.append(page_text)
                    successful_pages += 1
                else:
                    logger.warning(f"Page {i+1} extracted successfully but contains no text")
                    failed_pages.append(i+1)
            except Exception as page_error:
                logger.error(f"Error extracting text from page {i+1}: {str(page_error)}")
                failed_pages.append(i+1)
                # Continue with other pages
        
        # Log extraction metrics
        self._log_extraction_metrics(
            content_length=len(content),
            total_pages=num_pages,
            successful_pages=successful_pages,
            failed_pages=failed_pages,
            elapsed_ms=(time.time() - page_start_time) * 1000
        )
        
        # Combine and clean the extracted text
        if text_parts:
            text = "\n\n".join(text_parts)
            return self._clean_text_result(text)
        else:
            logger.warning("No text extracted from PDF with PyPDF2")
            return "[Document contains no extractable text]"
