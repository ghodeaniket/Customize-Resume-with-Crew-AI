"""
Emergency text sanitization for problematic job descriptions.

This module provides extra-robust sanitization functions for job descriptions
that cause errors in the standard sanitization process.
"""

import re
import unicodedata
import string

def deep_clean_text(text: str) -> str:
    """
    Apply aggressive cleaning to job description text that causes regex errors.
    
    Args:
        text: The problematic job description text
        
    Returns:
        str: The deeply sanitized text
    """
    if not text:
        return ""
    
    # First, apply Unicode normalization
    try:
        text = unicodedata.normalize('NFKD', text)
    except:
        # If normalization fails, try to decode with errors='ignore'
        text = str(text.encode('ascii', 'ignore').decode('ascii'))
    
    # Remove all control characters
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')
    
    # Keep only printable ASCII characters and basic punctuation
    allowed_chars = set(string.printable)
    text = ''.join(ch if ch in allowed_chars else ' ' for ch in text)
    
    # Fix common issues that break regex
    # Replace multiple spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    # Replace multiple newlines with a maximum of two
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Handle potentially problematic characters for regex
    for char in '[]()*+?{}.\\|^$':
        text = text.replace(char, f' {char} ')
    
    # Clean up again after replacements
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def character_by_character_clean(text: str) -> str:
    """
    Process text character by character to avoid regex errors.
    
    Args:
        text: The problematic job description text
        
    Returns:
        str: Sanitized text processed character by character
    """
    if not text:
        return ""
    
    # Convert to simple ASCII, ignoring problematic characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    result = []
    for char in text:
        # Keep only printable characters
        if char in string.printable:
            # Special handling for quotes
            if char == '"':
                result.append('"')
            elif char == "'":
                result.append("'")
            else:
                result.append(char)
    
    processed = ''.join(result)
    
    # Manual cleanups without regex
    # Handle multiple spaces
    while '  ' in processed:
        processed = processed.replace('  ', ' ')
    
    # Handle multiple newlines
    while '\n\n\n' in processed:
        processed = processed.replace('\n\n\n', '\n\n')
    
    return processed.strip()
