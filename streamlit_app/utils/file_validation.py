"""File validation utilities for resume uploads."""
import os
from pathlib import Path

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"]

def validate_file_type(filename):
    """Validate the file type based on extension.
    
    Args:
        filename (str): The name of the uploaded file
        
    Returns:
        tuple: (is_valid, message)
    """
    if not filename:
        return False, "No file selected"
    
    # Get the file extension
    file_ext = Path(filename).suffix.lower()
    
    # Check if the extension is in the allowed list
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Only PDF, DOCX, and TXT files are allowed, got {file_ext}"
    
    return True, "Valid file type"


def validate_file_size(size):
    """Validate the file size.
    
    Args:
        size (int): The size of the file in bytes
        
    Returns:
        tuple: (is_valid, message)
    """
    if size > MAX_FILE_SIZE:
        return False, f"File size exceeds the maximum limit of 10 MB"
    
    if size == 0:
        return False, "File is empty"
    
    return True, "Valid file size"


def format_size(size_bytes):
    """Format file size in bytes to a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
