"""
Text sanitization utilities for job descriptions.

This module provides functions to clean and prepare job description text
for API submission, preventing JSON parsing errors.
"""

import re
import unicodedata
import json
from typing import Dict, Any, List, Set, Optional
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Common patterns that cause issues in JSON
PROBLEMATIC_PATTERNS = [
    # Common control characters
    (r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ''),
    # Replace multiple newlines with a single one
    (r'\n{3,}', '\n\n'),
    # Replace multiple spaces with a single one
    (r' {2,}', ' '),
    # Replace tabs with spaces
    (r'\t', ' '),
    # Replace carriage returns
    (r'\r', '\n'),
    # Replace common bullet points with standard dash
    (r'[•·⁃‣⦿⁌⁍◦➤➢➣➔]', '-'),
    # Replace common quote characters with standard quotes
    (r'[""]', '"'),
    (r'['']', "'"),
    # Replace em dash and en dash with regular dash
    (r'[—–]', '-'),
]

# Characters that need special handling in JSON
JSON_ESCAPE_CHARS = {
    '\\': '\\\\',  # Backslash
    '"': '\\"',    # Double quote
    '/': '\\/',    # Forward slash
    '\b': '\\b',   # Backspace
    '\f': '\\f',   # Form feed
    '\n': '\\n',   # New line
    '\r': '\\r',   # Carriage return
    '\t': '\\t',   # Tab
}

def remove_non_printable_chars(text: str) -> str:
    """
    Remove non-printable and control characters from text.
    
    Args:
        text: The input text to process
        
    Returns:
        str: Text with non-printable characters removed
    """
    if not text:
        return ""
    
    # Replace control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize Unicode to remove unusual whitespace
    text = unicodedata.normalize('NFKD', text)
    
    # Strip null bytes and zero-width characters
    text = text.replace('\x00', '')
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    
    return text

def sanitize_text(text: str, preserve_newlines: bool = True) -> str:
    """
    Sanitize job description text to prevent JSON parsing errors.
    
    Args:
        text: The raw job description text
        preserve_newlines: Whether to preserve newline characters or replace them
        
    Returns:
        str: Sanitized text ready for API submission
    """
    if not text:
        return ""
    
    # Remove non-printable characters first
    text = remove_non_printable_chars(text)
    
    # Apply all problematic pattern replacements
    for pattern, replacement in PROBLEMATIC_PATTERNS:
        text = re.sub(pattern, replacement, text)
    
    # Normalize whitespace
    text = text.strip()
    
    # Replace newlines if not preserving them
    if not preserve_newlines:
        text = re.sub(r'\n', ' ', text)
    
    # Ensure the text doesn't have excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text

def escape_json_characters(text: str) -> str:
    """
    Escape special characters for JSON encoding.
    
    Args:
        text: Text to escape for JSON
        
    Returns:
        str: Text with JSON special characters escaped
    """
    if not text:
        return ""
    
    # First sanitize the text
    text = sanitize_text(text)
    
    # Manual escaping for better control
    for char, escaped in JSON_ESCAPE_CHARS.items():
        if char in text:
            text = text.replace(char, escaped)
    
    return text

def test_json_serialization(text: str) -> Dict[str, Any]:
    """
    Test if the text can be properly serialized in JSON.
    
    Args:
        text: Text to test for JSON serialization
        
    Returns:
        dict: Result with status and any error message
    """
    try:
        # Create a sample JSON object with the text
        test_obj = {"job_description": text}
        json_str = json.dumps(test_obj)
        
        # Try to parse it back to ensure it's valid
        json.loads(json_str)
        
        return {
            "is_valid": True,
            "error": None
        }
    except Exception as e:
        logger.warning(f"JSON serialization test failed: {str(e)}")
        return {
            "is_valid": False,
            "error": str(e)
        }

def clean_pasted_html(html_text: str) -> str:
    """
    Clean text that might have been pasted from HTML.
    
    Args:
        html_text: Potentially HTML-formatted text
        
    Returns:
        str: Cleaned plain text
    """
    if not html_text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_text)
    
    # Remove HTML entities
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    # Sanitize the resulting text
    return sanitize_text(text)
