"""Document processing infrastructure for Resume Customizer."""
import io
import re
import time
import hashlib
import functools
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

import docx
from PyPDF2 import PdfReader

# Lazy loading for PyMuPDF - don't import at module level
PYMUPDF_AVAILABLE = None
fitz = None  # Will be imported on-demand

from app.core.exceptions import DocumentProcessingError
from app.core.logging import logger
from app.core.utils.file_detection import (
    detect_file_type, get_detailed_file_info, PDF_MIME_TYPE, 
    DOCX_MIME_TYPE, TEXT_MIME_TYPE, OCTET_STREAM
)


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


# Cache for document extraction results
_EXTRACTION_CACHE = {}
_CACHE_MAX_SIZE = 16
_CACHE_MAX_AGE_SECONDS = 3600  # 1 hour

def document_extraction_cache(extraction_func: Callable) -> Callable:
    """Decorator to cache document extraction results.
    
    Args:
        extraction_func: The extraction function to wrap with caching
        
    Returns:
        Callable: Wrapped function with caching
    """
    @functools.wraps(extraction_func)
    def wrapper(self, content: bytes, *args, **kwargs) -> str:
        # Skip caching if disabled
        if not getattr(self, 'cache_enabled', True):
            return extraction_func(self, content, *args, **kwargs)
            
        # Create a hash of the content to use as cache key
        content_hash = hashlib.md5(content).hexdigest()
        
        # Get function name for the cache key
        func_name = extraction_func.__name__
        
        # Create cache key
        cache_key = f"{content_hash}_{func_name}"
        
        # Check if result is in cache
        current_time = time.time()
        if cache_key in _EXTRACTION_CACHE:
            cached_time, cached_result = _EXTRACTION_CACHE[cache_key]
            
            # Check if the cached result is still valid (not expired)
            if current_time - cached_time < _CACHE_MAX_AGE_SECONDS:
                logger.info(f"Using cached extraction result for {func_name}")
                return cached_result
        
        # Not in cache or expired, execute the function
        result = extraction_func(self, content, *args, **kwargs)
        
        # Cache the result with timestamp
        _EXTRACTION_CACHE[cache_key] = (current_time, result)
        
        # Prune cache if it grows too large
        if len(_EXTRACTION_CACHE) > _CACHE_MAX_SIZE:
            # Remove the oldest entries
            sorted_keys = sorted(_EXTRACTION_CACHE.keys(), 
                               key=lambda k: _EXTRACTION_CACHE[k][0])
            for old_key in sorted_keys[:len(_EXTRACTION_CACHE) - _CACHE_MAX_SIZE]:
                del _EXTRACTION_CACHE[old_key]
        
        return result
    
    return wrapper


class DocumentProcessor:
    """Processor for different document formats."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize document processor.
        
        Args:
            cache_enabled: Whether to cache extraction results
        """
        self.cache_enabled = cache_enabled
    
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
        actual_file_type = file_info["detected_type"]
        
        logger.info(f"Detected file type: {actual_file_type}, size: {file_size} bytes", extra={
            "file_type": actual_file_type,
            "file_size": file_size,
            "task": "document_extraction"
        })
        
        try:
            # Content hash for caching
            content_hash = None
            if self.cache_enabled:
                content_hash = hashlib.md5(file_content).hexdigest()
                logger.debug(f"Content hash: {content_hash}")
            
            # Process based on detected file type
            result = None
            
            if actual_file_type == PDF_MIME_TYPE:
                result = await self._extract_from_pdf_with_fallback(file_content)
            
            elif actual_file_type == DOCX_MIME_TYPE:
                # Run in executor to avoid blocking the event loop
                result = await asyncio.to_thread(self._extract_from_docx, file_content)
            
            elif actual_file_type == TEXT_MIME_TYPE:
                # Run in executor to avoid blocking the event loop
                result = await asyncio.to_thread(self._extract_from_text, file_content)
            
            else:
                # Try as text for unknown types
                try:
                    result = await asyncio.to_thread(self._extract_from_text, file_content)
                except UnicodeDecodeError:
                    logger.error(f"Unsupported file type: {actual_file_type}", extra={
                        "file_type": actual_file_type,
                        "error": "unsupported_file_type",
                        "task": "document_extraction"
                    })
                    raise DocumentProcessingError(
                        detail=f"Unsupported file type: {actual_file_type}"
                    )
            
            # Log extraction success
            if result:
                result_length = len(result)
                logger.info(f"Extraction successful, extracted {result_length} characters", extra={
                    "extracted_chars": result_length,
                    "file_type": actual_file_type,
                    "status": "success",
                    "task": "document_extraction"
                })
            
            return result
                
        except Exception as e:
            logger.error(
                f"Error extracting text from document: {str(e)}", 
                exc_info=True,
                extra={
                    "error": str(e),
                    "file_type": actual_file_type,
                    "status": "failed",
                    "task": "document_extraction"
                }
            )
            raise DocumentProcessingError(
                detail=f"Error extracting text from document: {str(e)}"
            )
        finally:
            total_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"Total extraction time: {total_time_ms:.2f}ms", extra={
                "processing_time_ms": total_time_ms,
                "task": "document_extraction"
            })
    
    async def _extract_from_pdf_with_fallback(self, content: bytes) -> str:
        """Extract text from PDF content with fallback mechanism.
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If all extraction methods fail
        """
        errors = []
        
        # Try PyMuPDF first if available (more robust)
        if lazy_import_pymupdf():
            try:
                logger.info("Attempting PDF extraction with PyMuPDF")
                return await asyncio.to_thread(self._extract_from_pdf_pymupdf, content)
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed, falling back to PyPDF2: {str(e)}")
                errors.append(f"PyMuPDF error: {str(e)}")
                # Fall through to PyPDF2
        
        # Use PyPDF2 as fallback or primary method if PyMuPDF is not available
        try:
            logger.info("Attempting PDF extraction with PyPDF2")
            return await asyncio.to_thread(self._extract_from_pdf, content)
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            errors.append(f"PyPDF2 error: {str(e)}")
            
            # All extraction methods failed
            error_msg = "All PDF extraction methods failed"
            logger.error(error_msg)
            raise DocumentProcessingError(
                detail=error_msg
            )
    
    @document_extraction_cache
    def _extract_from_text(self, content: bytes) -> str:
        """Extract text from text file content.
        
        Args:
            content: Text file content
            
        Returns:
            str: Decoded text
            
        Raises:
            UnicodeDecodeError: If content cannot be decoded as text
        """
        try:
            text = content.decode('utf-8')
            logger.debug(f"Extracted text (first 100 chars): {text[:100]}")
            return text
        except UnicodeDecodeError:
            logger.warning("Failed to decode as UTF-8, trying with errors='replace'")
            text = content.decode('utf-8', errors='replace')
            logger.debug(f"Extracted text with replacement (first 100 chars): {text[:100]}")
            return text
    
    @document_extraction_cache
    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content using PyPDF2.
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails completely
        """
        start_time = time.time()
        file_size = len(content)
        
        logger.info(f"Starting PDF extraction, size: {file_size} bytes")
        
        # Log detailed content information for debugging
        if content[:4] != b'%PDF':
            hex_header = " ".join([f"{b:02x}" for b in content[:20]])
            logger.warning(f"Content does not start with PDF signature. Header: {hex_header}")
        
        pdf_file = io.BytesIO(content)
        try:
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
                total_time_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"PDF extraction complete: {successful_pages}/{num_pages} pages, "
                    f"{len(cleaned_text)} chars, {total_time_ms:.2f}ms"
                )
                
                # Log sample of extracted text for verification
                sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                logger.debug(f"Extracted text sample: {sample}")
                
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
            
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
            
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
            else:
                raise DocumentProcessingError(
                    detail=f"Error processing PDF: {str(e)}"
                )
    
    @document_extraction_cache
    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX content.
        
        Args:
            content: DOCX file content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        start_time = time.time()
        file_size = len(content)
        
        logger.info(f"Starting DOCX extraction, size: {file_size} bytes")
        
        docx_file = io.BytesIO(content)
        try:
            doc = docx.Document(docx_file)
            
            # Extract text from paragraphs with error recovery
            paragraphs = []
            paragraph_errors = 0
            
            for i, para in enumerate(doc.paragraphs):
                try:
                    paragraphs.append(para.text)
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
                            row_text = [cell.text for cell in row.cells]
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
                
            text = "\n".join(all_text)
            
            # Clean and return text
            cleaned_text = self._clean_text(text)
            
            # Log performance and results
            total_time_ms = (time.time() - start_time) * 1000
            logger.info(
                f"DOCX extraction complete: {len(paragraphs)} paragraphs, "
                f"{len(doc.tables)} tables, {len(cleaned_text)} chars, {total_time_ms:.2f}ms"
            )
            
            # Log sample for verification
            sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
            logger.debug(f"Extracted text sample: {sample}")
            
            return cleaned_text
            
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Error processing DOCX: {str(e)}", exc_info=True)
            raise DocumentProcessingError(
                detail=f"Error processing DOCX: {str(e)}"
            )
    
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
    
    @document_extraction_cache
    def _extract_from_pdf_pymupdf(self, content: bytes) -> str:
        """Extract text from PDF content using PyMuPDF (more robust than PyPDF2).
        
        Args:
            content: PDF file content
            
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
            
        start_time = time.time()
        file_size = len(content)
        logger.info(f"Starting PyMuPDF PDF extraction, size: {file_size} bytes")
        
        try:
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
                
                total_time_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"PyMuPDF extraction complete: {successful_pages}/{num_pages} pages, "
                    f"{len(cleaned_text)} chars, {total_time_ms:.2f}ms"
                )
                
                # Log sample
                sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                logger.debug(f"PyMuPDF extracted text sample: {sample}")
                
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
                
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            logger.error(f"PyMuPDF extraction error: {str(e)}", exc_info=True)
            
            raise DocumentProcessingError(
                detail=f"PyMuPDF PDF extraction error: {str(e)}"
            )


class DocumentBuilder:
    """Builder for creating documents in various formats."""
    
    def __init__(self):
        """Initialize document builder."""
        pass
    
    def create_markdown(self, sections: List[Tuple[str, str]]) -> str:
        """Create a markdown document from sections.
        
        Args:
            sections: List of (section_title, section_content) tuples
            
        Returns:
            str: Markdown document
        """
        logger.debug(f"Creating markdown document with {len(sections)} sections")
        
        markdown = ""
        for title, content in sections:
            markdown += f"## {title}\n\n{content}\n\n"
        
        return markdown.strip()
