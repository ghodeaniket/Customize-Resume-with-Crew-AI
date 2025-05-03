"""PyMuPDF extraction implementation."""
import io
import time
import asyncio
from typing import Optional, List

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingError
from app.infrastructure.document_processor.pdf.base_pdf_extractor import BasePDFExtractor


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
            logger.warning("PyMuPDF (fitz) is not available")
    
    return PYMUPDF_AVAILABLE


class PyMuPDFExtractor(BasePDFExtractor):
    """PDF extractor using PyMuPDF (fitz) library."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize PyMuPDF extractor.
        
        Args:
            cache_enabled: Whether to enable caching
        """
        super().__init__(cache_enabled=cache_enabled)
        # Check availability on initialization
        if not lazy_import_pymupdf():
            logger.warning("PyMuPDF extractor initialized but PyMuPDF is not available")
    
    async def extract_text(self, content: bytes, filename: Optional[str] = None) -> str:
        """Extract text from PDF content using PyMuPDF.
        
        Args:
            content: PDF content as bytes
            filename: Optional original filename
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        # Ensure PyMuPDF is available
        if not lazy_import_pymupdf():
            raise DocumentProcessingError(
                detail="PyMuPDF not available for PDF extraction"
            )
        
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
                raise self._create_extraction_error("PyMuPDF", e)
    
    def _extract_sync(self, content: bytes) -> str:
        """Synchronous extraction using PyMuPDF.
        
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
        failed_pages: List[int] = []
        
        logger.info(f"PyMuPDF processing PDF with {num_pages} pages")
        
        # Process each page with error recovery
        for i in range(num_pages):
            page_start_time = time.time()
            page_extracted = False
            
            # Try multiple extraction methods for each page
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
            
            # Try each extraction method until one succeeds
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
                    
                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                        successful_pages += 1
                        page_extracted = True
                        logger.debug(f"Page {i+1} extracted successfully using {method_name} method")
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
        
        # Log extraction metrics
        self._log_extraction_metrics(
            content_length=len(content),
            total_pages=num_pages,
            successful_pages=successful_pages,
            failed_pages=failed_pages,
            elapsed_ms=(time.time() - page_start_time) * 1000
        )
        
        # Combine all text
        if text_parts:
            combined_text = "\n\n".join(text_parts)
            return self._clean_text_result(combined_text)
        else:
            logger.warning("No text extracted from PDF with PyMuPDF")
            return "[Document contains no extractable text]"
