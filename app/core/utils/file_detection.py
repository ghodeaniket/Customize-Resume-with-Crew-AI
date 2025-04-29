"""File type detection utilities."""
import os
import io
import mimetypes
from pathlib import Path
from typing import Dict, Optional, Any

# Initialize mimetypes if needed
mimetypes.init()

# Common MIME types
PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOC_MIME_TYPE = "application/msword"
TEXT_MIME_TYPE = "text/plain"
OCTET_STREAM = "application/octet-stream"

# Map of file extensions to MIME types for supported document formats
SUPPORTED_EXTENSIONS = {
    ".pdf": PDF_MIME_TYPE,
    ".docx": DOCX_MIME_TYPE,
    ".doc": DOC_MIME_TYPE,
    ".txt": TEXT_MIME_TYPE,
    ".rtf": "application/rtf",
}

# File signatures (magic bytes) for common formats
FILE_SIGNATURES = {
    # PDF: %PDF-
    b"%PDF-": PDF_MIME_TYPE,
    
    # DOCX: PK.. (ZIP format)
    b"PK\x03\x04": DOCX_MIME_TYPE,
    
    # DOC: D0 CF 11 E0 (Microsoft Compound File Binary)
    b"\xD0\xCF\x11\xE0": DOC_MIME_TYPE,
}


def is_supported_file_type(filename: str) -> bool:
    """Check if a file type is supported based on extension.
    
    Args:
        filename: Filename to check
        
    Returns:
        bool: True if the file type is supported, False otherwise
    """
    if not filename:
        return False
        
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def detect_mime_type_from_filename(filename: str) -> str:
    """Detect MIME type from filename.
    
    Args:
        filename: Filename to detect MIME type from
        
    Returns:
        str: Detected MIME type or application/octet-stream
    """
    if not filename:
        return OCTET_STREAM
        
    ext = Path(filename).suffix.lower()
    
    # Use our mapping for supported extensions
    if ext in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[ext]
    
    # Fall back to mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or OCTET_STREAM


def detect_mime_type_from_content(content: bytes, max_scan: int = 4096) -> Optional[str]:
    """Detect MIME type from file content using magic bytes.
    
    Args:
        content: File content bytes
        max_scan: Maximum number of bytes to scan
        
    Returns:
        Optional[str]: Detected MIME type or None if unknown
    """
    if not content:
        return None
        
    # Limit scan to beginning of file
    sample = content[:max_scan]
    
    # Check for file signatures
    for signature, mime_type in FILE_SIGNATURES.items():
        sig_len = len(signature)
        if len(sample) >= sig_len and sample[:sig_len] == signature:
            return mime_type
    
    # Check if it might be text
    try:
        # Try to decode as UTF-8 to see if it's text
        sample.decode('utf-8')
        return TEXT_MIME_TYPE
    except UnicodeDecodeError:
        pass
    
    return None


def detect_file_type(content: bytes, filename: Optional[str] = None) -> str:
    """Detect file type using both filename and content.
    
    Args:
        content: File content bytes
        filename: Original filename (optional)
        
    Returns:
        str: Detected MIME type or application/octet-stream
    """
    # First try content-based detection
    mime_type = detect_mime_type_from_content(content)
    if mime_type:
        return mime_type
    
    # Fall back to filename-based detection
    if filename:
        return detect_mime_type_from_filename(filename)
    
    # Default to octet-stream
    return OCTET_STREAM


def get_detailed_file_info(
    content: bytes, filename: Optional[str] = None
) -> Dict[str, Any]:
    """Get detailed file information for debugging.
    
    Args:
        content: File content bytes
        filename: Original filename (optional)
        
    Returns:
        Dict[str, Any]: Dictionary with detailed file information
    """
    result = {
        "size": len(content),
        "filename": filename,
        "extension": Path(filename).suffix.lower() if filename else None,
        "detected_type": detect_file_type(content, filename),
    }
    
    # Add hex dump of first 32 bytes for debugging
    if content:
        hex_header = " ".join([f"{b:02x}" for b in content[:32]])
        result["hex_header"] = hex_header
    
    return result
