"""PDF document extraction implementation."""
import io
import time
import asyncio
from typing import Optional, List, Dict, Any

from PyPDF2 import PdfReader

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.core.utils.file_detection import PDF_MIME_TYPE
from app.infrastructure.document_processor.base import BaseDocumentExtractor


# Lazy loading for PyMuPDF - don't import at module level
PYMUPDF_AVAILABLE = None
fitz = None  # Will be imported on-demand


def lazy_import_pymupdf():
    """Lazily import PyMuPDF only when needed to improve startup time."""
    global PYMUPDF_AVAILABLE, fitz
    
    if PYMUPDF_AVAILABLE is None:
        try:
            import fitz as pymupdf
            fitz = pymupdf
            PYMUPDF_AVAILABLE = True
            logger.debug("PyMuPDF successfully imported")
        except ImportError:
            PYMUPDF_AVAILABLE = False
            logger.warning("PyMuPDF (fitz) is not available; using PyPDF2 only for PDF processing")
    
    return PYMUPDF_AVAILABLE


class PDFExtractor(BaseDocumentExtractor):
    """PDF document extractor implementation."""
    
    def __init__(self, cache_enabled: bool = True, use_pymupdf_first: bool = True):
        """Initialize PDF extractor.
        
        Args:
            cache_enabled: Whether to enable caching
            use_pymupdf_first: Whether to try PyMuPDF before PyPDF2
        """
        super().__init__(cache_enabled=cache_enabled)
        self.use_pymupdf_first = use_pymupdf_first
    
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
                ("PyMuPDF", self._extract_with_pymupdf),
                ("PyPDF2", self._extract_with_pypdf2)
            ]
        else:
            extractors = [
                ("PyPDF2", self._extract_with_pypdf2)
            ]
            # Only add PyMuPDF if available
            if lazy_import_pymupdf():
                extractors.append(("PyMuPDF", self._extract_with_pymupdf))
        
        # Try each extractor in order
        for name, extractor in extractors:
            try:
                logger.info(f"Attempting PDF extraction with {name}")
                result = await extractor(content)
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
    
    async def _extract_with_pypdf2(self, content: bytes) -> str:
        """Extract text from PDF using PyPDF2.
        
        Args:
            content: PDF content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        try:
            # Run CPU-bound operation in thread pool
            return await asyncio.to_thread(self._extract_with_pypdf2_sync, content)
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            
            # Provide more specific error messages based on the exception
            error_message = str(e).lower()
            if "file has not been decrypted" in error_message or "password" in error_message:
                raise DocumentProcessingError(
                    detail="PDF is encrypted and cannot be processed. Please remove the password and try again."
                )
            elif "eof marker not found" in error_message:
                raise DocumentProcessingError(
                    detail="PDF file is incomplete or corrupted. Please verify the file and try again."
                )
            
            # Re-raise the original exception
            raise
    
    def _extract_with_pypdf2_sync(self, content: bytes) -> str:
        """Synchronous implementation of PyPDF2 extraction.
        
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
        failed_pages = []
        
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
        
        # Calculate success rate for extraction
        success_rate = successful_pages / num_pages if num_pages > 0 else 0
        
        # Clean the extracted text
        if text_parts:
            text = "\n\n".join(text_parts)
            cleaned_text = self._clean_text(text)
            
            # Warn if partial extraction
            if success_rate < 1.0:
                failed_pages_str = ", ".join(map(str, failed_pages))
                logger.warning(
                    f"Partial PDF extraction: {successful_pages}/{num_pages} pages extracted. "
                    f"Failed pages: {failed_pages_str}"
                )
            
            return cleaned_text
        else:
            # No text extracted, but don't fail completely
            logger.warning("No text extracted from PDF with PyPDF2")
            return "[Document contains no extractable text]"
    
    async def _extract_with_pymupdf(self, content: bytes) -> str:
        """Extract text from PDF using PyMuPDF.
        
        Args:
            content: PDF content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If PyMuPDF extraction fails completely
        """
        # Ensure PyMuPDF is available
        if not lazy_import_pymupdf():
            raise DocumentProcessingError(
                detail="PyMuPDF not available for PDF extraction"
            )
        
        try:
            # Run CPU-bound operation in thread pool
            return await asyncio.to_thread(self._extract_with_pymupdf_sync, content)
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {str(e)}")
            raise
    
    def _extract_with_pymupdf_sync(self, content: bytes) -> str:
        """Synchronous implementation of PyMuPDF extraction.
        
        Args:
            content: PDF content
            
        Returns:
            str: Extracted text
        """
        # Open PDF from memory buffer
        pdf_file = io.BytesIO(content)
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        
        text_parts = []
        num_pages = len(doc)
        successful_pages = 0
        failed_pages = []
        
        # Process each page with error recovery
        for i in range(num_pages):
            page_start_time = time.time()
            page_extracted = False
            
            # Try multiple extraction methods for each page with recovery
            extraction_methods = [
                {"name": "text", "get_text_param": "text"},
                {"name": "blocks", "get_text_param": "blocks"},
                {"name": "html", "get_text_param": "html"},
                {"name": "dict", "get_text_param": "dict"}
            ]
            
            page = None
            try:
                page = doc[i]
            except Exception as page_access_error:
                logger.error(f"PyMuPDF: Error accessing page {i+1}: {str(page_access_error)}")
                failed_pages.append(i+1)
                continue
            
            # Try each extraction method in order until one succeeds
            for method in extraction_methods:
                if page_extracted:
                    break
                    
                method_name = method["name"]
                get_text_param = method["get_text_param"]
                
                try:
                    if method_name == "blocks":
                        # Special handling for blocks method
                        blocks = page.get_text("blocks")
                        page_text = "\n".join([b[4] for b in blocks if isinstance(b[4], str)])
                    elif method_name == "dict":
                        # Special handling for dict method
                        text_dict = page.get_text("dict")
                        blocks = text_dict.get("blocks", [])
                        text_blocks = []
                        for block in blocks:
                            if "lines" in block:
                                for line in block["lines"]:
                                    if "spans" in line:
                                        for span in line["spans"]:
                                            if "text" in span:
                                                text_blocks.append(span["text"])
                        page_text = "\n".join(text_blocks)
                    else:
                        # Standard text extraction
                        page_text = page.get_text(get_text_param)
                        
                    page_time_ms = (time.time() - page_start_time) * 1000
                    
                    logger.debug(
                        f"PyMuPDF page {i+1} extraction using {method_name}: "
                        f"{len(page_text)} chars, {page_time_ms:.2f}ms"
                    )
                    
                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                        successful_pages += 1
                        page_extracted = True
                        logger.debug(f"Successfully extracted page {i+1} using {method_name} method")
                        break
                        
                except Exception as method_error:
                    logger.warning(
                        f"PyMuPDF: {method_name} extraction failed for page {i+1}: {str(method_error)}"
                    )
                    # Continue to next method
            
            # If all extraction methods failed for this page
            if not page_extracted:
                logger.warning(f"PyMuPDF: All extraction methods failed for page {i+1}")
                failed_pages.append(i+1)
        
        # Close the document
        doc.close()
        
        # Calculate success rate
        success_rate = successful_pages / num_pages if num_pages > 0 else 0
        
        # Combine all text
        if text_parts:
            combined_text = "\n\n".join(text_parts)
            cleaned_text = self._clean_text(combined_text)
            
            # Warn if partial extraction
            if success_rate < 1.0:
                failed_pages_str = ", ".join(map(str, failed_pages))
                logger.warning(
                    f"Partial PDF extraction with PyMuPDF: {successful_pages}/{num_pages} pages extracted. "
                    f"Failed pages: {failed_pages_str}"
                )
            
            return cleaned_text
        else:
            # No text extracted, but don't fail completely
            logger.warning("No text extracted from PDF with PyMuPDF")
            return "[Document contains no extractable text]"
